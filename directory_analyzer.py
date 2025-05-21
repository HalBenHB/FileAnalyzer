# directory_analyzer.py
import os
import pathlib
import collections
import sys
from fs_utils import is_hidden  # Import from our new module

# Define constants for special types to avoid magic strings
SYMLINK_TYPE_STR = ".<symlink>"
BROKEN_SYMLINK_TYPE_STR = ".<broken_symlink>"
SYMLINK_TO_DIR_TYPE_STR = ".<symlink_to_dir>"
SYMLINK_ERROR_TYPE_STR = ".<symlink_error>"
NON_FILE_TYPE_STR = ".<non_file_type>"  # For items in 'files' list that aren't regular files or handled symlinks
ERROR_TYPE_STR = ".<error_processing>"
NO_EXTENSION_STR = ".<no_ext>"


def analyze_directory(directory_path, os_name):
    """
    Traverses the given directory, collects file information,
    treating symlinks as distinct items with their own sizes.
    """
    print(f"\nStarting analysis of: {directory_path}\n")

    all_files_data = []
    total_files_processed = 0
    skipped_access_errors = 0
    visited_roots = 0

    file_types_count = collections.defaultdict(int)
    file_types_size = collections.defaultdict(int)  # Stores sum of symlink_own_size for symlinks

    def walk_error_handler(os_error):
        nonlocal skipped_access_errors
        print(f"Access denied or error reading directory: {os_error.filename}. Skipping.", file=sys.stderr)
        skipped_access_errors += 1

    for root, dirs, files in os.walk(directory_path, topdown=True, onerror=walk_error_handler):
        visited_roots += 1
        current_path_obj = pathlib.Path(root)

        for name in files:
            total_files_processed += 1
            file_path = current_path_obj / name
            file_info = {
                'path': file_path,
                'name': name,
                'is_symlink': False,
                'symlink_target_path': None,
                'symlink_target_type': None,  # e.g. '.txt', '.<dir>', '.<broken>'
                'symlink_target_size_bytes': None,
                'size_bytes': 0,  # Default, will be symlink's own size or file's size
                'type': ERROR_TYPE_STR  # Default
            }

            try:
                file_info['is_hidden'] = is_hidden(file_path, os_name)

                # Use lstat to get info about the file/symlink itself without following
                lstat_info = file_path.lstat()  # This works for both regular files and symlinks

                if file_path.is_symlink():
                    file_info['is_symlink'] = True
                    file_info['size_bytes'] = lstat_info.st_size  # Symlink's own size
                    file_info['type'] = SYMLINK_TYPE_STR  # Default type for symlink

                    try:
                        target_path_str = os.readlink(file_path)
                        # Resolve target path relative to the symlink's parent directory
                        absolute_target_path = (file_path.parent / target_path_str).resolve()
                        file_info['symlink_target_path'] = absolute_target_path

                        if absolute_target_path.exists():
                            if absolute_target_path.is_file():
                                target_stat = absolute_target_path.stat()
                                file_info['symlink_target_size_bytes'] = target_stat.st_size
                                file_info[
                                    'symlink_target_type'] = absolute_target_path.suffix.lower() if absolute_target_path.suffix else NO_EXTENSION_STR
                            elif absolute_target_path.is_dir():
                                file_info['symlink_target_type'] = ".<dir>"
                                # For symlinks to directories, we might change the primary 'type'
                                file_info['type'] = SYMLINK_TO_DIR_TYPE_STR
                            else:  # Target exists but is not a file or dir (e.g. special file)
                                file_info['symlink_target_type'] = ".<special_target>"
                        else:  # Broken symlink
                            file_info['symlink_target_type'] = ".<broken>"
                            file_info['type'] = BROKEN_SYMLINK_TYPE_STR

                    except OSError as e_link:
                        print(f"Error reading symlink target for {file_path}: {e_link}", file=sys.stderr)
                        file_info['type'] = SYMLINK_ERROR_TYPE_STR
                        file_info['symlink_target_path'] = f"Error: {e_link}"

                else:  # Not a symlink, must be a regular file (os.walk `files` list)
                    if lstat_info.st_mode & 0o170000 == 0o100000:  # S_ISREG - check if it's a regular file
                        file_info['size_bytes'] = lstat_info.st_size
                        file_info['type'] = file_path.suffix.lower() if file_path.suffix else NO_EXTENSION_STR
                    else:  # Not a regular file (e.g. named pipe, socket, device file if any appear)
                        # This case should be rare with os.walk on 'files' list.
                        file_info['size_bytes'] = lstat_info.st_size  # Still has a size
                        file_info['type'] = NON_FILE_TYPE_STR
                        print(
                            f"Warning: Non-regular file '{file_path}' found in 'files' list. Type: {oct(lstat_info.st_mode)}",
                            file=sys.stderr)

                all_files_data.append(file_info)
                file_types_count[file_info['type']] += 1
                file_types_size[file_info['type']] += file_info['size_bytes']

            except OSError as e_stat:
                print(f"Could not fully process/stat file: {file_path}. Error: {e_stat}. Skipping.", file=sys.stderr)
                skipped_access_errors += 1
                # Add partial info with error type
                file_info['type'] = ERROR_TYPE_STR
                all_files_data.append(file_info)
                file_types_count[file_info['type']] += 1
                # file_types_size will use the default size_bytes=0 for this error case
                continue

    total_directories_scanned = visited_roots

    summary_data = {
        "target_directory": str(directory_path),
        "total_directories_scanned": total_directories_scanned,
        "total_files_processed": total_files_processed,
        "skipped_access_errors": skipped_access_errors,
        "file_types_summary": dict(sorted(file_types_count.items(), key=lambda item: item[1], reverse=True)),
        "file_types_size_summary": dict(file_types_size)  # Convert defaultdict to dict for easier saving
    }

    return all_files_data, summary_data