# directory_analyzer.py
import os
import pathlib
import collections
import sys
from fs_utils import is_hidden

# Define constants for special types to avoid magic strings
SYMLINK_TYPE_STR = ".<symlink>"
BROKEN_SYMLINK_TYPE_STR = ".<broken_symlink>"
SYMLINK_TO_DIR_TYPE_STR = ".<symlink_to_dir>"  # Specifically for symlinks that ARE directories
SYMLINK_ERROR_TYPE_STR = ".<symlink_error>"
NON_FILE_TYPE_STR = ".<non_file_type>"
ERROR_TYPE_STR = ".<error_processing>"
NO_EXTENSION_STR = ".<no_ext>"

# Progress update interval
PROGRESS_UPDATE_INTERVAL_FILES = 500 # Update every 500 files
PROGRESS_UPDATE_INTERVAL_DIRS = 50 # Update after every 50 directories (roots visited)


# We'll add a new list to store directory symlink info
# This will be separate from all_files_data which is for items os.walk considers "files"

def analyze_directory(directory_path, os_name):
    """
    Traverses the given directory, collects file information,
    treating symlinks as distinct items with their own sizes.
    Also identifies directory symbolic links and shows progress.
    """
    print(f"\nStarting analysis of: {directory_path}\n")
    # Make directory_path absolute for clearer progress messages
    abs_directory_path = pathlib.Path(directory_path).resolve()
    print(f"Analyzing: {abs_directory_path}")

    all_files_data = []
    directory_symlinks_data = []

    total_files_processed_in_walk = 0  # Tracks files processed within the os.walk loop for progress
    total_dirs_processed_in_walk = 0  # Tracks dirs processed within os.walk for progress

    # Counters for summary
    final_total_files_processed = 0
    final_total_dir_symlinks_found = 0
    skipped_access_errors = 0
    visited_roots = 0

    file_types_count = collections.defaultdict(int)
    file_types_size = collections.defaultdict(int)

    # Spinner characters for a simple animation
    spinner_chars = ['|', '/', '-', '\\']
    spinner_idx = 0

    def walk_error_handler(os_error):
        nonlocal skipped_access_errors
        # Using \r and end='' to overwrite the line for errors can be messy with other prints
        # So, just print errors on a new line.
        print(f"\nAccess denied or error reading directory: {os_error.filename}. Skipping.", file=sys.stderr)
        skipped_access_errors += 1

    for root, dirs, files in os.walk(abs_directory_path, topdown=True, onerror=walk_error_handler, followlinks=False):
        visited_roots += 1
        current_path_obj = pathlib.Path(root)

        # --- Progress Update for Directories ---
        if visited_roots % PROGRESS_UPDATE_INTERVAL_DIRS == 0 or visited_roots == 1:
            # Truncate long paths for display
            display_path = str(current_path_obj)
            if len(display_path) > 70:
                display_path = "..." + display_path[-67:]
            print(
                f"\rScanning {spinner_chars[spinner_idx % len(spinner_chars)]} [{visited_roots} dirs]: {display_path:<70}",
                end="", flush=True)
            spinner_idx += 1

        # --- Process directory entries to find directory symlinks ---
        for dir_name in dirs:
            dir_path_obj = current_path_obj / dir_name
            if dir_path_obj.is_symlink():
                final_total_dir_symlinks_found += 1
                # ... (rest of dir_symlink_info logic as before)
                dir_symlink_info = {
                    'path': dir_path_obj, 'name': dir_name, 'is_symlink': True,
                    'type': SYMLINK_TO_DIR_TYPE_STR, 'symlink_target_path': None,
                    'symlink_target_type': '.<dir>', 'size_bytes': 0
                }
                try:
                    lstat_info = dir_path_obj.lstat()
                    dir_symlink_info['size_bytes'] = lstat_info.st_size
                    target_path_str = os.readlink(dir_path_obj)
                    absolute_target_path = (dir_path_obj.parent / target_path_str).resolve()
                    dir_symlink_info['symlink_target_path'] = absolute_target_path
                    if not absolute_target_path.exists():
                        dir_symlink_info['symlink_target_type'] = ".<broken>"
                        dir_symlink_info['type'] = BROKEN_SYMLINK_TYPE_STR
                    elif not absolute_target_path.is_dir():
                        dir_symlink_info['symlink_target_type'] = ".<target_not_dir>"
                        print(f"\nWarning: Dir symlink {dir_path_obj} points to non-dir {absolute_target_path}",
                              file=sys.stderr)
                except OSError as e_link:
                    print(f"\nError reading dir symlink {dir_path_obj}: {e_link}", file=sys.stderr)
                    dir_symlink_info['type'] = SYMLINK_ERROR_TYPE_STR
                    dir_symlink_info['symlink_target_path'] = f"Error: {e_link}"
                directory_symlinks_data.append(dir_symlink_info)
                file_types_count[dir_symlink_info['type']] += 1
                file_types_size[dir_symlink_info['type']] += dir_symlink_info['size_bytes']

        # --- Process file entries ---
        for name in files:
            final_total_files_processed += 1
            total_files_processed_in_walk += 1  # For progress message interval

            file_path = current_path_obj / name
            file_info = {  # (Initialize file_info dictionary as before)
                'path': file_path, 'name': name, 'is_symlink': False,
                'symlink_target_path': None, 'symlink_target_type': None,
                'symlink_target_size_bytes': None, 'size_bytes': 0, 'type': ERROR_TYPE_STR
            }
            # ... (rest of file processing logic as before) ...
            try:
                file_info['is_hidden'] = is_hidden(file_path, os_name)
                lstat_info = file_path.lstat()

                if file_path.is_symlink():
                    file_info['is_symlink'] = True
                    file_info['size_bytes'] = lstat_info.st_size
                    file_info['type'] = SYMLINK_TYPE_STR
                    try:
                        target_path_str = os.readlink(file_path)
                        absolute_target_path = (file_path.parent / target_path_str).resolve()
                        file_info['symlink_target_path'] = absolute_target_path
                        if absolute_target_path.exists():
                            if absolute_target_path.is_file():
                                target_stat = absolute_target_path.stat()
                                file_info['symlink_target_size_bytes'] = target_stat.st_size
                                file_info[
                                    'symlink_target_type'] = absolute_target_path.suffix.lower() if absolute_target_path.suffix else NO_EXTENSION_STR
                            else:
                                file_info['symlink_target_type'] = ".<special_target>"
                        else:
                            file_info['symlink_target_type'] = ".<broken>"
                            file_info['type'] = BROKEN_SYMLINK_TYPE_STR
                    except OSError as e_link:
                        print(f"\nError reading file symlink target for {file_path}: {e_link}", file=sys.stderr)
                        file_info['type'] = SYMLINK_ERROR_TYPE_STR
                        file_info['symlink_target_path'] = f"Error: {e_link}"
                else:
                    if (lstat_info.st_mode & 0o170000) == 0o100000:
                        file_info['size_bytes'] = lstat_info.st_size
                        file_info['type'] = file_path.suffix.lower() if file_path.suffix else NO_EXTENSION_STR
                    else:
                        file_info['size_bytes'] = lstat_info.st_size
                        file_info['type'] = NON_FILE_TYPE_STR
                        print(f"\nWarning: Non-regular file '{file_path}' (mode: {oct(lstat_info.st_mode)}) found.",
                              file=sys.stderr)

                all_files_data.append(file_info)
                file_types_count[file_info['type']] += 1
                file_types_size[file_info['type']] += file_info['size_bytes']

            except OSError as e_stat:
                print(f"\nCould not fully process/stat file: {file_path}. Error: {e_stat}. Skipping.", file=sys.stderr)
                skipped_access_errors += 1
                file_info['type'] = ERROR_TYPE_STR
                all_files_data.append(file_info)  # Add with error info
                file_types_count[file_info['type']] += 1
                continue

            # --- Progress Update for Files ---
            if total_files_processed_in_walk % PROGRESS_UPDATE_INTERVAL_FILES == 0:
                # \r to return to beginning of line, end='' to not add newline
                # Using total_files_processed_in_walk for the count being shown during scan
                print(
                    f"\rScanning {spinner_chars[spinner_idx % len(spinner_chars)]} [{visited_roots} dirs, {total_files_processed_in_walk} files processed]...",
                    end="", flush=True)
                spinner_idx += 1

    # --- Finalize Progress Display ---
    # Clear the progress line and print a completion message for the scan itself
    print("\r" + " " * 100 + "\r", end="")  # Clear the line
    print(
        f"Directory scan complete. Processed {visited_roots} directories and {final_total_files_processed} file entries.")

    summary_data = {
        "target_directory": str(abs_directory_path),  # Use absolute path
        "total_directories_scanned": visited_roots,
        "total_file_entries_processed": final_total_files_processed,
        "total_directory_symlinks_found": final_total_dir_symlinks_found,
        "skipped_access_errors": skipped_access_errors,
        "file_types_summary": dict(sorted(file_types_count.items(), key=lambda item: item[1], reverse=True)),
        "file_types_size_summary": dict(file_types_size)
    }

    return all_files_data, directory_symlinks_data, summary_data
