# Scripts

A collection of scripts for organizing media files.

## Running

Scripts are run with uv:

```sh
uv run --project ~/code/scripts python ~/code/scripts/<script>.py
```

Scripts operate on the current working directory (and subdirectories recursively where applicable). They refuse to run from `~` as a safety measure.

## Scripts

### `rename-media.py`

General-purpose media file renaming. Renames to `YYYYMMDD-IDENTIFIERHHMMSS` for photos and videos.

**Supported extensions:** `.jpg`, `.jpeg`, `.png`, `.heic`, `.mp4`, `.mov`, `.mkv`, `.avi`

**Datetime extraction priority:**
1. EXIF DateTimeOriginal/DateTimeDigitized/ModifyDate (images only, via Pillow + pillow-heif)
2. `creation_time` from ffprobe (videos only, requires ffmpeg installed, converted to local timezone)
3. Filename -- first valid `YYYYMMDDHHMMSS` or `YYYYMMDD` + `HHMMSS` sequence
4. File modification time (`os.path.getmtime`)

**Identifier:** non-numeric portion of the original filename stem.

**Duplicate handling:** appends `-01`, `-02`, etc. before the extension.

**Skips** files already matching `^\d{8}-`.

### `rename-lower-hyphen.py`

Recursively renames files to lowercase and replaces spaces with hyphens. Operates on the current working directory and subdirectories.

### `img2html.py`

Renames image files (`.png`, `.jpg`, `.jpeg`) in the current directory to sequential numbers, then writes an `index.html` displaying them in order.

### `automouse.py`

Moves the mouse cursor by one pixel in a random direction every ~5 minutes to prevent the screen from sleeping.

## Dependencies

Managed by uv. See `pyproject.toml`. System dependency: `ffmpeg`/`ffprobe` for video metadata.
