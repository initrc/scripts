import os


def rename_files(directory):
    """Traverses a directory and its subdirectories, renaming files to lowercase and replacing spaces with hyphens."""

    for root, directories, files in os.walk(directory):
        for filename in files:
            old_path = os.path.join(root, filename)
            new_filename = filename.lower().replace(" ", "-")
            new_path = os.path.join(root, new_filename)

            if old_path == new_path:
                continue

            try:
                os.rename(old_path, new_path)
                print(f"Renamed '{old_path}' to '{new_path}'")
            except OSError as error:
                print(f"Error renaming '{old_path}': {error}")


if __name__ == "__main__":
    current_dir = os.getcwd()
    if current_dir == os.path.expanduser("~"):
        print("You are currently in the home directory. Exiting.")
        exit()
    rename_files(current_dir)
