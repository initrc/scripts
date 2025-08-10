import os

def rename_files(directory):
    """Traverses a directory and its subdirectories, renaming files to lowercase and replacing spaces with hyphens."""

    for root, directories, files in os.walk(directory):
        prefix = "20250809-"
        for filename in files:
            old_path = os.path.join(root, filename)
            new_filename = prefix + filename.lower().replace("jpeg", "jpg")
            new_path = os.path.join(root, new_filename)

            try:
                os.rename(old_path, new_path)
                print(f"Renamed '{old_path}' to '{new_path}'")
            except OSError as error:
                print(f"Error renaming '{old_path}': {error}")

if __name__ == "__main__":
    current_dir = os.getcwd()
    if current_dir == os.path.expanduser("~"):
        print("You are current in the home directry. Exiting.")
        exit()
    rename_files(current_dir)

