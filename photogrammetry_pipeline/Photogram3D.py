# =========================================================================
# Folder Content Monitoring Script (Python, en-GB)
# Author: Jiří Mach
# Institution: UCT Prague, Faculty of Food and Biochemical Technology,
#              Laboratory of Bioengineering
# Licence: Apache 2.0
# Date: 2025-09-18
# Description:
#   Continuously monitors a target folder for the expected number of
#   subfolders and image files. When the defined structure is satisfied,
#   the script automatically triggers Plant3D.py to launch the
#   photogrammetric reconstruction workflow.
# =========================================================================

import os
import time
import subprocess

# Expected counts — must match FOLDER_AMOUNT and IMAGE_AMOUNT in config.json
FOLDER_AMOUNT = 2    # expected number of subfolders
IMAGE_AMOUNT   = 361 # expected number of images per subfolder


def monitor_folder(folder_path):
    while True:
        # List only subfolders (directories)
        subfolders = [f for f in os.listdir(folder_path)
                      if os.path.isdir(os.path.join(folder_path, f))]

        if len(subfolders) == FOLDER_AMOUNT:
            all_valid = True
            for folder in subfolders:
                subfolder_path = os.path.join(folder_path, folder)
                image_files = [f for f in os.listdir(subfolder_path)
                               if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if len(image_files) != IMAGE_AMOUNT:
                    all_valid = False
                    break
            if all_valid:
                trigger_analysis()
                break

        time.sleep(10)


def trigger_analysis():
    print("[OK] Starting photogrammetric reconstruction...")
    python_path = os.path.join(".", "Python39", "python.exe")
    script_path = os.path.join(os.path.dirname(__file__), "plant3D_reconstruction.py")
    subprocess.run([python_path, script_path])


if __name__ == "__main__":
    # Path to the monitored folder — update to your actual path
    folder_path = os.path.join(".", "source_data")
    monitor_folder(folder_path)
