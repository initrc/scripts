from datetime import datetime
import os
from PIL import Image  # Alternatively, use 'piexif' library
from pillow_heif import register_heif_opener
import re

def get_date_taken(filepath):
    # extract the date taken from the image's EXIF data using Pillow
    try:
        register_heif_opener()
        img = Image.open(filepath)
        exifdata = img.getexif()
        date_taken = exifdata.get(306)
        if date_taken:
            return datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S")
        else:
            return None
    except (IOError, KeyError, ValueError):
        # handle errors like file not found or missing EXIF data
        print(f"[{filepath}] error getting EXIF data")
        return None

"""add a prefix of the date taken in the format of YYYYMMDD-, and lowercase the extension"""
def rename_file(filepath):
    date_taken = get_date_taken(filepath)
    if date_taken:
        old_base, old_ext = os.path.splitext(filepath)
        old_filename = old_base + old_ext.lower()
        new_filename = f"{date_taken.strftime('%Y%m%d')}-{os.path.basename(old_filename)}"
        new_path = os.path.join(os.path.dirname(filepath), new_filename)
        #print(f"{filepath} -> {new_path}")
        os.rename(filepath, new_path)

    else:
        print(f"[{filepath}] missing date info from EXIF")

def traverse_files(directory):
    for root, directories, files in os.walk(directory):
        for filename in files:
            if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".heic")): continue 
            if filename.lower().startswith("2024"): continue

            # skip already formatted files
            pattern = r"^\d{8}\-"
            if re.match(pattern, filename): continue 

            filepath = os.path.join(root, filename)
            rename_file(filepath)

if __name__ == "__main__":
    current_dir = os.getcwd()
    if current_dir == os.path.expanduser("~"):
        print("You are current in the home directry. Exiting.")
        exit()
    traverse_files(current_dir)

