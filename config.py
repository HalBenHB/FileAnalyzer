# config.py

# --- Report Generation Configuration ---
# Set to True to include the detailed list of all symbolic links in the report.
# Set to False to omit it and only show the summary table.
INCLUDE_DETAILED_SYMLINK_LIST = True

# Number of top hidden file types to display in the "Hidden Items Summary" table.
TOP_N_HIDDEN_TYPES = 10

# --- Directory Analysis Configuration ---
# Interval for printing file processing progress updates during directory scan.
PROGRESS_UPDATE_INTERVAL_FILES = 500  # Update after every N files processed in current dir

# Interval for printing directory scanning progress updates.
PROGRESS_UPDATE_INTERVAL_DIRS = 20   # Update after every N directories (roots) visited
