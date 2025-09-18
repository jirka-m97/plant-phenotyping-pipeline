# =========================================================================
# Folder Content Monitoring Script (Python, en-GB)
# Author: Jiří Mach
# Institution: UCT Prague, Laboratory of Bioengineering
# Licence: Apache 2.0
# Date: 2025-09-18
# Description:
#   Continuously monitors a target folder for the expected number of
#   subfolders and image files. When the defined structure is satisfied,
#   the script automatically triggers Plant3D.py to launch the
#   photogrammetric reconstruction workflow.
# =========================================================================

# Import libraries
import os
import time
import subprocess

## Expected counts of folders and images
folder_amount = 2      # Example: number of subfolders
image_amount = 361     # Example: number of images per subfolder

## Define functions
def monitor_folder(folder_path):
    while True:
        # List only subfolders (directories)
        subfolders = [f for f in os.listdir(folder_path)
                      if os.path.isdir(os.path.join(folder_path, f))]
        
        if len(subfolders) == folder_amount:
            all_valid = True
            for folder in subfolders:
                subfolder_path = os.path.join(folder_path, folder)
                image_files = [f for f in os.listdir(subfolder_path)
                               if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if len(image_files) != image_amount:
                    all_valid = False
                    break
            if all_valid:
                trigger_analysis()
                break

        time.sleep(10)

def trigger_analysis():
    print("✅ Starting photogrammetry analysis...")

    # Run Plant3D.py located in the same directory
    python_path = r'.\Python39\python.exe'
    script_path = os.path.join(os.path.dirname(__file__), "Plant3D.py")
    subprocess.run([python_path, script_path])  

# Path to the monitored folder (update to your actual path)
folder_path = r".\source_data"
monitor_folder(folder_path)

