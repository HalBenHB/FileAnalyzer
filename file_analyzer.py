import os
import platform
import pathlib
# import shutil # We'll add this when we need it
# import pandas as pd # For later
# import matplotlib.pyplot as plt # For later
# import numpy as np # For later
# import scipy.stats # For later

def detect_os():
    system = platform.system()
    if system == "Windows":
        return "Windows"
    elif system == "Linux": # Ubuntu is a Linux distribution
        return "Linux"
    else:
        return "Unknown"

def main():
    current_os = detect_os()
    print(f"Running on: {current_os}")
    if current_os == "Unknown":
        print("Unsupported operating system. Exiting.")
        return
    print("Project: File Analysis")

if __name__ == "__main__":
    main()