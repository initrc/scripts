# Scripts

A collection of scripts for organizing media files.

## Running

Scripts are run with uv:

```sh
uv run --project ~/code/scripts python ~/code/scripts/<script>.py
```

Scripts operate on the current working directory (and subdirectories recursively). They refuse to run from `~` as a safety measure.

## Scripts

### `rename-photos.py`

Camera-specific photo renaming. Handles OPPO and Dazz camera files using EXIF data (tag 271 for Make, tag 306 for ModifyDate). Prepends `YYYYMMDD-` prefix and normalizes extensions.

### `rename-media.py`

General-purpose media file renaming. Prepends a `YYYYMMDD-` date prefix to photos and videos.

**Supported extensions:** `.jpg`, `.jpeg`, `.png`, `.heic`, `.mp4`, `.mov`, `.mkv`, `.avi`

**Date extraction priority:**
1. Filename — first valid `YYYYMMDD` sequence (removed from original position and prepended as prefix)
2. EXIF tag 306 (images only, via Pillow + pillow-heif)
3. `creation_time` from ffprobe (videos only, requires ffmpeg installed)
4. File modification time (`os.path.getmtime`)

**Duplicate handling:** appends `-01`, `-02`, etc. before the extension.

**Skips** files already matching `^\d{8}-`.

## Dependencies

Managed by uv. See `pyproject.toml`. System dependency: `ffmpeg`/`ffprobe` for video metadata.
