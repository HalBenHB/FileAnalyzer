# serializer.py
import pickle
import os
import pathlib
import hashlib  # For creating a more filename-friendly hash of the target directory
import config  # To get SCAN_DATA_DIRECTORY


def _get_scan_filename(target_dir_path_obj):
    """
    Generates a consistent filename for a given target directory.
    Uses a hash of the absolute path to create a unique and safe filename.
    """
    # Ensure the path is absolute and normalized for consistency
    abs_path_str = str(target_dir_path_obj.resolve())

    # Create a hash of the path string to use as a filename
    # MD5 is fine here as we just need a unique mapping, not cryptographic security
    hasher = hashlib.md5()
    hasher.update(abs_path_str.encode('utf-8'))
    hashed_filename = hasher.hexdigest()

    return f"scan_{hashed_filename}.pkl"


def _get_full_scan_filepath(target_dir):
    """
    Constructs the full path to where the scan data file would be stored.
    """
    target_dir_path_obj = pathlib.Path(target_dir)
    scan_filename = _get_scan_filename(target_dir_path_obj)

    # Ensure SCAN_DATA_DIRECTORY exists
    if not os.path.exists(config.SCAN_DATA_DIRECTORY):
        try:
            os.makedirs(config.SCAN_DATA_DIRECTORY)
            print(f"Created scan data directory: {config.SCAN_DATA_DIRECTORY}")
        except OSError as e:
            print(f"Error creating scan data directory {config.SCAN_DATA_DIRECTORY}: {e}")
            # Fallback or raise error - for now, let's try to proceed if it fails but warn
            pass

    return os.path.join(config.SCAN_DATA_DIRECTORY, scan_filename)


def scan_exists(target_dir):
    """
    Checks if a saved scan file exists for the given target directory.

    Args:
        target_dir (str or pathlib.Path): The directory that was scanned.

    Returns:
        bool: True if a saved scan exists, False otherwise.
    """
    filepath = _get_full_scan_filepath(target_dir)
    return os.path.exists(filepath)


def save_scan(all_file_details, dir_symlink_details, summary_stats, target_dir):
    """
    Saves the scan results to a file using pickle.

    Args:
        all_file_details (list): Data for file-like entries.
        dir_symlink_details (list): Data for directory symlinks.
        summary_stats (dict): Summary statistics.
        target_dir (str or pathlib.Path): The directory that was scanned (used for filename generation).
    """
    filepath = _get_full_scan_filepath(target_dir)
    data_to_save = {
        'all_file_details': all_file_details,
        'dir_symlink_details': dir_symlink_details,
        'summary_stats': summary_stats,
        'original_target_dir': str(pathlib.Path(target_dir).resolve())  # Store for verification
    }

    try:
        with open(filepath, 'wb') as f:
            pickle.dump(data_to_save, f)
        print(f"Scan data successfully saved to: {filepath}")
    except pickle.PicklingError as e:
        print(f"Error pickling data: {e}")
    except IOError as e:
        print(f"Error saving scan data to {filepath}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during save_scan: {e}")


def load_scan(target_dir):
    """
    Loads scan results from a file.

    Args:
        target_dir (str or pathlib.Path): The directory for which to load the scan.

    Returns:
        tuple: (all_file_details, dir_symlink_details, summary_stats) if successful,
               otherwise (None, None, None).
    """
    filepath = _get_full_scan_filepath(target_dir)
    if not os.path.exists(filepath):
        print(f"No saved scan found at: {filepath}")
        return None, None, None

    try:
        with open(filepath, 'rb') as f:
            loaded_data = pickle.load(f)

        # Optional: Verify if the loaded scan matches the requested target_dir
        # This is a basic check. More robust checks could involve timestamps or content hashes.
        original_target_dir_stored = loaded_data.get('original_target_dir')
        current_target_dir_resolved = str(pathlib.Path(target_dir).resolve())
        if original_target_dir_stored != current_target_dir_resolved:
            print(f"Warning: Loaded scan was for '{original_target_dir_stored}', "
                  f"but current request is for '{current_target_dir_resolved}'. Using loaded data anyway.")
            # You could choose to return None here if a strict match is required.

        print(f"Scan data successfully loaded from: {filepath}")
        return (
            loaded_data['all_file_details'],
            loaded_data['dir_symlink_details'],
            loaded_data['summary_stats']
        )
    except pickle.UnpicklingError as e:
        print(f"Error unpickling data from {filepath}: {e}. File might be corrupted or incompatible.")
    except IOError as e:
        print(f"Error loading scan data from {filepath}: {e}")
    except KeyError as e:
        print(f"Error: Saved scan file {filepath} is missing expected data key: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during load_scan: {e}")

    return None, None, None