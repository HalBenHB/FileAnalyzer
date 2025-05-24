# plot_generator.py

import os
import config
import datetime
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
def generate_plot_filename(plot_name):
    """Generates a filename with a timestamp for a plot."""
    now = datetime.datetime.now()
    plot_output_dir = config.PLOT_OUTPUT_DIRECTORY
    if not os.path.exists(plot_output_dir):
        os.makedirs(plot_output_dir)
    plot_output_filename= f"{plot_name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.png"
    return os.path.join(plot_output_dir, plot_output_filename)

def get_sizes_for_plotting(all_files_data):
    """
    Prepares a list of file sizes based on the SYMLINK_SIZE_HANDLING_FOR_PLOTS config.
    This list is used for PMF, CDF, and scatter plots.
    """
    sizes = []

    for item in all_files_data:
        is_symlink = item.get('is_symlink', False)
        size_bytes = item.get('size_bytes', 0) # This is symlink's own size if it's a symlink

        if is_symlink:
            if config.SYMLINK_SIZE_HANDLING_FOR_PLOTS == 'target':
                # Potentially double counts if target is also in all_files_data
                target_size = item.get('symlink_target_size_bytes')
                if target_size is not None:
                    sizes.append(target_size)
            elif config.SYMLINK_SIZE_HANDLING_FOR_PLOTS == 'own_size':
                if size_bytes >= 0: # Include 0-byte symlinks (Windows)
                    sizes.append(size_bytes)
            elif config.SYMLINK_SIZE_HANDLING_FOR_PLOTS == 'exclude':
                pass # Do not include symlinks
            else: # Default to excluding if config is unknown
                pass
        else: # Not a symlink (regular file)
            if size_bytes >= 0: # We may want to control it for non-empty files but we are including them for distributions.
                sizes.append(size_bytes)
    return sizes

def generate_plots(all_files_data, directory_symlinks_data, summary_data, os_name):
    """
    Main function to generate and save all specified plots.
    """
    print(f"\n--- Generating Plots for {os_name} ---")

    if not all_files_data and not directory_symlinks_data:
        print("No data available to generate plots.")
        return

    # Prepare sizes based on config (handles symlinks and potential double counting)
    plot_sizes = get_sizes_for_plotting(all_files_data)

    if not plot_sizes:
        # More specific message based on why plot_sizes might be empty
        if config.SYMLINK_SIZE_HANDLING_FOR_PLOTS == 'exclude' and not any(not f.get('is_symlink', False) for f in all_files_data):
            print("No non-symlink file data available to generate size-based plots (and symlinks are excluded).")
        else:
            print("No valid file sizes available to generate size-based plots after filtering/processing.")

    # Create a unique prefix for filenames for this run/OS
    # Sanitize target directory path for use in filenames
    sanitized_target_dir = summary_data.get('target_directory', 'unknown_dir').replace(':', '').replace('/', '_').replace('\\', '_')
    # Take last part of path if too long, or a fixed length
    if len(sanitized_target_dir) > 30:
        sanitized_target_dir = sanitized_target_dir[-30:]

    base_plot_name_prefix = f"{os_name}_{sanitized_target_dir}"

    if plot_sizes:
        # PMF plot (normalized histogram for probability density)
        generate_pmf_plot(plot_sizes, os_name, base_plot_name_prefix)

        # Histogram plot (frequency counts)
        generate_size_histogram_plot(plot_sizes, os_name, base_plot_name_prefix)

        # CDF plot
        generate_cdf_plot(plot_sizes, os_name, base_plot_name_prefix)

    # Bar chart for file types uses all_files_data directly
    generate_file_type_bar_chart(all_files_data, directory_symlinks_data, os_name, base_plot_name_prefix)

    print(f"Plots saved in '{config.PLOT_OUTPUT_DIRECTORY}' directory.")

    #generate_pmf_plot(all_files_data,os_name)
    #generate_cdf_plot(all_files_data,os_name)
    #generate_scatter_plot(all_files_data,os_name)
    #generate_file_type_bar_chart(all_files_data,os_name)

def generate_pmf_plot(sizes, os_name, base_plot_name_prefix):
    """
    Generates a PMF plot (normalized histogram for probability density) of file sizes.
    'sizes' is a list of integers.
    """
    if not sizes:
        print("PMF plot: No sizes to plot.")
        return

    plt.figure(figsize=(10, 6))

    # Use logarithmic bins for file sizes as they span many orders of magnitude
    # Filter out non-positive sizes before log, though get_sizes_for_plotting should handle most.
    positive_sizes = [s for s in sizes if s > 0]
    has_zero_sizes = any(s == 0 for s in sizes)

    if not positive_sizes:
        if has_zero_sizes: # All files are 0 bytes
            # Create a single bar at 0 or a small range like [0, 1]
            plt.hist(sizes, bins=[-0.5, 0.5], density=True, alpha=0.7, color='skyblue', edgecolor='black', align='mid')
            plt.xticks([0])
            plt.xlabel("File Size (bytes) - Linear Scale")
        else: # No files at all (or all filtered out)
            print("PMF plot: No positive sizes to plot for log scale, and no zero-byte files.")
            plt.close() # Close the empty figure
            return
    else: # There are positive sizes
        min_val = min(positive_sizes)
        max_val = max(positive_sizes)

        if min_val == max_val : # All positive files are the same size
             # Create bins around this single size for visibility
             bins = [min_val * 0.9 if min_val > 0 else -0.1, min_val * 1.1 if min_val > 0 else 0.1]
             if has_zero_sizes: # If zeros also exist, need to handle bins carefully
                 bins = sorted(list(set([-0.5, 0.5] + bins))) # Combine zero bin with the positive bin
             plt.hist(sizes, bins=bins, density=True, alpha=0.7, color='skyblue', edgecolor='black')
             plt.xlabel("File Size (bytes) - Linear Scale")
        else:
            num_bins = 50
            # If zeros are present, they will be in their own bin if the log scale doesn't cover them
            # or might be excluded by log scale. It's often better to plot zeros separately or use symlog.
            # For simplicity, histogram on positive sizes with log bins.
            log_bins = np.logspace(np.log10(min_val), np.log10(max_val), num_bins)
            plt.hist(positive_sizes, bins=log_bins, density=True, alpha=0.7, color='skyblue', edgecolor='black')
            plt.xscale('log')
            plt.xlabel("File Size (bytes) - Log Scale (Positive Sizes Only)")
            if has_zero_sizes:
                # Add a note if zero-byte files were present but not shown on log scale PMF
                plt.text(0.05, 0.05, f"Note: {sizes.count(0)} zero-byte files not shown on log scale",
                         transform=plt.gca().transAxes, fontsize=9, color='gray')


    plt.ylabel("Probability Density")
    plt.title(f"PMF of File Sizes ({os_name})")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    plot_filename = generate_plot_filename(f"{base_plot_name_prefix}_pmf_file_sizes")
    plt.savefig(plot_filename)
    plt.close()
    print(f"Saved: {plot_filename}")


def generate_size_histogram_plot(sizes, os_name, base_plot_name_prefix):
    """
    Generates a histogram (frequency counts) of file sizes.
    'sizes' is a list of integers.
    """
    if not sizes:
        print("Size Histogram plot: No sizes to plot.")
        return

    plt.figure(figsize=(10, 6))

    positive_sizes = [s for s in sizes if s > 0]
    has_zero_sizes = any(s == 0 for s in sizes)

    if not positive_sizes:
        if has_zero_sizes: # All files are 0 bytes
            counts, bins = np.histogram(sizes, bins=[-0.5, 0.5])
            plt.bar(bins[:-1], counts, width=np.diff(bins), alpha=0.7, color='coral', edgecolor='black', align='edge')
            plt.xticks([0])
            plt.xlabel("File Size (bytes) - Linear Scale")
        else:
            print("Size Histogram plot: No positive sizes to plot for log scale, and no zero-byte files.")
            plt.close()
            return
    else:
        min_val = min(positive_sizes)
        max_val = max(positive_sizes)

        if min_val == max_val: # All positive files are the same size
             bins = [min_val * 0.9 if min_val > 0 else -0.1, min_val * 1.1 if min_val > 0 else 0.1]
             if has_zero_sizes:
                 bins = sorted(list(set([-0.5, 0.5] + bins)))
             counts, bins = np.histogram(sizes, bins=bins)
             plt.bar(bins[:-1], counts, width=np.diff(bins), alpha=0.7, color='coral', edgecolor='black', align='edge')
             plt.xlabel("File Size (bytes) - Linear Scale")
        else:
            num_bins = 50
            log_bins = np.logspace(np.log10(min_val), np.log10(max_val), num_bins)
            # Plot histogram for positive sizes on log scale
            plt.hist(positive_sizes, bins=log_bins, alpha=0.7, color='coral', edgecolor='black')
            plt.xscale('log')
            plt.xlabel("File Size (bytes) - Log Scale (Positive Sizes Only)")
            if has_zero_sizes:
                plt.text(0.05, 0.05, f"Note: {sizes.count(0)} zero-byte files not shown on log scale",
                         transform=plt.gca().transAxes, fontsize=9, color='gray')

    plt.ylabel("Frequency (Count)")
    plt.title(f"Histogram of File Sizes ({os_name})")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    plot_filename = generate_plot_filename(f"{base_plot_name_prefix}_histogram_file_sizes")
    plt.savefig(plot_filename)
    plt.close()
    print(f"Saved: {plot_filename}")


def generate_cdf_plot(sizes, os_name, base_plot_name_prefix):
    """
    Generates a CDF plot of file sizes.
    'sizes' is a list of integers.
    """
    if not sizes:
        print("CDF plot: No sizes to plot.")
        return

    plt.figure(figsize=(10, 6))

    sorted_sizes = np.sort(sizes) # Includes 0-byte files if they are in 'sizes'
    yvals = np.arange(1, len(sorted_sizes) + 1) / float(len(sorted_sizes))

    plt.plot(sorted_sizes, yvals, marker='.', linestyle='none', ms=4, color='navy')
    plt.plot(sorted_sizes, yvals, linestyle='-', drawstyle='steps-post', color='cornflowerblue')

    # Determine if log scale is appropriate for X-axis
    # If there are positive values and a significant range (e.g., max/min > 10 or many values)
    positive_sizes_for_scale = [s for s in sorted_sizes if s > 0]
    use_log_scale_x = False
    if positive_sizes_for_scale:
        min_pos = min(positive_sizes_for_scale)
        max_pos = max(positive_sizes_for_scale)
        if max_pos / (min_pos or 1) > 10 or len(set(positive_sizes_for_scale)) > 10: # Heuristic
            use_log_scale_x = True

    if use_log_scale_x:
        plt.xscale('log')
        plt.xlabel("File Size (bytes) - Log Scale")
        # Adjust xlim for log scale: ensure min is slightly less than smallest positive if present
        # x_min_limit = min_pos * 0.9 if min_pos > 0 else 1 # Avoid log(0) or log(negative)
        # if x_min_limit <=0: x_min_limit = 1e-1 # a small positive number if min_pos was 0
        # plt.xlim(left=x_min_limit)

    else:
        plt.xlabel("File Size (bytes) - Linear Scale")
        # plt.xlim(left=max(0, min(sorted_sizes) * 0.9 if sorted_sizes.size > 0 and min(sorted_sizes) >=0 else 0))

    # For xlim, ensure it starts from 0 or just before the first data point if linear
    # For log, it must be > 0. Smallest positive value can be a guide.
    if sorted_sizes.size > 0:
        if plt.gca().get_xscale() == 'log':
            first_positive = next((s for s in sorted_sizes if s > 0), None)
            if first_positive is not None:
                plt.xlim(left=first_positive * 0.5) # Start a bit before the first positive point
            else: # All zeros, log scale won't show anything useful, but plot is already linear
                plt.xlim(left=-0.1) # Show around zero
        else: # Linear scale
            plt.xlim(left=min(sorted_sizes) - (max(sorted_sizes)-min(sorted_sizes))*0.05 if len(set(sorted_sizes)) > 1 else min(sorted_sizes)-0.5 )


    plt.ylabel("Cumulative Probability (P(Size <= x))")
    plt.title(f"CDF of File Sizes ({os_name})")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.ylim(0, 1.05)
    plt.tight_layout()
    plot_filename = generate_plot_filename(f"{base_plot_name_prefix}_cdf_file_sizes")
    plt.savefig(plot_filename)
    plt.close()
    print(f"Saved: {plot_filename}")


def generate_file_type_bar_chart(all_files_data, directory_symlinks_data, os_name, base_plot_name_prefix):
    """
    Generates a bar chart for file/entry type counts.
    """
    if not all_files_data and not directory_symlinks_data:
        print("Bar chart: No data for file types.")
        return

    # Consolidate types from both lists
    type_list = [f.get("type", "unknown") for f in all_files_data]
    type_list.extend([d.get("type", "unknown") for d in directory_symlinks_data])

    type_counter = Counter(type_list)
    top_types = type_counter.most_common(config.BAR_CHART_TOP_N_TYPES)

    if not top_types:
        print("Bar chart: No file types to plot after processing.")
        return

    types, counts = zip(*top_types)

    plt.figure(figsize=(12, 8))
    bars = plt.bar(types, counts, color='teal', edgecolor='black')
    plt.xlabel("File / Entry Type")
    plt.ylabel("Count")
    plt.title(f"Top {len(types)} File & Entry Type Counts ({os_name})")
    plt.xticks(rotation=45, ha="right")

    # Dynamic y-ticks
    if counts:
        max_c = max(counts)
        # Ensure step is at least 1
        step_val = max(1, int(max_c * 0.05 if max_c > 20 else (max_c * 0.1 if max_c > 10 else 1) ))
        plt.yticks(np.arange(0, max_c + step_val, step=step_val))


    for bar in bars:
        yval = bar.get_height()
        if yval > 0 :
             plt.text(bar.get_x() + bar.get_width()/2.0, yval + (max(counts)*0.01 if counts and max(counts)>0 else 0.1), int(yval), ha='center', va='bottom', fontsize=9)

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plot_filename = generate_plot_filename(f"{base_plot_name_prefix}_top_entry_types")
    plt.savefig(plot_filename)
    plt.close()
    print(f"Saved: {plot_filename}")