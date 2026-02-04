from datetime import datetime
import json
import os
from PIL import Image
from pillow_heif import register_heif_opener
import re
import subprocess


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".heic")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi")
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS


def extract_date_from_filename(filename):
    """Find first 8-digit sequence in stem that is a valid YYYYMMDD date."""
    stem = os.path.splitext(filename)[0]
    for match in re.finditer(r"\d{8}", stem):
        candidate = match.group()
        try:
            datetime.strptime(candidate, "%Y%m%d")
            return candidate, match.start(), match.end()
        except ValueError:
            continue
    return None


def get_exif_date(filepath):
    """Read EXIF tag 306 (ModifyDate) via Pillow."""
    try:
        register_heif_opener()
        img = Image.open(filepath)
        exifdata = img.getexif()
        date_str = exifdata.get(306)
        if date_str:
            dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            return dt.strftime("%Y%m%d")
    except (IOError, KeyError, ValueError):
        pass
    return None


def get_video_date(filepath):
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
        creation_time = metadata.get("format", {}).get("tags", {}).get("creation_time")
        if creation_time:
            dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
            return dt.strftime("%Y%m%d")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, FileNotFoundError):
        pass
    return None


def get_mtime_date(filepath):
    """Fallback: file modification time."""
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime).strftime("%Y%m%d")


def get_date(filepath):
    """Orchestrate date extraction with priority chain."""
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()

    # 1. From filename
    result = extract_date_from_filename(filename)
    if result:
        return result[0], "filename"

    # 2. From EXIF (images only)
    if ext in IMAGE_EXTENSIONS:
        date = get_exif_date(filepath)
        if date:
            return date, "exif"

    # 3. From video metadata
    if ext in VIDEO_EXTENSIONS:
        date = get_video_date(filepath)
        if date:
            return date, "video"

    # 4. Fallback: mtime
    return get_mtime_date(filepath), "mtime"


def build_new_filename(filename, date, source):
    """Build new filename with date prefix. Remove date from original position
    if it came from the filename, normalize .jpeg -> .jpg."""
    stem, ext = os.path.splitext(filename)

    if ext.lower() == ".jpeg":
        ext = ".jpg"
    else:
        ext = ext.lower()

    if source == "filename":
        result = extract_date_from_filename(filename)
        if result:
            _, start, end = result
            # Remove the date from the stem
            new_stem = stem[:start] + stem[end:]
            # Clean up leftover separators at the join point
            new_stem = re.sub(r"[-_ ]{2,}", lambda m: m.group()[0], new_stem)
            new_stem = new_stem.strip("-_ ")
            return f"{date}-{new_stem}{ext}"

    return f"{date}-{stem}{ext}"


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


def rename_file(filepath):
    """Orchestrate single file rename."""
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    date, source = get_date(filepath)
    new_filename = build_new_filename(filename, date, source)
    new_filename = resolve_conflict(directory, new_filename)

    new_path = os.path.join(directory, new_filename)
    os.rename(filepath, new_path)
    print(f"{filepath} -> {new_path}")


def traverse_files(directory):
    """Recursively walk directory, rename supported files, skip already-prefixed."""
    for root, directories, files in os.walk(directory):
        for filename in files:
            if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
                continue
            if re.match(r"^\d{8}-", filename):
                continue
            filepath = os.path.join(root, filename)
            rename_file(filepath)


if __name__ == "__main__":
    current_dir = os.getcwd()
    if current_dir == os.path.expanduser("~"):
        print("You are currently in the home directory. Exiting.")
        exit()
    traverse_files(current_dir)
