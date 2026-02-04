# Scripts

A collection of scripts for organizing media files. See `README.md` for script descriptions.

## Running

Scripts are run with uv:

```sh
uv run --project ~/code/scripts python ~/code/scripts/<script>.py
```

Scripts operate on the current working directory (and subdirectories recursively). They refuse to run from `~` as a safety measure.

## Conventions

- No shebangs -- scripts are run via `uv run`.
- All scripts that modify files include a `~` home directory safety check.
- Dependencies are managed in `pyproject.toml`.
- System dependency: `ffmpeg`/`ffprobe` for video metadata.
