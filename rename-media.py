from datetime import datetime, timedelta
import argparse
import json
import os
from PIL import Image
from pillow_heif import register_heif_opener
import re
import subprocess


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".heic")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi")
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS
ANSI_BLUE_BOLD = "\033[1;34m"
ANSI_RESET = "\033[0m"


def extract_datetime_from_filename(filename):
    """Find a datetime in the filename. Prefer 14-digit YYYYMMDDHHMMSS."""
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
    except (IOError, KeyError, ValueError):
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


def get_mtime_datetime(filepath):
    """Fallback: file modification time."""
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime)


def get_datetime(filepath):
    """Orchestrate datetime extraction with priority chain."""
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()

    # 1. From EXIF (images only)
    if ext in IMAGE_EXTENSIONS:
        dt = get_exif_datetime(filepath)
        if dt:
            return dt, "exif"

    # 2. From video metadata
    if ext in VIDEO_EXTENSIONS:
        dt = get_video_datetime(filepath)
        if dt:
            return dt, "video"

    # 3. From filename
    dt = extract_datetime_from_filename(filename)
    if dt:
        return dt, "filename"

    # 4. Fallback: mtime
    return get_mtime_datetime(filepath), "mtime"


def extract_identifier(filename):
    """Return the non-numeric identifier portion of the filename stem."""
    stem = os.path.splitext(filename)[0]
    identifier = re.sub(r"\d", "", stem)
    identifier = identifier.strip("-_ ")
    if len(identifier) > 0:
        identifier = "IMG"
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


def rename_file(filepath, dry_run=False):
    """Orchestrate single file rename."""
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    dt, _source = get_datetime(filepath)
    new_filename = build_new_filename(filename, dt)
    if filename == new_filename:
        return
    new_filename = resolve_conflict(directory, new_filename)

    display_name = highlight_time(filename, new_filename)
    if dry_run:
        print(f"{filepath} -> {display_name}")
        return

    new_path = os.path.join(directory, new_filename)
    os.rename(filepath, new_path)
    print(f"{filepath} -> {display_name}")


def traverse_files(directory, dry_run=False):
    """Recursively walk directory, rename supported files, skip already-prefixed."""
    for root, directories, files in os.walk(directory):
        for filename in files:
            if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
                continue
            filepath = os.path.join(root, filename)
            rename_file(filepath, dry_run=dry_run)


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
