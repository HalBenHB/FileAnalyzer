# file_analyzer.py
import os
from os_utils import detect_os
from fs_utils import get_target_directory
from directory_analyzer import analyze_directory
from report_generator import generate_report_filename, write_summary_report
import config
from plot_generator import generate_plots

def main():
    """Main function to run the file analysis."""
    print("\nProject: File Analysis - CS350")
    print("\nBy: Halil Nebioğlu - Murat Yiğit Mert")

    current_os = detect_os()
    print(f"Running on: {current_os}")

    if current_os == "Unknown":
        print("Unsupported operating system. Exiting.")
        return

    target_dir = get_target_directory(current_os)
    if target_dir:
        try:
            # analyze_directory now prints its own start/end messages for the scan
            all_file_details, dir_symlink_details, summary_stats = analyze_directory(target_dir, current_os)

            # --- Console Summary (can be kept brief or match file report structure) ---
            print("\n--- Analysis Summary (Console) ---")
            print(f"Target Directory: {summary_stats['target_directory']}")
            print(
                f"Total Dirs Scanned: {summary_stats['total_directories_scanned']}, File Entries: {summary_stats['total_file_entries_processed']}, Dir Symlinks: {summary_stats['total_directory_symlinks_found']}")
            if summary_stats['skipped_access_errors'] > 0:
                print(f"Skipped items due to errors: {summary_stats['skipped_access_errors']}")

            print("\n--- File & Entry Types Summary (Console) ---")
            if summary_stats['file_types_summary']:
                print(f"{'Extension/Type':<30} {'Count':>10} {'Total Size (Bytes)':>20}")
                print("-" * 65)
                # Limit console output for brevity if desired, or print all
                for ext_type, count in list(summary_stats['file_types_summary'].items())[:15]:  # Example: top 15
                    size = summary_stats['file_types_size_summary'].get(ext_type, 0)
                    print(f"{ext_type:<30} {count:>10} {size:>20}")
                if len(summary_stats['file_types_summary']) > 15:
                    print("... and more ...")
            else:
                print("No files or entries found or accessible to analyze.")
            # --- End Console Summary ---

            if all_file_details or dir_symlink_details:
                combined_entries = len(all_file_details) + len(dir_symlink_details)
                print(f"\nCollected details for {combined_entries} total entries (files, file symlinks, dir symlinks).")


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
            print(f"An unexpected error occurred during analysis or reporting: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No valid directory selected or user chose to exit. Exiting program.")


if __name__ == "__main__":
    main()