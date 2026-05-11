import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


DEFAULT_VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi", ".m4v")
MERGED_PREFIX = "merged-"
STREAM_BASE_FIELDS = ("codec_type", "codec_name", "codec_tag_string", "time_base")
VIDEO_FIELDS = ("width", "height", "pix_fmt", "sample_aspect_ratio")
AUDIO_FIELDS = ("sample_rate", "channels", "channel_layout", "sample_fmt")


class MergeVideosError(Exception):
    """Expected user-facing failure."""


def natural_sort_key(path):
    """Sort filenames with embedded numbers in numeric order."""
    parts = re.split(r"(\d+)", path.name.lower())
    return tuple((1, int(part)) if part.isdigit() else (0, part) for part in parts)


def normalize_extensions(values):
    """Normalize extension filters to lowercase dotted suffixes."""
    if not values:
        return DEFAULT_VIDEO_EXTENSIONS

    extensions = []
    for value in values:
        extension = value.lower()
        if not extension.startswith("."):
            extension = f".{extension}"
        extensions.append(extension)
    return tuple(dict.fromkeys(extensions))


def collect_videos(directory, extensions):
    """Collect videos in the current directory, excluding previous outputs."""
    files = []
    for path in directory.iterdir():
        if not path.is_file():
            continue
        if path.name.startswith(MERGED_PREFIX):
            continue
        if path.suffix.lower() not in extensions:
            continue
        files.append(path)
    return sorted(files, key=natural_sort_key)


def require_tool(tool):
    """Ensure a required executable is available."""
    if shutil.which(tool):
        return
    raise MergeVideosError(
        f"Missing required tool: {tool}. Install ffmpeg, which includes ffmpeg and ffprobe."
    )


def probe_video(path):
    """Read stream metadata with ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as error:
        raise MergeVideosError(f"ffprobe timed out while reading {path.name}") from error
    except FileNotFoundError as error:
        raise MergeVideosError(
            "Missing required tool: ffprobe. Install ffmpeg, which includes ffprobe."
        ) from error

    if result.returncode != 0:
        message = result.stderr.strip() or "unknown ffprobe error"
        raise MergeVideosError(f"Could not inspect {path.name}: {message}")

    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise MergeVideosError(f"Could not parse ffprobe output for {path.name}") from error

    streams = metadata.get("streams", [])
    if not streams:
        raise MergeVideosError(f"No media streams found in {path.name}")
    return metadata


def comparison_fields(reference_stream, candidate_stream):
    """Fields that must match for a lossless concat-copy merge."""
    fields = list(STREAM_BASE_FIELDS)
    stream_types = {
        reference_stream.get("codec_type"),
        candidate_stream.get("codec_type"),
    }
    if "video" in stream_types:
        fields.extend(VIDEO_FIELDS)
    if "audio" in stream_types:
        fields.extend(AUDIO_FIELDS)
    return fields


def field_value(stream, field):
    """Use None for absent ffprobe fields so missing-vs-present is visible."""
    return stream.get(field)


def compatibility_errors(files, probes):
    """Return a list of user-facing compatibility mismatch messages."""
    reference_file = files[0]
    reference_streams = probes[0].get("streams", [])
    errors = []

    for path, metadata in zip(files[1:], probes[1:]):
        streams = metadata.get("streams", [])
        file_errors = []

        if len(streams) != len(reference_streams):
            file_errors.append(
                f"stream count {len(streams)} != {len(reference_streams)} in {reference_file.name}"
            )
        else:
            for index, (reference_stream, stream) in enumerate(
                zip(reference_streams, streams)
            ):
                for field in comparison_fields(reference_stream, stream):
                    reference_value = field_value(reference_stream, field)
                    current_value = field_value(stream, field)
                    if current_value != reference_value:
                        file_errors.append(
                            "stream "
                            f"{index} {field}: {current_value!r} != {reference_value!r}"
                        )

        if file_errors:
            errors.append(f"{path.name}:\n  " + "\n  ".join(file_errors))

    return errors


def build_output_path(directory, first_input):
    """Build a timestamped output path using the first input's extension."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return directory / f"{MERGED_PREFIX}{timestamp}{first_input.suffix.lower()}"


def ffconcat_quote(path):
    """Quote a path for ffmpeg concat demuxer manifests."""
    return "'" + str(path).replace("'", "'\\''") + "'"


def write_manifest(files):
    """Write a temporary ffconcat manifest and return its path."""
    manifest = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        prefix="merge-videos-",
        suffix=".ffconcat",
        delete=False,
    )
    try:
        manifest.write("ffconcat version 1.0\n")
        for path in files:
            manifest.write(f"file {ffconcat_quote(path.resolve())}\n")
    finally:
        manifest.close()
    return Path(manifest.name)


def print_merge_plan(files, output_path):
    """Print the detected merge order and output."""
    print(f"Found {len(files)} videos:")
    for index, path in enumerate(files, start=1):
        print(f"  {index}. {path.name}")
    print(f"Output: {output_path.name}")


def merge_videos(files, output_path):
    """Run ffmpeg concat demuxer in stream-copy mode."""
    manifest_path = write_manifest(files)
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(manifest_path),
                "-map",
                "0",
                "-c",
                "copy",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise MergeVideosError(
            "Missing required tool: ffmpeg. Install ffmpeg to merge videos."
        ) from error
    finally:
        manifest_path.unlink(missing_ok=True)

    if result.returncode != 0:
        output_path.unlink(missing_ok=True)
        message = result.stderr.strip() or "unknown ffmpeg error"
        raise MergeVideosError(f"ffmpeg merge failed:\n{message}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge video segments in the current directory with ffmpeg."
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Print the merge plan and compatibility check without writing output.",
    )
    parser.add_argument(
        "--include",
        action="append",
        metavar="EXT",
        help="Only include this extension. Can be repeated, e.g. --include .mp4.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    current_dir = Path.cwd()
    if current_dir == Path(os.path.expanduser("~")):
        print("You are currently in the home directory. Exiting.", file=sys.stderr)
        return 1

    try:
        require_tool("ffprobe")
        require_tool("ffmpeg")

        extensions = normalize_extensions(args.include)
        files = collect_videos(current_dir, extensions)
        if len(files) < 2:
            raise MergeVideosError(
                f"Need at least 2 videos to merge; found {len(files)}."
            )

        output_path = build_output_path(current_dir, files[0])
        if output_path.exists():
            raise MergeVideosError(f"Output already exists: {output_path.name}")

        probes = [probe_video(path) for path in files]
        errors = compatibility_errors(files, probes)
        if errors:
            details = "\n\n".join(errors)
            raise MergeVideosError(
                "Cannot losslessly merge: video segments are not concat-compatible.\n"
                f"Reference file: {files[0].name}\n\n{details}"
            )

        print_merge_plan(files, output_path)
        print("Compatibility: OK for lossless concat copy")
        if args.dry_run:
            return 0

        merge_videos(files, output_path)
        print(f"Merged video written: {output_path.name}")
        return 0
    except MergeVideosError as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
