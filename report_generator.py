# report_generator.py
import datetime
from directory_analyzer import ( # Keep these if needed for symlink summary
    SYMLINK_TYPE_STR, BROKEN_SYMLINK_TYPE_STR,
    SYMLINK_TO_DIR_TYPE_STR, SYMLINK_ERROR_TYPE_STR
)

# Number of top hidden file types to display in the table
TOP_N_HIDDEN_TYPES = 10

def generate_report_filename():
    """Generates a filename with a timestamp."""
    now = datetime.datetime.now()
    return f"file_analysis_report_{now.strftime('%Y-%m-%d_%H-%M-%S')}.txt"


def write_summary_report(report_filepath, summary_data, all_files_data, dir_symlinks_data, os_name, include_details):
    """Writes the analysis summary and symlink details to a text file."""
    with open(report_filepath, 'w', encoding='utf-8') as f:
        f.write("--- File System Analysis Report ---\n")
        f.write(f"Operating System: {os_name}\n")
        # summary_data['target_directory'] should already be absolute from analyze_directory
        f.write(f"Analyzed Directory: {summary_data['target_directory']}\n")
        f.write(f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        f.write("\n--- Overall Summary ---\n")
        f.write(f"Total Directories Scanned (walked into): {summary_data['total_directories_scanned']}\n")
        f.write(f"Total File-like Entries Processed (from os.walk 'files' list): {summary_data['total_file_entries_processed']}\n")
        f.write(f"Total Directory Symbolic Links Found (in os.walk 'dirs' list): {summary_data['total_directory_symlinks_found']}\n")

        # --- Display Total Hidden Files Count in Overall Summary ---
        f.write(f"Total Hidden Items Found (Files & Dir Symlinks): {summary_data.get('total_hidden_files_count', 0)}\n")
        # ---------------------------------------------------------

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

        # --- Hidden Files Summary Section ---
        f.write("\n--- Hidden Items Summary ---\n")
        total_hidden_count = summary_data.get('total_hidden_files_count', 0)
        total_hidden_size = summary_data.get('total_hidden_files_size', 0)
        f.write(f"Total Hidden Items Count: {total_hidden_count}\n")
        f.write(f"Total Storage Size of Hidden Items (own sizes): {total_hidden_size} bytes\n")

        hidden_types_summary = summary_data.get('hidden_file_types_summary', {})
        if total_hidden_count > 0 and hidden_types_summary:
            f.write(f"\nTop {TOP_N_HIDDEN_TYPES} Hidden Item Types by Count:\n")
            f.write(f"{'Hidden Type':<30} {'Count':>10} {'Total Size (Bytes)':>20}\n")
            f.write("-" * 65 + "\n")

            # Sort hidden types by count for the top N display
            # hidden_types_summary is already sorted by count from directory_analyzer
            count_displayed = 0
            for item_type, count in hidden_types_summary.items():
                if count_displayed >= TOP_N_HIDDEN_TYPES:
                    break
                size = summary_data['hidden_file_types_size_summary'].get(item_type, 0)
                f.write(f"{item_type:<30} {count:>10} {size:>20}\n")
                count_displayed += 1
            if len(hidden_types_summary) > TOP_N_HIDDEN_TYPES:
                f.write("... and more ...\n")
        elif total_hidden_count > 0:
            f.write("Breakdown by type for hidden items is not available (or all hidden items had errors).\n")
        else:
            f.write("No hidden items found.\n")
        # ------------------------------------

        f.write("\n--- Symbolic Link Type Summary ---\n")
        symlink_types_for_summary = [
            SYMLINK_TYPE_STR,
            SYMLINK_TO_DIR_TYPE_STR,
            BROKEN_SYMLINK_TYPE_STR,
            SYMLINK_ERROR_TYPE_STR
        ]

        has_symlink_summary_data = any(
            stype in summary_data['file_types_summary'] for stype in symlink_types_for_summary)

        if has_symlink_summary_data:
            f.write(f"{'Symlink Category':<30} {'Count':>10} {'Total Own Size (Bytes)':>25}\n")
            f.write("-" * 70 + "\n")
            total_symlinks_in_summary = 0
            total_symlink_own_size_in_summary = 0
            for sl_type in symlink_types_for_summary:
                count = summary_data['file_types_summary'].get(sl_type, 0)
                if count > 0:
                    own_size = summary_data['file_types_size_summary'].get(sl_type, 0)
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
                for sl in sorted(all_symlinks_detailed, key=lambda x: x['path']):  # Sort by path
                    f.write(f"  Link: {sl['path']}\n")
                    f.write(f"    Type: {sl['type']}\n")
                    f.write(f"    Own Size (bytes): {sl['size_bytes']}\n")
                    f.write(f"    Target Path: {sl['symlink_target_path']}\n")
                    if sl.get('symlink_target_type'):
                        f.write(f"    Target Type: {sl['symlink_target_type']}\n")
                    if sl.get('symlink_target_size_bytes') is not None: # For file symlinks
                        f.write(f"    Target Size (bytes): {sl['symlink_target_size_bytes']}\n")
                    f.write("-" * 20 + "\n")
            else:
                f.write("No symbolic links found for detailed listing.\n")
        else:
            f.write("\n--- Symbolic Link Details (Detailed List Omitted by Configuration) ---\n")

        f.write("\n--- End of Report ---\n")
    print(f"\nAnalysis report saved to: {report_filepath}")