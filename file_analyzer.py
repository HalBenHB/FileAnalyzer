# file_analyzer.py

import os
import platform
import pathlib


# import shutil # We'll add this when we need it
# import pandas as pd # For later
# import matplotlib.pyplot as plt # For later
# import numpy as np # For later
# import scipy.stats # For later

def detect_os():
    """Detects the current operating system."""
    system = platform.system()
    if system == "Windows":
        return "Windows"
    elif system == "Linux":  # Ubuntu is a Linux distribution
        return "Linux"
    else:
        return "Unknown"


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
        # Should not happen if detect_os is working
        print("Cannot determine default root for unknown OS.")
        return None

    while True:
        prompt_message = (
            f"Enter the directory path to analyze, or press Enter to use the default root ({default_root}): "
        )
        user_input = input(prompt_message).strip()

        if not user_input:  # User pressed Enter
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

        # Ask if user wants to try again or exit
        retry = input("Do you want to try entering a directory again? (yes/no): ").strip().lower()
        if retry != 'yes':
            return None


def basic_traverse_directory(directory_path):
    """
    Traverses the given directory and prints names of files and subdirectories.
    Handles potential PermissionError exceptions.
    """
    print(f"\nStarting basic traversal of: {directory_path}\n")
    # We will count these later
    file_count = 0
    dir_count = 0

    for root, dirs, files in os.walk(directory_path, topdown=True, onerror=None):
        # 'onerror=None' will skip directories that cause errors (like permission errors)
        # but os.walk will still print a message to stderr.
        # For more control, we'd handle errors within the loop or provide a custom error handler.

        current_path_obj = pathlib.Path(root)
        #print(f"Current directory: {current_path_obj}")

        # Process directories
        for name in dirs:
            dir_path = current_path_obj / name
            # For now, just acknowledge them. We could add specific handling if needed.
            # print(f"  Subdirectory: {name}")
            dir_count += 1

        # Process files
        for name in files:
            file_path = current_path_obj / name
            # For now, just acknowledge them.
            # print(f"  File: {name}")
            file_count += 1

        # Optional: Add a small delay or a counter to show progress for large directories
        # print(f"Processed {file_count} files and {dir_count} directories in {current_path_obj}...")

    print(f"\nBasic traversal complete for: {directory_path}")
    print(f"Found (approximately) {file_count} files and {dir_count} directories.")
    print("Note: Counts might be affected by skipped directories due to permissions.")


def main():
    """Main function to run the file analysis."""
    current_os = detect_os()
    print(f"Running on: {current_os}")

    if current_os == "Unknown":
        print("Unsupported operating system. Exiting.")
        return

    print("Project: File Analysis - CS350")

    target_dir = get_target_directory(current_os)

    if target_dir:
        try:
            basic_traverse_directory(target_dir)
        except Exception as e:
            print(f"An unexpected error occurred during directory traversal: {e}")
    else:
        print("No valid directory selected or user chose to exit. Exiting program.")


if __name__ == "__main__":
    main()