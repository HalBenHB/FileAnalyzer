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
    print(f"\nStarting analysis of: {directory_path}\n")
    abs_directory_path = pathlib.Path(directory_path).resolve() # Resolve the starting dir once
    print(f"Analyzing: {abs_directory_path}")

    all_files_data = []
    directory_symlinks_data = []
    final_total_files_processed = 0
    final_total_dir_symlinks_found = 0
    skipped_access_errors = 0
    visited_roots = 0
    file_types_count = collections.defaultdict(int)
    file_types_size = collections.defaultdict(int)
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

        if visited_roots % PROGRESS_UPDATE_INTERVAL_DIRS == 0 or visited_roots == 1 :
            # Truncate long paths for display
            display_path = str(current_path_obj)
            if len(display_path) > 70:
                display_path = "..." + display_path[-67:]
            print(f"\rScanning {spinner_chars[spinner_idx % len(spinner_chars)]} [{visited_roots} dirs]: {display_path:<70}", end="", flush=True)
            spinner_idx += 1

        # --- Process directory entries to find directory symlinks ---
        for dir_name in dirs:
            dir_path_obj = current_path_obj / dir_name
            if dir_path_obj.is_symlink():
                final_total_dir_symlinks_found += 1
                dir_symlink_info = {
                    'path': dir_path_obj, 'name': dir_name, 'is_symlink': True,
                    'type': SYMLINK_TO_DIR_TYPE_STR, 'symlink_target_path': None,
                    'symlink_target_type': '.<dir>', 'size_bytes': 0
                }
                try:
                    lstat_info = dir_path_obj.lstat()
                    dir_symlink_info['size_bytes'] = lstat_info.st_size
                    target_path_str = os.readlink(dir_path_obj)

                    # Use the new helper function to get absolute path without full resolve
                    # This should prevent symlink loop errors from .resolve()
                    immediate_absolute_target = get_absolute_target_path(dir_path_obj, target_path_str)
                    dir_symlink_info['symlink_target_path'] = immediate_absolute_target

                    # Now check existence and type of this immediate_absolute_target
                    if not immediate_absolute_target.exists(): # This .exists() might still follow one level of symlink if target is a symlink
                        dir_symlink_info['symlink_target_type'] = ".<broken>"
                        dir_symlink_info['type'] = BROKEN_SYMLINK_TYPE_STR
                    elif not immediate_absolute_target.is_dir(): # .is_dir() also follows one level if needed
                        dir_symlink_info['symlink_target_type'] = ".<target_not_dir>"
                        dir_symlink_info['type'] = SYMLINK_TYPE_STR # It's a symlink, but points to a non-dir
                        print(f"\nWarning: Dir symlink {dir_path_obj} points to non-dir {immediate_absolute_target}", file=sys.stderr)
                    # If it exists and is a dir, symlink_target_type remains '.<dir>' (default)

                except RuntimeError as e_runtime: # Catch potential symlink loops from exists() or is_dir() if they go too deep
                    print(f"\nRuntimeError (likely symlink loop) processing dir symlink target {dir_path_obj}: {e_runtime}", file=sys.stderr)
                    dir_symlink_info['type'] = SYMLINK_ERROR_TYPE_STR
                    dir_symlink_info['symlink_target_path'] = f"Error: {e_runtime}"

                except OSError as e_link:
                    print(f"\nOSError processing dir symlink {dir_path_obj}: {e_link}", file=sys.stderr)
                    dir_symlink_info['type'] = SYMLINK_ERROR_TYPE_STR
                    dir_symlink_info['symlink_target_path'] = f"Error: {e_link}"

                directory_symlinks_data.append(dir_symlink_info)
                file_types_count[dir_symlink_info['type']] += 1
                file_types_size[dir_symlink_info['type']] += dir_symlink_info['size_bytes']

        # --- Process file entries ---
        for name in files:
            final_total_files_processed += 1
            total_files_processed_in_walk +=1
            file_path = current_path_obj / name
            file_info = {
                'path': file_path, 'name': name, 'is_symlink': False,
                'symlink_target_path': None, 'symlink_target_type': None,
                'symlink_target_size_bytes': None, 'size_bytes': 0, 'type': ERROR_TYPE_STR
            }
            try:
                file_info['is_hidden'] = is_hidden(file_path, os_name)
                lstat_info = file_path.lstat()

                if file_path.is_symlink():
                    file_info['is_symlink'] = True
                    file_info['size_bytes'] = lstat_info.st_size
                    file_info['type'] = SYMLINK_TYPE_STR
                    try:
                        target_path_str = os.readlink(file_path)

                        # Use the new helper function
                        immediate_absolute_target = get_absolute_target_path(file_path, target_path_str)
                        file_info['symlink_target_path'] = immediate_absolute_target

                        # Check existence and type of immediate_absolute_target
                        # .exists() and .is_file() follow one layer of symlinks if the target is a symlink.
                        # This is generally OK. The problem was .resolve() following *all* layers.
                        if immediate_absolute_target.exists(): # Explicitly allow one level for target check
                            # Note: Path.exists() has follow_symlinks=True by default.
                            # Path.is_file() also has follow_symlinks=True by default.
                            if immediate_absolute_target.is_file(): # This will follow if immediate_absolute_target is itself a symlink
                                target_stat = immediate_absolute_target.stat() # stat() follows by default
                                file_info['symlink_target_size_bytes'] = target_stat.st_size
                                file_info['symlink_target_type'] = immediate_absolute_target.suffix.lower() if immediate_absolute_target.suffix else NO_EXTENSION_STR
                            else: # Target exists but is not a file (e.g., a dir, or another symlink to a dir)
                                file_info['symlink_target_type'] = ".<target_not_file>"
                                if immediate_absolute_target.is_dir():
                                     file_info['type'] = SYMLINK_TO_DIR_TYPE_STR # A file symlink points to a dir
                                else:
                                     file_info['type'] = ".<symlink_to_special>"


                        else: # Target does not exist
                            file_info['symlink_target_type'] = ".<broken>"
                            file_info['type'] = BROKEN_SYMLINK_TYPE_STR

                    except RuntimeError as e_runtime: # Catch potential symlink loops from target's exists() or is_file()
                        print(f"\nRuntimeError (likely symlink loop) processing file symlink target {file_path}: {e_runtime}", file=sys.stderr)
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
                    else:
                        file_info['size_bytes'] = lstat_info.st_size
                        file_info['type'] = NON_FILE_TYPE_STR
                        print(f"\nWarning: Non-regular file '{file_path}' (mode: {oct(lstat_info.st_mode)}) found.", file=sys.stderr)

                all_files_data.append(file_info)
                file_types_count[file_info['type']] += 1
                file_types_size[file_info['type']] += file_info['size_bytes']

            except OSError as e_stat:
                print(f"\nOSError during main processing of {file_path}: {e_stat}. Skipping.", file=sys.stderr)
                skipped_access_errors += 1
                file_info['type'] = ERROR_TYPE_STR
                all_files_data.append(file_info)
                file_types_count[file_info['type']] +=1
                continue

            if total_files_processed_in_walk % PROGRESS_UPDATE_INTERVAL_FILES == 0:
                print(f"\rScanning {spinner_chars[spinner_idx % len(spinner_chars)]} [{visited_roots} dirs, {total_files_processed_in_walk} files processed]...", end="", flush=True)
                spinner_idx +=1

    print("\r" + " " * 100 + "\r", end="")
    print(f"Directory scan complete. Processed {visited_roots} directories and {final_total_files_processed} file entries.")

    summary_data = { # ... (same as before) ...
        "target_directory": str(abs_directory_path),
        "total_directories_scanned": visited_roots,
        "total_file_entries_processed": final_total_files_processed,
        "total_directory_symlinks_found": final_total_dir_symlinks_found,
        "skipped_access_errors": skipped_access_errors,
        "file_types_summary": dict(sorted(file_types_count.items(), key=lambda item: item[1], reverse=True)),
        "file_types_size_summary": dict(file_types_size)
    }

    return all_files_data, directory_symlinks_data, summary_data
