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
2. `creation_time` (or `com.apple.quicktime.creationdate`) from ffprobe (videos only, requires ffmpeg installed; uses timezone info from metadata if present, otherwise converts UTC using system timezone rules for the capture date)
3. Filename -- first valid `YYYYMMDDHHMMSS` or `YYYYMMDD` + `HHMMSS` sequence
4. File modification time (`os.path.getmtime`)

**Identifier:** non-numeric portion of the original filename stem.

**Duplicate handling:** appends `-01`, `-02`, etc. before the extension.

**Dry run:** add `--dry-run` (or `-n`) to print the rename plan without changing files. The created-time `HHMMSS` portion is highlighted in color when it didn't exist in the original name.

### `rename-lower-hyphen.py`

Recursively renames files to lowercase and replaces spaces with hyphens. Operates on the current working directory and subdirectories.

### `merge-videos.py`

Merges video segments from the current directory in natural filename order, so `part2.mp4` comes before `part10.mp4`.

**Supported extensions:** `.mp4`, `.mov`, `.mkv`, `.avi`, `.m4v`

**Output:** writes `merged-YYYYMMDD-HHMMSS<ext>` using the first input file's extension. Existing `merged-*` files are excluded from inputs.

**Merge mode:** uses ffmpeg concat demuxer with `-c copy` for a lossless merge. The script checks stream compatibility first with ffprobe and fails clearly if segments have different codecs, stream counts, video dimensions, pixel formats, audio layout, sample rates, or time bases.

**Dry run:** add `--dry-run` (or `-n`) to print the merge order, output filename, and compatibility result without writing output.

**Extension filter:** add `--include .mp4` to only include a specific extension. Repeat the flag to include multiple extensions.

### `img2html.py`

Renames image files (`.png`, `.jpg`, `.jpeg`) in the current directory to sequential numbers, then writes an `index.html` displaying them in order.

### `automouse.py`

Moves the mouse cursor by one pixel in a random direction every ~5 minutes to prevent the screen from sleeping.

## Dependencies

Managed by uv. See `pyproject.toml`. System dependency: `ffmpeg`/`ffprobe` for video metadata.
