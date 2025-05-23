import os
import pathlib

def get_target_directory(os_name):
    """
    Prompts the user for a directory to analyze or defaults to the root directory.
    Returns a pathlib.Path object or None if input is invalid.
    """
    if os_name == "Windows":
        default_root = pathlib.Path("C:\\")
    elif os_name == "Linux":
        default_root = pathlib.Path("/")
    else:
        print("Cannot determine default root for unknown OS.")
        return None

    while True:
        prompt_message = (
            f"Enter the directory path to analyze, or press Enter to use the default root ({default_root}): "
        )
        user_input = input(prompt_message).strip()

        if not user_input:
            print(f"No path entered, defaulting to root directory: {default_root}")
            target_path = default_root
        else:
            target_path = pathlib.Path(user_input)

        if target_path.exists():
            if target_path.is_dir():
                print(f"Selected directory: {target_path}")
                return target_path
            else:
                print(f"Error: '{target_path}' is a file, not a directory. Please enter a valid directory path.")
        else:
            print(f"Error: Path '{target_path}' does not exist. Please enter a valid path.")

        retry = input("Do you want to try entering a directory again? (yes/no): ").strip().lower()
        if retry != 'yes':
            return None


def is_hidden(filepath, os_name):
    """
    Checks if a file is hidden based on OS conventions.
    filepath should be a pathlib.Path object.
    """
    if os_name == "Windows":
        try:
            # FILE_ATTRIBUTE_HIDDEN is 2
            return bool(filepath.stat().st_file_attributes & 2)
        except (OSError, AttributeError): # AttributeError if st_file_attributes doesn't exist
            return False
    elif os_name == "Linux":
        return filepath.name.startswith('.')
    return False
