import glob
import os


IMAGE_EXTENSIONS = ("*.png", "*.jpg", "*.jpeg")


def collect_images():
    """Collect all supported image files in the current directory, sorted."""
    files = []
    for pattern in IMAGE_EXTENSIONS:
        files.extend(glob.glob(pattern))
    return sorted(set(files))


def rename_to_sequential(files):
    """Rename image files to sequential numbers, preserving extensions."""
    digits = len(str(len(files)))
    renamed = []
    for i, oldfile in enumerate(files, start=1):
        ext = os.path.splitext(oldfile)[1].lower()
        newfile = f"{str(i).zfill(digits)}{ext}"
        os.rename(oldfile, newfile)
        print(f"{oldfile} -> {newfile}")
        renamed.append(newfile)
    return renamed


def write_html(files):
    """Write an index.html displaying all images in order."""
    images = [f"<img src='{f}' style='max-width:100%' />" for f in files]
    html = f"<html><body>\n{chr(10).join(images)}\n</body></html>"
    with open("index.html", "w") as f:
        f.write(html)
    print(f"Wrote index.html with {len(files)} images")


if __name__ == "__main__":
    current_dir = os.getcwd()
    if current_dir == os.path.expanduser("~"):
        print("You are currently in the home directory. Exiting.")
        exit()
    files = collect_images()
    if not files:
        print("No image files found.")
        exit()
    renamed = rename_to_sequential(files)
    write_html(renamed)
