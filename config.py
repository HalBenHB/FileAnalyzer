# config.py

# --- Scan Data Caching ---
# Set to True to attempt to load a previously saved scan for the selected target directory.
# If True and no saved scan is found, a new scan will be performed.
LOAD_SAVED_SCAN = True # Default to False, user can change to True to enable loading

# Set to True to save the results of a new scan.
# This will overwrite any existing saved scan for the same target directory.
SAVE_NEW_SCAN = True   # Default to True to save new scans

# Directory to store saved scan data files.
SCAN_DATA_DIRECTORY = "scan_data"

# --- Report Generation Configuration ---
# Directory where text analysis reports will be saved.
REPORT_OUTPUT_DIRECTORY = "reports"

# Set to True to include the detailed list of all symbolic links in the report.
# Set to False to omit it and only show the summary table.
INCLUDE_DETAILED_SYMLINK_LIST = True


# --- Plot Generation Configuration ---
PLOT_OUTPUT_DIRECTORY = "Plots"

# How to handle the 'size' of symbolic links in size-based plots (PMF, CDF, Scatter):
# - 'target': Use the symlink's target file size. WARNING: This can lead to double counting
#             if the target file is also scanned independently.
# - 'own_size': Use the symlink's own intrinsic size (path length on Linux, often 0 on Windows).
#               This treats symlinks as distinct, typically small, files.
# - 'exclude': Exclude all symbolic links from these size-based plots.
# Recommended for avoiding double count: 'own_size' or 'exclude'
SYMLINK_SIZE_HANDLING_FOR_PLOTS = 'exclude'

# For file type bar chart, how many top types to display
BAR_CHART_TOP_N_TYPES = 20

# Number of top hidden file types to display in the "Hidden Items Summary" table.
TOP_N_HIDDEN_TYPES = 10

# --- Directory Analysis Configuration ---
# Interval for printing file processing progress updates during directory scan.
PROGRESS_UPDATE_INTERVAL_FILES = 500  # Update after every N files processed in current dir

# Interval for printing directory scanning progress updates.
PROGRESS_UPDATE_INTERVAL_DIRS = 20   # Update after every N directories (roots) visited
