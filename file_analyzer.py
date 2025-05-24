# file_analyzer.py
from os_utils import detect_os
from fs_utils import get_target_directory
from directory_analyzer import analyze_directory
from report_generator import generate_report_filename, write_summary_report
import config
from plot_generator import generate_plots
from serializer import load_scan, save_scan, scan_exists

def main():
    """Main function to run the file analysis."""
    print("\nProject: File Analysis - CS350")
    print("By: Halil Nebioğlu - Murat Yiğit Mert")

    current_os = detect_os()
    print(f"Running on: {current_os}")

    if current_os == "Unknown":
        print("Unsupported operating system. Exiting.")
        return

    target_dir_path_obj = get_target_directory(current_os)

    if target_dir_path_obj: # Check if a valid directory was selected
        target_dir_str = str(target_dir_path_obj)

        all_file_details, dir_symlink_details, summary_stats = None, None, None
        scan_loaded = False

        try:
            if config.LOAD_SAVED_SCAN and scan_exists(target_dir_path_obj):
                print(f"Attempting to load saved scan for: {target_dir_str}")
                all_file_details, dir_symlink_details, summary_stats = load_scan(target_dir_path_obj)
                if all_file_details is not None: # Check if loading was successful
                    scan_loaded = True
                    print("Successfully loaded data from saved scan.")
                else:
                    print("Failed to load saved scan. Proceeding with new scan.")

            if not scan_loaded:
                print(f"Performing new scan for: {target_dir_str}")
                all_file_details, dir_symlink_details, summary_stats = analyze_directory(target_dir_path_obj, current_os)

                # Save the new scan only if it was successful and saving is enabled
                if config.SAVE_NEW_SCAN and all_file_details is not None: # Ensure scan produced data
                    print(f"Attempting to save new scan for: {target_dir_str}")
                    save_scan(all_file_details, dir_symlink_details, summary_stats, target_dir_path_obj)

            # Ensure we have valid data to proceed with reporting and plotting
            if all_file_details is None or summary_stats is None:
                print("No scan data available (either failed to load or new scan failed). Exiting analysis for this directory.")
                return # Or raise an error

            # --- Console Summary ---
            print("\n--- Analysis Summary (Console) ---")
            print(f"Target Directory: {summary_stats.get('target_directory', 'N/A')}") # Use .get for safety
            print(
                f"Total Dirs Scanned: {summary_stats.get('total_directories_scanned', 0)}, "
                f"File Entries: {summary_stats.get('total_file_entries_processed', 0)}, "
                f"Dir Symlinks: {summary_stats.get('total_directory_symlinks_found', 0)}"
            )
            if summary_stats.get('skipped_access_errors', 0) > 0:
                print(f"Skipped items due to errors: {summary_stats['skipped_access_errors']}")

            print("\n--- File & Entry Types Summary (Console) ---")
            file_types_summary_console = summary_stats.get('file_types_summary', {})
            if file_types_summary_console:
                print(f"{'Extension/Type':<30} {'Count':>10} {'Total Size (Bytes)':>20}")
                print("-" * 65)
                # Limit console output for brevity if desired, or print all
                for ext_type, count in list(file_types_summary_console.items())[:15]:  # Example: top 15
                    size = summary_stats.get('file_types_size_summary', {}).get(ext_type, 0)
                    print(f"{ext_type:<30} {count:>10} {size:>20}")
                if len(file_types_summary_console) > 15:
                    print("... and more ...")
            else:
                print("No file types summary available for console.")


            if all_file_details or dir_symlink_details:
                combined_entries = len(all_file_details or []) + len(dir_symlink_details or [])
                print(f"\nCollected details for {combined_entries} total entries (files, file symlinks, dir symlinks).")

            # The save_scan logic was moved up to only save *new* scans.
            # If you wanted to re-save a loaded scan (e.g. if config changes how it's processed later),
            # that would be a different logic branch.


            # --- Generate Text Report ---
            report_file = generate_report_filename()
            write_summary_report(
                report_filepath=report_file,
                summary_data=summary_stats,
                all_files_data=all_file_details,
                dir_symlinks_data=dir_symlink_details,
                os_name=current_os,
                include_details=config.INCLUDE_DETAILED_SYMLINK_LIST
            )

            # --- Generate Plots ---
            generate_plots(
                all_files_data=all_file_details,
                directory_symlinks_data=dir_symlink_details,
                summary_data=summary_stats,
                os_name=current_os
            )

        except Exception as e:
            print(f"An unexpected error occurred: {e}") # Simplified error message for top level
            import traceback
            traceback.print_exc() # Still good for debugging
    else:
        print("No valid directory selected or user chose to exit. Exiting program.")


if __name__ == "__main__":
    main()