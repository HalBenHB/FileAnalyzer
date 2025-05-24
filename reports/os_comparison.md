# File System Comparison: Linux vs Windows

| Metric | Linux | Windows |
|--------|--------|---------|
| Skipped items due to access/read errors | 8 | 70 |
| Total Directories Scanned (walked into) | 56293 | 341290 |
| Total Directory Symbolic Links Found (in os.walk 'dirs' list) | 5472 | 5 |
| Total File-like Entries Processed (from os.walk 'files' list) | 598333 | 1380718 |
| Total Hidden Items Found (Files & Dir Symlinks) | 1656 | 1369 |

## Observations
Although comparing the Linux `/` directory with the Windows `C:\` may not be perfectly fair due to differences in disk size and structure, a few insights can still be made:

- **Symbolic Links**: Linux shows a significantly higher number of symbolic links (5484) compared to Windows (5), highlighting the more prevalent use of symlinks in Unix-like systems.
- **Directory Depth**: Windows has far more directories and files scanned, likely due to user installations and nested application directories.
- **Access Errors**: Linux had more skipped items due to access errors, which might be due to system permissions on `/proc` or `/sys`.

This comparison is not meant to draw absolute conclusions but offers a glimpse into OS-level filesystem characteristics.
