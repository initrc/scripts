from datetime import datetime
import os
from PIL import Image  # Alternatively, use 'piexif' library
from pillow_heif import register_heif_opener
import re

"""extract the Make tag taken from the image's EXIF data using Pillow"""
"""https://exiftool.org/TagNames/EXIF.html"""
def get_make(filepath):
    try:
        register_heif_opener()
        img = Image.open(filepath)
        exifdata = img.getexif()
        make = exifdata.get(271)
        return make
    except (IOError, KeyError, ValueError):
        # handle errors like file not found or missing EXIF data
        print(f"[{filepath}] error getting EXIF data")
        return None

"""extract the ModifyDate tag taken from the image's EXIF data using Pillow"""
def get_date_taken(filepath):
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
        make = get_make(filepath)
        # rename if the make is OPPO
        if make == "OPPO":
            date = f"{date_taken.strftime('%Y%m%d')}"
            time = f"{date_taken.strftime('%H%M%S')}"
            rename_oppo_file(filepath, date, time)
            return
        # rename if %Y-%m-%d is already in the filename like taken by dazz
        dazz_date = f"{date_taken.strftime('%Y-%m-%d')}"
        if dazz_date in old_base:
            rename_dazz_file(filepath, dazz_date)
            return
        # standardize jpg extensions
        if old_ext.lower() == ".jpeg":
            old_ext = ".jpg"
        old_filename = old_base + old_ext.lower()
        new_filename = f"{date_taken.strftime('%Y%m%d')}-{os.path.basename(old_filename)}"
        new_path = os.path.join(os.path.dirname(filepath), new_filename)
        # print(f"{filepath} -> {new_path}")
        os.rename(filepath, new_path)

    else:
        print(f"[{filepath}] missing date info from EXIF")

"""rename photos take by oppo"""
def rename_oppo_file(filepath, date, time):
    old_base, old_ext = os.path.splitext(filepath)
    new_filename = date + '-IMG' + time + old_ext.lower()
    new_path = os.path.join(os.path.dirname(filepath), new_filename)

    index = 1
    while os.path.exists(new_path):
        new_filename = "%s-IMG%s-%02d%s" % (date, time, index, old_ext.lower())
        new_path = os.path.join(os.path.dirname(filepath), new_filename)
        index += 1

    # print(f"{filepath} -> {new_path}")
    os.rename(filepath, new_path)

"""rename photos take by dazz"""
def rename_dazz_file(filepath, date):
    old_base, old_ext = os.path.splitext(filepath)
    new_date = date.replace('-', '')
    old_filename = old_base + old_ext.lower()
    new_filename = new_date + '-' + '-'.join([s for s in os.path.basename(old_filename).split() if s != date])
    new_path = os.path.join(os.path.dirname(filepath), new_filename)
    # print(f"{filepath} -> {new_path}")
    os.rename(filepath, new_path)

def traverse_files(directory):
    for root, directories, files in os.walk(directory):
        for filename in files:
            if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".heic")): continue 
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

