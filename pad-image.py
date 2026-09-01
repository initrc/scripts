import argparse
import os
import sys

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

DEFAULT_BG_WIDTH = 3440
DEFAULT_BG_HEIGHT = 1440
DEFAULT_FG_HEIGHT = 720
DEFAULT_PADDING = 100


def positive_int(value: str) -> int:
    """Parse and validate a positive integer CLI argument."""
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer (must be > 0)")
    return ivalue


def get_output_path(image_path: str) -> str:
    """Generate output path with -pad postfix in the same directory as input image."""
    dirname, filename = os.path.split(image_path)
    stem, ext = os.path.splitext(filename)
    out_ext = ext
    if ext.lower() in (".heic", ".heif"):
        out_ext = ".jpg"
    out_filename = f"{stem}-pad{out_ext}"
    return os.path.join(dirname, out_filename) if dirname else out_filename


def pad_images(
    image_paths: list[str],
    bg_width: int = DEFAULT_BG_WIDTH,
    bg_height: int = DEFAULT_BG_HEIGHT,
    fg_height: int = DEFAULT_FG_HEIGHT,
    padding: int = DEFAULT_PADDING,
    output_path: str | None = None,
) -> str:
    """Resize images proportionally to fg_height, lay them out horizontally with padding,

    and center on a pure black canvas of bg_width x bg_height.
    """
    if not image_paths:
        raise ValueError("At least one image path must be provided.")

    register_heif_opener()

    resized_images: list[Image.Image] = []
    try:
        for path in image_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Input image not found: {path}")

            with Image.open(path) as raw_img:
                img = ImageOps.exif_transpose(raw_img)
                orig_width, orig_height = img.size
                if orig_height <= 0 or orig_width <= 0:
                    raise ValueError(f"Invalid image dimensions for '{path}': {orig_width}x{orig_height}")

                # Calculate proportional width for fg_height
                scale = fg_height / orig_height
                fg_width = max(1, round(orig_width * scale))

                # Resize foreground
                fg_resized = img.resize((fg_width, fg_height), Image.Resampling.LANCZOS)
                # Keep in memory as a separate copy so raw_img file handle can close
                resized_images.append(fg_resized.copy())

        # Calculate total width with padding
        num_images = len(resized_images)
        total_padding = max(0, (num_images - 1) * padding)
        total_fg_width = sum(im.width for im in resized_images) + total_padding

        # Create pure black background canvas
        bg = Image.new("RGB", (bg_width, bg_height), (0, 0, 0))

        # Center composite horizontally and vertically
        start_x = (bg_width - total_fg_width) // 2
        y = (bg_height - fg_height) // 2

        # Paste images horizontally
        current_x = start_x
        for fg_img in resized_images:
            if fg_img.mode in ("RGBA", "LA") or (
                fg_img.mode == "P" and "transparency" in fg_img.info
            ):
                fg_rgba = fg_img.convert("RGBA")
                bg.paste(fg_rgba, (current_x, y), fg_rgba)
            else:
                fg_rgb = fg_img.convert("RGB")
                bg.paste(fg_rgb, (current_x, y))
            current_x += fg_img.width + padding

        if not output_path:
            output_path = get_output_path(image_paths[0])

        bg.save(output_path)
        return output_path
    finally:
        for im in resized_images:
            im.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Place one or more images resized to fg_height horizontally onto a pure black canvas of bg_width x bg_height."
    )
    parser.add_argument(
        "args",
        nargs="+",
        help="One or more image paths, optionally followed by bg_width, bg_height, fg_height.",
    )
    parser.add_argument(
        "--bg-width",
        type=positive_int,
        help=f"Width of the black background canvas (default: {DEFAULT_BG_WIDTH})",
    )
    parser.add_argument(
        "--bg-height",
        type=positive_int,
        help=f"Height of the black background canvas (default: {DEFAULT_BG_HEIGHT})",
    )
    parser.add_argument(
        "--fg-height",
        type=positive_int,
        help=f"Target height of the resized foreground images (default: {DEFAULT_FG_HEIGHT})",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=DEFAULT_PADDING,
        help=f"Padding in pixels between horizontal images (default: {DEFAULT_PADDING})",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional explicit output path (defaults to <first_image>-pad.<ext>)",
    )

    parsed = parser.parse_args()
    pos = list(parsed.args)

    # Extract trailing positional dimensions if present (e.g. img1.png img2.png 1920 1080 600)
    dims: list[int] = []
    while len(pos) > 1 and pos[-1].isdigit() and not os.path.exists(pos[-1]):
        dims.insert(0, int(pos.pop()))
        if len(dims) == 3:
            break

    bg_width = parsed.bg_width or (dims[0] if len(dims) >= 1 else DEFAULT_BG_WIDTH)
    bg_height = parsed.bg_height or (dims[1] if len(dims) >= 2 else DEFAULT_BG_HEIGHT)
    fg_height = parsed.fg_height or (dims[2] if len(dims) >= 3 else DEFAULT_FG_HEIGHT)

    return pos, bg_width, bg_height, fg_height, parsed.padding, parsed.output


if __name__ == "__main__":
    current_dir = os.getcwd()
    if current_dir == os.path.expanduser("~"):
        print("You are currently in the home directory. Exiting.")
        sys.exit(1)

    image_paths, bg_w, bg_h, fg_h, pad_px, out_path = parse_args()
    try:
        saved_file = pad_images(
            image_paths=image_paths,
            bg_width=bg_w,
            bg_height=bg_h,
            fg_height=fg_h,
            padding=pad_px,
            output_path=out_path,
        )
        print(f"Created: {saved_file}")
    except (OSError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
