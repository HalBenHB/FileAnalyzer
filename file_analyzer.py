# file_analyzer.py
import os
import pathlib
import datetime  # For timestamped filename
import json  # For potentially saving structured data if needed, or use for report formatting

from os_utils import detect_os
from fs_utils import get_target_directory
from directory_analyzer import analyze_directory


# We will create report_generator.py later and import from it

def generate_report_filename():
    """Generates a filename with a timestamp."""
    now = datetime.datetime.now()
    return f"file_analysis_report_{now.strftime('%Y-%m-%d_%H-%M-%S')}.txt"


def write_summary_report(report_filepath, summary_data, all_files_data, os_name):
    """Writes the analysis summary and symlink details to a text file."""
    with open(report_filepath, 'w', encoding='utf-8') as f:
        f.write("--- File System Analysis Report ---\n")
        f.write(f"Operating System: {os_name}\n")
        f.write(f"Analyzed Directory: {summary_data['target_directory']}\n")
        f.write(f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n--- Overall Summary ---\n")
        f.write(f"Total Directories Scanned: {summary_data['total_directories_scanned']}\n")
        f.write(f"Total File Entries Processed: {summary_data['total_files_processed']}\n")
        if summary_data['skipped_access_errors'] > 0:
            f.write(f"Skipped items due to access/read errors: {summary_data['skipped_access_errors']}\n")

        f.write("\n--- File Types Summary (Count & Size of Type Entry) ---\n")
        if summary_data['file_types_summary']:
            f.write(f"{'Extension/Type':<30} {'Count':>10} {'Total Size (Bytes)':>20}\n")
            f.write("-" * 65 + "\n")
            for ext_type, count in summary_data['file_types_summary'].items():
                size = summary_data['file_types_size_summary'].get(ext_type, 0)
                f.write(f"{ext_type:<30} {count:>10} {size:>20}\n")
        else:
            f.write("No files found or accessible to analyze.\n")

        f.write("\n--- Symbolic Link Details ---\n")
        symlinks_found = [file_info for file_info in all_files_data if file_info['is_symlink']]
        if symlinks_found:
            f.write(f"Found {len(symlinks_found)} symbolic links:\n")
            for sl in symlinks_found:
                f.write(f"  Link: {sl['path']}\n")
                f.write(f"    Type: {sl['type']}\n")  # This will be .<symlink>, .<broken_symlink> etc.
                f.write(f"    Own Size (bytes): {sl['size_bytes']}\n")
                f.write(f"    Target Path: {sl['symlink_target_path']}\n")
                if sl['symlink_target_type']:
                    f.write(f"    Target Type: {sl['symlink_target_type']}\n")
                if sl['symlink_target_size_bytes'] is not None:
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
            all_file_details, summary_stats = analyze_directory(target_dir, current_os)

            # Print live summary to console
            print("\n--- Analysis Summary (Console) ---")
            print(f"Target Directory: {summary_stats['target_directory']}")
            print(f"Total Directories Scanned: {summary_stats['total_directories_scanned']}")
            print(f"Total File Entries Processed: {summary_stats['total_files_processed']}")
            if summary_stats['skipped_access_errors'] > 0:
                print(f"Skipped items due to access/read errors: {summary_stats['skipped_access_errors']}")

            print("\n--- File Types Summary (Console) ---")
            if summary_stats['file_types_summary']:
                print(f"{'Extension/Type':<30} {'Count':>10} {'Total Size (Bytes)':>20}")
                print("-" * 65)
                for ext_type, count in summary_stats['file_types_summary'].items():
                    size = summary_stats['file_types_size_summary'].get(ext_type, 0)
                    print(f"{ext_type:<30} {count:>10} {size:>20}")
            else:
                print("No files found or accessible to analyze.")

            # Generate and write report to file
            report_file = generate_report_filename()
            write_summary_report(report_file, summary_stats, all_file_details, current_os)

            # Later: Pass all_file_details to Pandas and plotting functions
            if all_file_details:
                print(f"\nCollected details for {len(all_file_details)} file entries for further processing.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No valid directory selected or user chose to exit. Exiting program.")


if __name__ == "__main__":
    main()