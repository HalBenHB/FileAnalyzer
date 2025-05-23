# file_analyzer.py
import os
import pathlib
import datetime
import json

from os_utils import detect_os
from fs_utils import get_target_directory
from directory_analyzer import (
    analyze_directory,
    SYMLINK_TYPE_STR,
    BROKEN_SYMLINK_TYPE_STR,
    SYMLINK_TO_DIR_TYPE_STR,
    SYMLINK_ERROR_TYPE_STR
)

# Configuration for report
INCLUDE_DETAILED_SYMLINK_LIST = True  # Set to False to omit detailed list


def generate_report_filename():
    now = datetime.datetime.now()
    return f"file_analysis_report_{now.strftime('%Y-%m-%d_%H-%M-%S')}.txt"


def write_summary_report(report_filepath, summary_data, all_files_data, dir_symlinks_data, os_name, include_details):
    """Writes the analysis summary and symlink details to a text file."""
    with open(report_filepath, 'w', encoding='utf-8') as f:
        f.write("--- File System Analysis Report ---\n")
        f.write(f"Operating System: {os_name}\n")
        f.write(f"Analyzed Directory: {summary_data['target_directory']}\n")
        f.write(f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        f.write("\n--- Overall Summary ---\n")
        f.write(f"Total Directories Scanned (walked into): {summary_data['total_directories_scanned']}\n")
        f.write(
            f"Total File-like Entries Processed (from os.walk 'files' list): {summary_data['total_file_entries_processed']}\n")
        f.write(
            f"Total Directory Symbolic Links Found (in os.walk 'dirs' list): {summary_data['total_directory_symlinks_found']}\n")
        if summary_data['skipped_access_errors'] > 0:
            f.write(f"Skipped items due to access/read errors: {summary_data['skipped_access_errors']}\n")

        f.write("\n--- File & Entry Types Summary (Count & Size of Type Entry) ---\n")
        if summary_data['file_types_summary']:
            f.write(f"{'Extension/Type':<30} {'Count':>10} {'Total Size (Bytes)':>20}\n")
            f.write("-" * 65 + "\n")
            for ext_type, count in summary_data['file_types_summary'].items():
                size = summary_data['file_types_size_summary'].get(ext_type, 0)
                f.write(f"{ext_type:<30} {count:>10} {size:>20}\n")
        else:
            f.write("No files or entries found or accessible to analyze.\n")

        # --- Symbolic Link Summary Table ---
        f.write("\n--- Symbolic Link Type Summary ---\n")
        symlink_types_for_summary = [
            SYMLINK_TYPE_STR,  # Symlinks to files
            SYMLINK_TO_DIR_TYPE_STR,  # Symlinks to directories
            BROKEN_SYMLINK_TYPE_STR,  # Broken symlinks (could be to file or dir)
            SYMLINK_ERROR_TYPE_STR  # Errors processing symlinks
        ]

        # Check if there are any symlink types present in the summary
        has_symlink_summary_data = any(
            stype in summary_data['file_types_summary'] for stype in symlink_types_for_summary)

        if has_symlink_summary_data:
            f.write(f"{'Symlink Category':<30} {'Count':>10} {'Total Own Size (Bytes)':>25}\n")
            f.write("-" * 70 + "\n")
            total_symlinks_in_summary = 0
            total_symlink_own_size_in_summary = 0
            for sl_type in symlink_types_for_summary:
                count = summary_data['file_types_summary'].get(sl_type, 0)
                if count > 0:  # Only print if there are symlinks of this type
                    own_size = summary_data['file_types_size_summary'].get(sl_type, 0)
                    # Make category names more readable
                    readable_name = sl_type.replace(".<", "").replace(">", "")
                    if sl_type == SYMLINK_TYPE_STR:
                        readable_name = "Symlinks to Files"
                    elif sl_type == SYMLINK_TO_DIR_TYPE_STR:
                        readable_name = "Symlinks to Directories"
                    elif sl_type == BROKEN_SYMLINK_TYPE_STR:
                        readable_name = "Broken Symlinks"
                    elif sl_type == SYMLINK_ERROR_TYPE_STR:
                        readable_name = "Symlinks with Errors"

                    f.write(f"{readable_name:<30} {count:>10} {own_size:>25}\n")
                    total_symlinks_in_summary += count
                    total_symlink_own_size_in_summary += own_size
            f.write("-" * 70 + "\n")
            f.write(f"{'Total Symlinks':<30} {total_symlinks_in_summary:>10} {total_symlink_own_size_in_summary:>25}\n")
        else:
            f.write("No symbolic links found to summarize.\n")

        # --- Optional Detailed Symbolic Link List ---
        if include_details:
            all_symlinks_detailed = [sl_info for sl_info in all_files_data if sl_info['is_symlink']] + dir_symlinks_data
            f.write("\n--- Symbolic Link Details (Detailed List) ---\n")
            if all_symlinks_detailed:
                f.write(f"Found {len(all_symlinks_detailed)} symbolic links (file and directory targets):\n")
                for sl in sorted(all_symlinks_detailed, key=lambda x: x['path']):
                    f.write(f"  Link: {sl['path']}\n")
                    f.write(f"    Type: {sl['type']}\n")
                    f.write(f"    Own Size (bytes): {sl['size_bytes']}\n")
                    f.write(f"    Target Path: {sl['symlink_target_path']}\n")
                    if sl.get('symlink_target_type'):
                        f.write(f"    Target Type: {sl['symlink_target_type']}\n")
                    if sl.get('symlink_target_size_bytes') is not None:
                        f.write(f"    Target Size (bytes): {sl['symlink_target_size_bytes']}\n")
                    f.write("-" * 20 + "\n")
            else:
                f.write("No symbolic links found for detailed listing.\n")
        else:
            f.write("\n--- Symbolic Link Details (Detailed List Omitted by Configuration) ---\n")

        f.write("\n--- End of Report ---\n")
    print(f"\nAnalysis report saved to: {report_filepath}")


def main():
    """Main function to run the file analysis."""
    current_os = detect_os()
    print(f"Running on: {current_os}")

    if current_os == "Unknown":
        print("Unsupported operating system. Exiting.")
        return

    print("Project 12: File Analysis - CS350")
    target_dir = get_target_directory(current_os)

    if target_dir:
        try:
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

            report_file = generate_report_filename()
            write_summary_report(
                report_file,
                summary_stats,
                all_file_details,
                dir_symlink_details,
                current_os,
                INCLUDE_DETAILED_SYMLINK_LIST  # Pass the configuration flag
            )

            if all_file_details or dir_symlink_details:
                # This count is useful for knowing what's available for Pandas/plotting later
                combined_entries = len(all_file_details) + len(dir_symlink_details)
                print(f"\nCollected details for {combined_entries} total entries (files, file symlinks, dir symlinks).")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No valid directory selected or user chose to exit. Exiting program.")


if __name__ == "__main__":
    main()