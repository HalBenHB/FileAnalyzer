# directory_analyzer.py
import os
import pathlib
import collections
import sys
from fs_utils import is_hidden  # Import from our new module

# Define constants for special types to avoid magic strings
SYMLINK_TYPE_STR = ".<symlink>"
BROKEN_SYMLINK_TYPE_STR = ".<broken_symlink>"
SYMLINK_TO_DIR_TYPE_STR = ".<symlink_to_dir>"  # Specifically for symlinks that ARE directories
SYMLINK_ERROR_TYPE_STR = ".<symlink_error>"
NON_FILE_TYPE_STR = ".<non_file_type>"
ERROR_TYPE_STR = ".<error_processing>"
NO_EXTENSION_STR = ".<no_ext>"


# We'll add a new list to store directory symlink info
# This will be separate from all_files_data which is for items os.walk considers "files"

def analyze_directory(directory_path, os_name):
    """
    Traverses the given directory, collects file information,
    treating symlinks as distinct items with their own sizes.
    Also identifies directory symbolic links.
    """
    print(f"\nStarting analysis of: {directory_path}\n")

    all_files_data = []  # For "file" entries from os.walk
    directory_symlinks_data = []  # For symlinks that are directories

    total_files_processed = 0
    total_dir_symlinks_found = 0  # New counter
    skipped_access_errors = 0
    visited_roots = 0

    file_types_count = collections.defaultdict(int)
    file_types_size = collections.defaultdict(int)

    def walk_error_handler(os_error):
        nonlocal skipped_access_errors
        print(f"Access denied or error reading directory: {os_error.filename}. Skipping.", file=sys.stderr)
        skipped_access_errors += 1

    # If you want os.walk to traverse INTO directory symlinks, set followlinks=True
    # For now, we keep it False to analyze the link itself, not its target's contents in this function.
    # If followlinks=True, a symlink to a dir would make os.walk treat the target dir as a normal dir.
    for root, dirs, files in os.walk(directory_path, topdown=True, onerror=walk_error_handler, followlinks=False):
        visited_roots += 1
        current_path_obj = pathlib.Path(root)

        # --- Process directory entries to find directory symlinks ---
        # We need to make a copy of dirs if we modify it (e.g. for pruning traversal with topdown=True)
        # For now, just iterating is fine.
        for dir_name in dirs:
            dir_path_obj = current_path_obj / dir_name
            if dir_path_obj.is_symlink():  # Check if this "directory" entry is actually a symlink
                total_dir_symlinks_found += 1
                dir_symlink_info = {
                    'path': dir_path_obj,
                    'name': dir_name,
                    'is_symlink': True,  # It is, and it points to a directory (or should)
                    'type': SYMLINK_TO_DIR_TYPE_STR,  # Special type for dir symlinks
                    'symlink_target_path': None,
                    'symlink_target_type': '.<dir>',  # Assumed target type
                    'size_bytes': 0  # For its own size
                }
                try:
                    lstat_info = dir_path_obj.lstat()
                    dir_symlink_info['size_bytes'] = lstat_info.st_size  # Symlink's own size

                    target_path_str = os.readlink(dir_path_obj)
                    absolute_target_path = (dir_path_obj.parent / target_path_str).resolve()
                    dir_symlink_info['symlink_target_path'] = absolute_target_path

                    if not absolute_target_path.exists():
                        dir_symlink_info['symlink_target_type'] = ".<broken>"
                        dir_symlink_info['type'] = BROKEN_SYMLINK_TYPE_STR  # More specific if broken
                    elif not absolute_target_path.is_dir():
                        # This would be odd: a symlink listed in 'dirs' but target isn't a dir
                        dir_symlink_info['symlink_target_type'] = ".<target_not_dir>"
                        print(
                            f"Warning: Directory symlink {dir_path_obj} points to a non-directory target {absolute_target_path}",
                            file=sys.stderr)

                except OSError as e_link:
                    print(f"Error reading directory symlink {dir_path_obj}: {e_link}", file=sys.stderr)
                    dir_symlink_info['type'] = SYMLINK_ERROR_TYPE_STR
                    dir_symlink_info['symlink_target_path'] = f"Error: {e_link}"

                directory_symlinks_data.append(dir_symlink_info)
                # Also add to general file_types_count for overall stats
                file_types_count[dir_symlink_info['type']] += 1
                file_types_size[dir_symlink_info['type']] += dir_symlink_info['size_bytes']

        # --- Process file entries (as before) ---
        for name in files:
            total_files_processed += 1
            file_path = current_path_obj / name
            # (Initialize file_info dictionary as before)
            file_info = {
                'path': file_path, 'name': name, 'is_symlink': False,
                'symlink_target_path': None, 'symlink_target_type': None,
                'symlink_target_size_bytes': None, 'size_bytes': 0, 'type': ERROR_TYPE_STR
            }

            try:
                file_info['is_hidden'] = is_hidden(file_path, os_name)
                lstat_info = file_path.lstat()

                if file_path.is_symlink():  # This will be symlinks to FILES
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
                            # elif absolute_target_path.is_dir():
                            # This case should ideally not happen if os.walk lists symlinks to dirs in `dirs`
                            # and symlinks to files in `files`. If it does, handle it.
                            # file_info['symlink_target_type'] = ".<dir>"
                            # file_info['type'] = SYMLINK_TO_DIR_TYPE_STR # Mark as such, but it came from 'files' list
                            # print(f"Warning: File symlink {file_path} points to a directory {absolute_target_path}", file=sys.stderr)
                            else:
                                file_info['symlink_target_type'] = ".<special_target>"
                        else:
                            file_info['symlink_target_type'] = ".<broken>"
                            file_info['type'] = BROKEN_SYMLINK_TYPE_STR

                    except OSError as e_link:
                        print(f"Error reading file symlink target for {file_path}: {e_link}", file=sys.stderr)
                        file_info['type'] = SYMLINK_ERROR_TYPE_STR
                        file_info['symlink_target_path'] = f"Error: {e_link}"

                else:  # Not a symlink, presumed regular file from 'files' list
                    # Check if it's a regular file using S_ISREG from stat mode
                    # 0o100000 is S_IFREG (regular file bitmask)
                    # 0o040000 is S_IFDIR (directory)
                    # 0o120000 is S_IFLNK (symbolic link)
                    if (lstat_info.st_mode & 0o170000) == 0o100000:  # S_ISREG from POSIX stat.h
                        file_info['size_bytes'] = lstat_info.st_size
                        file_info['type'] = file_path.suffix.lower() if file_path.suffix else NO_EXTENSION_STR
                    else:
                        file_info['size_bytes'] = lstat_info.st_size
                        file_info['type'] = NON_FILE_TYPE_STR
                        print(
                            f"Warning: Non-regular file '{file_path}' (mode: {oct(lstat_info.st_mode)}) found in 'files' list.",
                            file=sys.stderr)

                all_files_data.append(file_info)
                file_types_count[file_info['type']] += 1
                file_types_size[file_info['type']] += file_info['size_bytes']

            except OSError as e_stat:
                print(f"Could not fully process/stat file: {file_path}. Error: {e_stat}. Skipping.", file=sys.stderr)
                skipped_access_errors += 1
                file_info['type'] = ERROR_TYPE_STR
                all_files_data.append(file_info)
                file_types_count[file_info['type']] += 1
                continue

    total_directories_scanned = visited_roots

    summary_data = {
        "target_directory": str(directory_path),
        "total_directories_scanned": total_directories_scanned,
        "total_file_entries_processed": total_files_processed,  # Symlinks to files, regular files
        "total_directory_symlinks_found": total_dir_symlinks_found,  # New summary item
        "skipped_access_errors": skipped_access_errors,
        "file_types_summary": dict(sorted(file_types_count.items(), key=lambda item: item[1], reverse=True)),
        "file_types_size_summary": dict(file_types_size)
    }

    # Return both lists of data
    return all_files_data, directory_symlinks_data, summary_data