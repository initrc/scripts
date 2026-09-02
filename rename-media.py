import argparse
import json
import os
import re
import subprocess
from datetime import UTC, datetime, timedelta

from PIL import Image
from pillow_heif import register_heif_opener

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".heic")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi")
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS
UNCHANGED_DIRECTORY = "unchanged"
ANSI_BLUE_BOLD = "\033[1;34m"
ANSI_RESET = "\033[0m"


def extract_datetime_from_filename(filename):
    """Find a datetime in the filename, including WeChat timestamps."""
    wechat_datetime = extract_wechat_datetime(filename)
    if wechat_datetime:
        return wechat_datetime

    stem = os.path.splitext(filename)[0]
    for match in re.finditer(r"\d{14}", stem):
        candidate = match.group()
        try:
            dt = datetime.strptime(candidate, "%Y%m%d%H%M%S")
            return dt
        except ValueError:
            continue
    for date_match in re.finditer(r"\d{8}", stem):
        date_part = date_match.group()
        try:
            datetime.strptime(date_part, "%Y%m%d")
        except ValueError:
            continue
        remainder = stem[date_match.end():]
        time_match = re.search(r"\d{6}", remainder)
        if time_match:
            time_part = time_match.group()
            try:
                dt = datetime.strptime(date_part + time_part, "%Y%m%d%H%M%S")
                return dt
            except ValueError:
                continue
    return None


def extract_wechat_datetime(filename):
    """Extract a local datetime from a WeChat millisecond timestamp filename."""
    stem = os.path.splitext(os.path.basename(filename))[0]
    match = re.fullmatch(r"mmexport(\d{13})", stem, re.IGNORECASE)
    if not match:
        return None
    try:
        return (
            datetime.fromtimestamp(
                int(match.group(1)) / 1000,
                tz=UTC,
            )
            .astimezone()
            .replace(tzinfo=None)
        )
    except (OSError, OverflowError, ValueError):
        return None


def get_exif_datetime(filepath):
    """Read EXIF datetime via Pillow. Prefer DateTimeOriginal/DateTimeDigitized."""
    try:
        register_heif_opener()
        img = Image.open(filepath)
        exifdata = img.getexif()
        for tag in (36867, 36868, 306):
            date_str = exifdata.get(tag)
            if not date_str:
                continue
            dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            return dt
    except (OSError, KeyError, ValueError):
        pass
    return None


def get_video_datetime(filepath):
    """Read creation_time via ffprobe subprocess."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                filepath,
            ],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None
        metadata = json.loads(result.stdout)
        tags = metadata.get("format", {}).get("tags", {})
        for key in (
            "creation_time",
            "com.apple.quicktime.creationdate",
        ):
            creation_time = tags.get(key)
            if not creation_time:
                continue
            dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt
            # If metadata is UTC (+00:00), convert using local timezone at dt's date.
            if dt.utcoffset() == timedelta(0):
                # Use timezone rules at the capture date, not current time.
                return datetime.fromtimestamp(dt.timestamp())
            # Otherwise, use the timezone from metadata.
            return dt.replace(tzinfo=None)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, FileNotFoundError):
        pass
    return None


def get_datetime(filepath):
    """Orchestrate datetime extraction with priority chain."""
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()

    # 1. From EXIF (images only)
    if ext in IMAGE_EXTENSIONS:
        dt = get_exif_datetime(filepath)
        if dt:
            return dt, "exif"

    # 2. From a WeChat image filename (the timestamp is in milliseconds).
    if ext in IMAGE_EXTENSIONS:
        dt = extract_wechat_datetime(filename)
        if dt:
            return dt, "wechat"

    # 3. From video metadata
    if ext in VIDEO_EXTENSIONS:
        dt = get_video_datetime(filepath)
        if dt:
            return dt, "video"

    # 4. From filename
    dt = extract_datetime_from_filename(filename)
    if dt:
        return dt, "filename"

    # No reliable datetime found; do not use the file modification time.
    return None, "unknown"


def set_exif_comment(filepath, comment):
    """Store the original filename in the image's Comment tag via exiftool."""
    try:
        result = subprocess.run(
            [
                "exiftool",
                "-overwrite_original",
                f"-Comment={comment}",
                filepath,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError as error:
        raise OSError(
            "exiftool is required to write the WeChat filename to EXIF Comment"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise OSError(f"exiftool timed out while writing {filepath}") from error

    if result.returncode != 0:
        message = result.stderr.strip() or "unknown exiftool error"
        raise OSError(f"Could not write EXIF Comment for {filepath}: {message}")


def extract_identifier(filename):
    """Return IMG for images or VID for videos with an identifier in the stem."""
    stem = os.path.splitext(filename)[0]
    identifier = re.sub(r"\d", "", stem)
    identifier = identifier.strip("-_ ")
    if len(identifier) > 0:
        extension = os.path.splitext(filename)[1].lower()
        identifier = "VID" if extension in VIDEO_EXTENSIONS else "IMG"
    return identifier


def build_new_filename(filename, dt):
    """Build new filename as YYYYMMDD-IDENTIFIERHHMMSS, normalize .jpeg -> .jpg."""
    stem, ext = os.path.splitext(filename)

    if ext.lower() == ".jpeg":
        ext = ".jpg"
    else:
        ext = ext.lower()

    date_part = dt.strftime("%Y%m%d")
    time_part = dt.strftime("%H%M%S")
    identifier = extract_identifier(filename)

    return f"{date_part}-{identifier}{time_part}{ext}"


def highlight_time(filename, new_filename):
    """Highlight numeric substrings in the new filename if they weren't in the old name."""
    old_stem = os.path.splitext(filename)[0]
    new_stem, ext = os.path.splitext(new_filename)

    if not re.search(r"\d", new_stem):
        return new_filename

    parts = []
    last_idx = 0
    for match in re.finditer(r"\d+", new_stem):
        start, end = match.span()
        numeric = match.group()
        parts.append(new_stem[last_idx:start])
        if numeric in old_stem:
            parts.append(numeric)
        else:
            parts.append(f"{ANSI_BLUE_BOLD}{numeric}{ANSI_RESET}")
        last_idx = end
    parts.append(new_stem[last_idx:])
    return f"{''.join(parts)}{ext}"


def resolve_conflict(directory, filename):
    """Append -01, -02, etc. if file already exists."""
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return filename

    stem, ext = os.path.splitext(filename)
    index = 1
    while True:
        candidate = f"{stem}-{index:02d}{ext}"
        if not os.path.exists(os.path.join(directory, candidate)):
            return candidate
        index += 1


def move_to_unchanged(filepath):
    """Move a file into an unchanged subfolder and return its new filename."""
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    unchanged_directory = os.path.join(directory, UNCHANGED_DIRECTORY)
    try:
        os.makedirs(unchanged_directory, exist_ok=True)
        unchanged_filename = resolve_conflict(unchanged_directory, filename)
        os.rename(filepath, os.path.join(unchanged_directory, unchanged_filename))
    except OSError:
        raise
    return unchanged_filename


def rename_file(filepath, dry_run=False):
    """Rename one file or return a result describing why it was not renamed."""
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    dt, source = get_datetime(filepath)
    if dt is None:
        result = {
            "section": "unchanged",
            "directory": directory,
            "display": filename,
        }
        if not dry_run:
            try:
                unchanged_filename = move_to_unchanged(filepath)
                result["display"] = (
                    f"{filename} -> {UNCHANGED_DIRECTORY}/{unchanged_filename}"
                )
            except OSError as error:
                result["error"] = str(error)
        return result

    new_filename = build_new_filename(filename, dt)
    if filename == new_filename:
        return None
    new_filename = resolve_conflict(directory, new_filename)

    display_name = highlight_time(filename, new_filename)
    result = {
        "section": "renamed",
        "directory": directory,
        "display": f"{filename} -> {display_name}",
    }
    if dry_run:
        if source == "wechat":
            result["wechat_comment"] = filename
        return result

    new_path = os.path.join(directory, new_filename)
    comment_set = False
    try:
        if source == "wechat":
            set_exif_comment(filepath, filename)
            comment_set = True
        os.rename(filepath, new_path)
    except OSError as error:
        result = {
            "section": "errors",
            "directory": directory,
            "display": f"{filename}: {error!s}",
        }
        if comment_set:
            result["wechat_comment"] = filename
        return result
    if comment_set:
        result["wechat_comment"] = filename
    return result


def print_section(title, files_by_directory):
    """Print a section with each directory path followed by its file names."""
    if not files_by_directory:
        return

    print(f"\n{title}:")
    for directory, files in files_by_directory.items():
        print(directory)
        for filename in files:
            print(f"  {filename}")


def traverse_files(directory, dry_run=False):
    """Recursively process supported files and print grouped results."""
    sections = {}
    directory = os.path.abspath(directory)

    for root, directories, files in os.walk(directory):
        directories[:] = [
            child for child in directories if child != UNCHANGED_DIRECTORY
        ]
        for filename in files:
            if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
                continue
            filepath = os.path.join(root, filename)
            result = rename_file(filepath, dry_run=dry_run)
            if result is None:
                continue
            section = result["section"]
            sections.setdefault(section, {}).setdefault(
                result["directory"], []
            ).append(result["display"])
            if "wechat_comment" in result:
                sections.setdefault("wechat_comments", {}).setdefault(
                    result["directory"], []
                ).append(result["wechat_comment"])
            if "error" in result:
                sections.setdefault("errors", {}).setdefault(
                    result["directory"], []
                ).append(f"{filename}: {result['error']}")

    print_section(
        "Files to rename" if dry_run else "Renamed files",
        sections.get("renamed", {}),
    )
    print_section(
        "WeChat original filenames to store in Comment"
        if dry_run
        else "WeChat original filenames stored in Comment",
        sections.get("wechat_comments", {}),
    )
    print_section(
        "Unchanged files (no usable date found)",
        sections.get("unchanged", {}),
    )
    print_section("Errors", sections.get("errors", {}))


def parse_args():
    parser = argparse.ArgumentParser(description="Rename media files by taken datetime.")
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Print the rename plan without renaming files.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    current_dir = os.getcwd()
    if current_dir == os.path.expanduser("~"):
        print("You are currently in the home directory. Exiting.")
        exit()
    traverse_files(current_dir, dry_run=args.dry_run)
