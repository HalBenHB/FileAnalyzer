# file_analyzer.py
import os
import pathlib
import datetime
import json

from os_utils import detect_os
from fs_utils import get_target_directory
from directory_analyzer import analyze_directory, SYMLINK_TO_DIR_TYPE_STR  # import the constant if needed


def generate_report_filename():
    # ... (same as before) ...
    now = datetime.datetime.now()
    return f"file_analysis_report_{now.strftime('%Y-%m-%d_%H-%M-%S')}.txt"


def write_summary_report(report_filepath, summary_data, all_files_data, dir_symlinks_data, os_name):
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
            f"Total Directory Symbolic Links Found (in os.walk 'dirs' list): {summary_data['total_directory_symlinks_found']}\n")  # New line
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

        # Combine file symlinks and directory symlinks for the report section
        all_symlinks = [sl_info for sl_info in all_files_data if sl_info['is_symlink']] + dir_symlinks_data

        f.write("\n--- Symbolic Link Details ---\n")
        if all_symlinks:
            f.write(f"Found {len(all_symlinks)} symbolic links (file and directory targets):\n")
            for sl in sorted(all_symlinks, key=lambda x: x['path']):  # Sort by path for consistent output
                f.write(f"  Link: {sl['path']}\n")
                f.write(f"    Type: {sl['type']}\n")
                f.write(f"    Own Size (bytes): {sl['size_bytes']}\n")
                f.write(f"    Target Path: {sl['symlink_target_path']}\n")
                if sl.get(
                        'symlink_target_type'):  # Use .get() as not all symlink dicts might have all target fields initially
                    f.write(f"    Target Type: {sl['symlink_target_type']}\n")
                if sl.get('symlink_target_size_bytes') is not None:  # For file symlinks
                    f.write(f"    Target Size (bytes): {sl['symlink_target_size_bytes']}\n")
                f.write("-" * 20 + "\n")
        else:
            f.write("No symbolic links found.\n")

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
            # Note the change in return values from analyze_directory
            all_file_details, dir_symlink_details, summary_stats = analyze_directory(target_dir, current_os)

            print("\n--- Analysis Summary (Console) ---")
            print(f"Target Directory: {summary_stats['target_directory']}")
            print(f"Total Directories Scanned (walked into): {summary_stats['total_directories_scanned']}")
            print(f"Total File-like Entries Processed: {summary_stats['total_file_entries_processed']}")
            print(
                f"Total Directory Symbolic Links Found: {summary_stats['total_directory_symlinks_found']}")  # New line
            if summary_stats['skipped_access_errors'] > 0:
                print(f"Skipped items due to access/read errors: {summary_stats['skipped_access_errors']}")

            print("\n--- File & Entry Types Summary (Console) ---")
            if summary_stats['file_types_summary']:
                print(f"{'Extension/Type':<30} {'Count':>10} {'Total Size (Bytes)':>20}")
                print("-" * 65)
                for ext_type, count in summary_stats['file_types_summary'].items():
                    size = summary_stats['file_types_size_summary'].get(ext_type, 0)
                    print(f"{ext_type:<30} {count:>10} {size:>20}")
            else:
                print("No files or entries found or accessible to analyze.")

            report_file = generate_report_filename()
            write_summary_report(report_file, summary_stats, all_file_details, dir_symlink_details, current_os)

            if all_file_details or dir_symlink_details:
                print(
                    f"\nCollected details for {len(all_file_details)} file-like entries and {len(dir_symlink_details)} directory symlinks.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No valid directory selected or user chose to exit. Exiting program.")


if __name__ == "__main__":
    main()