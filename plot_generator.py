# plot_generator.py

import os
import matplotlib.pyplot as plt
from collections import Counter

def generate_plots(all_files_data, directory_symlinks_data, summary_data, output_dir, os_name):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    generate_pmf_plot(all_files_data, output_dir)
    generate_cdf_plot(all_files_data, output_dir)
    generate_scatter_plot(all_files_data, output_dir)
    generate_file_type_bar_chart(all_files_data, output_dir)

def generate_pmf_plot(all_files_data, output_dir):
    buckets = {
        '<1KB': 0,
        '1KB–1MB': 0,
        '1MB–10MB': 0,
        '>10MB': 0,
    }
    total_files = len(all_files_data)

    for file_info in all_files_data:
        size = file_info.get("size_bytes", 0)
        if size < 1024:
            buckets['<1KB'] += 1
        elif size < 1024**2:
            buckets['1KB–1MB'] += 1
        elif size < 10 * 1024**2:
            buckets['1MB–10MB'] += 1
        else:
            buckets['>10MB'] += 1

    pmf = {k: v / total_files for k, v in buckets.items()}

    plt.bar(pmf.keys(), pmf.values())
    plt.title("PMF of File Sizes")
    plt.ylabel("Probability")
    plt.xlabel("Size Range")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "pmf_file_sizes.png"))
    plt.close()

def generate_cdf_plot(all_files_data, output_dir):
    buckets = {
        '<1KB': 0,
        '1KB–1MB': 0,
        '1MB–10MB': 0,
        '>10MB': 0,
    }
    total_files = len(all_files_data)

    for file_info in all_files_data:
        size = file_info.get("size_bytes", 0)
        if size < 1024:
            buckets['<1KB'] += 1
        elif size < 1024**2:
            buckets['1KB–1MB'] += 1
        elif size < 10 * 1024**2:
            buckets['1MB–10MB'] += 1
        else:
            buckets['>10MB'] += 1

    values = list(buckets.values())
    cdf = [sum(values[:i+1]) / total_files for i in range(len(values))]

    plt.plot(list(buckets.keys()), cdf, marker='o')
    plt.title("CDF of File Sizes")
    plt.ylabel("Cumulative Probability")
    plt.xlabel("Size Range")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "cdf_file_sizes.png"))
    plt.close()

def generate_scatter_plot(all_files_data, output_dir):
    sizes = [f.get("size_bytes", 0) for f in all_files_data]

    plt.scatter(range(len(sizes)), sizes, alpha=0.5, s=5)
    plt.title("Scatter Plot of File Sizes")
    plt.xlabel("File Index")
    plt.ylabel("Size (Bytes)")
    plt.yscale("log")  # Optional for better visibility
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "scatter_file_sizes.png"))
    plt.close()

def generate_file_type_bar_chart(all_files_data, output_dir, top_n=10):
    type_counter = Counter(f.get("type", "unknown") for f in all_files_data)
    top_types = type_counter.most_common(top_n)

    if not top_types:
        return  # Nothing to plot

    types, counts = zip(*top_types)
    plt.bar(types, counts)
    plt.title(f"Top {top_n} File Types")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "top_file_types.png"))
    plt.close()
