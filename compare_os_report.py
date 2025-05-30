import re
import csv
import config

def extract_summary_data(report_text):
    summary = {}
    overall_section = re.search(r"--- Overall Summary ---\n(.*?)\n\n", report_text, re.DOTALL)
    if not overall_section:
        return summary
    
    lines = overall_section.group(1).splitlines()
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            summary[key.strip()] = int(val.strip().replace(',', ''))  
    return summary

def extract_os_name(report_text):
    match = re.search(r"Operating System:\s+(.*)", report_text)
    return match.group(1).strip() if match else "Unknown"

import csv

def compare_reports(file1, file2):
    metrics = [
        "Skipped items due to access/read errors",
        "Total Directories Scanned (walked into)",
        "Total Directory Symbolic Links Found (in os.walk 'dirs' list)",
        "Total File-like Entries Processed (from os.walk 'files' list)",
        "Total Hidden Items Found (Files & Dir Symlinks)",
    ]

    def parse_report(path):
        values = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                for metric in metrics:
                    if metric in line:
                        try:
                            val = int(line.split(":")[-1].strip())
                            values[metric] = val
                        except:
                            values[metric] = "N/A"
        return values

    linux_data = parse_report(file1)
    windows_data = parse_report(file2)

    # Output CSV
    with open("os_comparison.csv", "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Metric", "Linux", "Windows"])
        for metric in metrics:
            writer.writerow([metric, linux_data.get(metric, "N/A"), windows_data.get(metric, "N/A")])

    # Output Markdown
    with open(f"{config.REPORT_OUTPUT_DIRECTORY}/os_comparison.md", "w", encoding="utf-8") as mdfile:
        mdfile.write("# File System Comparison: Linux vs Windows\n\n")
        mdfile.write("| Metric | Linux | Windows |\n")
        mdfile.write("|--------|--------|---------|\n")
        for metric in metrics:
            mdfile.write(f"| {metric} | {linux_data.get(metric, 'N/A')} | {windows_data.get(metric, 'N/A')} |\n")

        mdfile.write("\n## Observations\n")
        mdfile.write(
            """Although comparing the Linux `/` directory with the Windows `C:\\` may not be perfectly fair due to differences in disk size and structure, a few insights can still be made:

- **Symbolic Links**: Linux shows a significantly higher number of symbolic links (5484) compared to Windows (5), highlighting the more prevalent use of symlinks in Unix-like systems.
- **Directory Depth**: Windows has far more directories and files scanned, likely due to user installations and nested application directories.
- **Access Errors**: Linux had more skipped items due to access errors, which might be due to system permissions on `/proc` or `/sys`.

This comparison is not meant to draw absolute conclusions but offers a glimpse into OS-level filesystem characteristics.
"""
        )

    print("✅ Comparison saved as `os_comparison.csv` and `os_comparison.md`.")


if __name__ == "__main__":
    compare_reports(
        f"{config.REPORT_OUTPUT_DIRECTORY}/file_analysis_report_2025-05-24_20-01-06.txt",  # Linux report
        f"{config.REPORT_OUTPUT_DIRECTORY}/file_analysis_report_2025-05-24_22-30-45.txt",  # Windows report
    )

#compare_reports("file_analysis_report_2025-05-23_19-29-00.txt", "file_analysis_report_2025-05-23_22-49-44.txt")
