# directory_analyzer.py
import os
import pathlib
import collections
import sys
from fs_utils import is_hidden
import config

# Define constants for special types to avoid magic strings
SYMLINK_TYPE_STR = ".<symlink>"
BROKEN_SYMLINK_TYPE_STR = ".<broken_symlink>"
SYMLINK_TO_DIR_TYPE_STR = ".<symlink_to_dir>"  # Specifically for symlinks that ARE directories
SYMLINK_ERROR_TYPE_STR = ".<symlink_error>"
NON_FILE_TYPE_STR = ".<non_file_type>"
ERROR_TYPE_STR = ".<error_processing>"
NO_EXTENSION_STR = ".<no_ext>"


def get_absolute_target_path(symlink_path_obj, target_path_str_from_readlink):
    """
    Constructs an absolute path to the immediate target of a symlink.
    Does not fully resolve symlink chains in the target itself, avoiding loops.
    """
    # target_path_str_from_readlink can be absolute or relative
    target_as_path = pathlib.Path(target_path_str_from_readlink)
    if target_as_path.is_absolute():
        # If os.readlink already gave an absolute path, use it directly.
        # .absolute() on an already absolute path is a no-op.
        return target_as_path.absolute()
    else:
        # If relative, join with the symlink's parent directory and then make absolute.
        # (symlink_path_obj.parent / target_as_path) creates the combined path.
        # .absolute() then resolves '..' and '.' and prepends CWD if necessary
        # to make it absolute, but doesn't follow symlinks within the constructed path.
        return (symlink_path_obj.parent / target_as_path).absolute()


def analyze_directory(directory_path, os_name):
    """
    Traverses the given directory, collects file information,
    treating symlinks as distinct items with their own sizes.
    Also identifies directory symbolic links and shows progress.
    """
    print(f"Starting analysis of: {directory_path}")
    abs_directory_path = pathlib.Path(directory_path).resolve()
    print(f"Analyzing: {abs_directory_path}")

    all_files_data = []
    directory_symlinks_data = []

    # Counters for overall summary
    final_total_files_processed = 0
    final_total_dir_symlinks_found = 0
    skipped_access_errors = 0
    visited_roots = 0

    # General file type aggregation
    file_types_count = collections.defaultdict(int)
    file_types_size = collections.defaultdict(int)

    # --- Statistics for hidden files ---
    total_hidden_files_count = 0
    total_hidden_files_size = 0
    hidden_file_types_count = collections.defaultdict(int)
    hidden_file_types_size = collections.defaultdict(int)
    # --------------------------------------

    # Progress related
    spinner_chars = ['|', '/', '-', '\\']
    spinner_idx = 0
    total_files_processed_in_walk = 0

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

        if visited_roots % config.PROGRESS_UPDATE_INTERVAL_DIRS == 0 or visited_roots == 1 :
            # Truncate long paths for display
            display_path = str(current_path_obj)
            if len(display_path) > 70: display_path = "..." + display_path[-67:]
            print(f"\rScanning {spinner_chars[spinner_idx % len(spinner_chars)]} [{visited_roots} dirs]: {display_path:<70}", end="", flush=True)
            spinner_idx += 1

        # --- Process directory entries to find directory symlinks ---
        processed_dirs_this_iteration = [] # To keep track of dirs successfully processed
        for dir_name in dirs:
            dir_path_obj = current_path_obj / dir_name
            try: # <------------------------------------ ADD TRY HERE
                if dir_path_obj.is_symlink():
                    final_total_dir_symlinks_found += 1
                    dir_symlink_info = {
                        'path': dir_path_obj, 'name': dir_name, 'is_symlink': True,
                        'type': SYMLINK_TO_DIR_TYPE_STR, 'symlink_target_path': None,
                        'symlink_target_type': '.<dir>', 'size_bytes': 0, 'is_hidden': False
                    }
                    # The following try-except is for issues within symlink processing
                    try:
                        dir_symlink_info['is_hidden'] = is_hidden(dir_path_obj, os_name)
                        lstat_info = dir_path_obj.lstat()
                        dir_symlink_info['size_bytes'] = lstat_info.st_size
                        target_path_str = os.readlink(dir_path_obj)

                        # Use the new helper function to get absolute path without full resolve
                        # This should prevent symlink loop errors from .resolve()

                        immediate_absolute_target = get_absolute_target_path(dir_path_obj, target_path_str)
                        dir_symlink_info['symlink_target_path'] = immediate_absolute_target

                        # Now check existence and type of this immediate_absolute_target

                        if not immediate_absolute_target.exists():
                            dir_symlink_info['symlink_target_type'] = ".<broken>"
                            dir_symlink_info['type'] = BROKEN_SYMLINK_TYPE_STR
                        elif not immediate_absolute_target.is_dir():
                            dir_symlink_info['symlink_target_type'] = ".<target_not_dir>"
                            dir_symlink_info['type'] = SYMLINK_TYPE_STR
                            print(f"\nWarning: Dir symlink {dir_path_obj} points to non-dir {immediate_absolute_target}", file=sys.stderr)
                        # If it exists and is a dir, symlink_target_type remains '.<dir>' (default)


                    except RuntimeError as e_runtime:
                        print(f"\nRuntimeError processing dir symlink target {dir_path_obj}: {e_runtime}", file=sys.stderr)
                        dir_symlink_info['type'] = SYMLINK_ERROR_TYPE_STR
                        dir_symlink_info['symlink_target_path'] = f"Error: {e_runtime}"
                    except OSError as e_link_ops: # Catch OS errors during readlink, lstat on symlink itself
                        print(f"\nOSError processing dir symlink {dir_path_obj} (target ops or link itself): {e_link_ops}", file=sys.stderr)
                        dir_symlink_info['type'] = SYMLINK_ERROR_TYPE_STR
                        dir_symlink_info['symlink_target_path'] = f"Error: {e_link_ops}"

                    directory_symlinks_data.append(dir_symlink_info)
                    file_types_count[dir_symlink_info['type']] += 1
                    file_types_size[dir_symlink_info['type']] += dir_symlink_info['size_bytes']
                    if dir_symlink_info['is_hidden']:
                        total_hidden_files_count += 1
                        total_hidden_files_size += dir_symlink_info['size_bytes']
                        hidden_file_types_count[dir_symlink_info['type']] += 1
                        hidden_file_types_size[dir_symlink_info['type']] += dir_symlink_info['size_bytes']
                # else: # Not a symlink, it's a regular directory entry from 'dirs' list.
                      # No special processing needed here for regular dirs beyond os.walk traversing them.

                processed_dirs_this_iteration.append(dir_name) # If successful

            except PermissionError as e_perm:
                print(f"\nPermission denied processing directory entry: {dir_path_obj}. Error: {e_perm}. Skipping this entry.", file=sys.stderr)
                skipped_access_errors += 1
                continue # Skip to the next dir_name in dirs
            except OSError as e_os:
                print(f"\nOSError processing directory entry: {dir_path_obj}. Error: {e_os}. Skipping this entry.", file=sys.stderr)
                skipped_access_errors += 1
                continue # Skip to the next dir_name in dirs

        # If you were modifying `dirs` in place for topdown=True traversal pruning,
        # you would do: `dirs[:] = processed_dirs_this_iteration`
        # But since we are just reading, it's not strictly necessary here.

        # Process file entries
        for name in files:
            final_total_files_processed += 1
            total_files_processed_in_walk +=1
            file_path = current_path_obj / name
            file_info = {
                'path': file_path, 'name': name, 'is_symlink': False, 'is_hidden': False,
                'symlink_target_path': None, 'symlink_target_type': None,
                'symlink_target_size_bytes': None, 'size_bytes': 0, 'type': ERROR_TYPE_STR
            }
            try:
                file_info['is_hidden'] = is_hidden(file_path, os_name)
                lstat_info = file_path.lstat()

                # Logic for symlinks to files (as before)
                if file_path.is_symlink():
                    file_info['is_symlink'] = True
                    file_info['size_bytes'] = lstat_info.st_size
                    file_info['type'] = SYMLINK_TYPE_STR
                    try:
                        target_path_str = os.readlink(file_path)

                        # Use the new helper function
                        immediate_absolute_target = get_absolute_target_path(file_path, target_path_str)
                        file_info['symlink_target_path'] = immediate_absolute_target
                        if immediate_absolute_target.exists():
                            if immediate_absolute_target.is_file():
                                target_stat = immediate_absolute_target.stat()
                                file_info['symlink_target_size_bytes'] = target_stat.st_size
                                file_info['symlink_target_type'] = immediate_absolute_target.suffix.lower() if immediate_absolute_target.suffix else NO_EXTENSION_STR
                            else:
                                file_info['symlink_target_type'] = ".<target_not_file>"
                                if immediate_absolute_target.is_dir():
                                     file_info['type'] = SYMLINK_TO_DIR_TYPE_STR
                                else:
                                     file_info['type'] = ".<symlink_to_special>"
                        else:
                            file_info['symlink_target_type'] = ".<broken>"
                            file_info['type'] = BROKEN_SYMLINK_TYPE_STR
                    except RuntimeError as e_runtime:
                        print(f"\nRuntimeError processing file symlink target {file_path}: {e_runtime}", file=sys.stderr)
                        file_info['type'] = SYMLINK_ERROR_TYPE_STR
                        file_info['symlink_target_path'] = f"Error: {e_runtime}"
                    except OSError as e_link:
                        print(f"\nOSError processing file symlink target {file_path}: {e_link}", file=sys.stderr)
                        file_info['type'] = SYMLINK_ERROR_TYPE_STR
                        file_info['symlink_target_path'] = f"Error: {e_link}"
                else: # Not a symlink
                    if (lstat_info.st_mode & 0o170000) == 0o100000:
                        file_info['size_bytes'] = lstat_info.st_size
                        file_info['type'] = file_path.suffix.lower() if file_path.suffix else NO_EXTENSION_STR
                    else: # Non-regular file type from 'files' list
                        file_info['size_bytes'] = lstat_info.st_size
                        file_info['type'] = NON_FILE_TYPE_STR
                        print(f"\nWarning: Non-regular file '{file_path}' (mode: {oct(lstat_info.st_mode)}) found.", file=sys.stderr)

                # EXTREMELY_LARGE_THRESHOLD = 10**12 # 1 TB, adjust as needed
                #
                # if file_info['size_bytes'] > EXTREMELY_LARGE_THRESHOLD:
                #     print(f"\n[DEBUG] Extremely large file detected: "
                #           f"Path: {file_info['path']}, Size: {file_info['size_bytes']} bytes, "
                #           f"Type: {file_info['type']}, IsSymlink: {file_info['is_symlink']}", file=sys.stderr)
                #     if file_info['is_symlink']:
                #         print(f"          Symlink Target: {file_info.get('symlink_target_path')}", file=sys.stderr)
                #         print(f"          Symlink Target Size: {file_info.get('symlink_target_size_bytes')}", file=sys.stderr)
                #     return None, None, None

                all_files_data.append(file_info)
                # General aggregation
                file_types_count[file_info['type']] += 1
                file_types_size[file_info['type']] += file_info['size_bytes']

                # --- Aggregate hidden file statistics ---
                # This applies to both regular files and symlinks to files (based on their own hidden status)
                if file_info['is_hidden']:
                    total_hidden_files_count += 1
                    total_hidden_files_size += file_info['size_bytes'] # Use the item's own size
                    hidden_file_types_count[file_info['type']] += 1
                    hidden_file_types_size[file_info['type']] += file_info['size_bytes']
                # ----------------------------------------

            except OSError as e_stat:
                print(f"\nOSError during main processing of {file_path}: {e_stat}. Skipping.", file=sys.stderr)
                skipped_access_errors += 1
                file_info['type'] = ERROR_TYPE_STR # Mark as error
                # Potentially set is_hidden to False or a special state if stat failed before is_hidden check
                file_info['is_hidden'] = False # Or some other default on error
                all_files_data.append(file_info)
                file_types_count[file_info['type']] +=1 # Count as error type
                continue

            # Progress update for files (as before)
            if total_files_processed_in_walk % config.PROGRESS_UPDATE_INTERVAL_FILES == 0:
                print(f"\rScanning {spinner_chars[spinner_idx % len(spinner_chars)]} [{visited_roots} dirs, {total_files_processed_in_walk} files processed]...", end="", flush=True)
                spinner_idx +=1

    print("\r" + " " * 100 + "\r", end="")
    print(f"Directory scan complete. Processed {visited_roots} directories and {final_total_files_processed} file entries.")

    summary_data = {
        "target_directory": str(abs_directory_path),
        "total_directories_scanned": visited_roots,
        "total_file_entries_processed": final_total_files_processed,
        "total_directory_symlinks_found": final_total_dir_symlinks_found,
        "skipped_access_errors": skipped_access_errors,
        "file_types_summary": dict(sorted(file_types_count.items(), key=lambda item: item[1], reverse=True)),
        "file_types_size_summary": dict(file_types_size),
        "total_hidden_files_count": total_hidden_files_count,
        "total_hidden_files_size": total_hidden_files_size,
        "hidden_file_types_summary": dict(sorted(hidden_file_types_count.items(), key=lambda item: item[1], reverse=True)),
        "hidden_file_types_size_summary": dict(hidden_file_types_size)
        # --------------------------------------------
    }

    return all_files_data, directory_symlinks_data, summary_data