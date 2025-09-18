# Import knihoven
import os
import time
import json
import subprocess

## Načtení user dat z json souboru
with open(r"Z:\Data\Photogrammetry\Data_processing\Fotogram3D_v2\_internal\config.json", "r") as f:
    config = json.load(f)

## Definice počtu souborů a snímků
folder_amount = config.get("FOLDER_AMOUNT", None)
image_amount = config.get("IMAGE_AMOUNT", None)

## Definice funkcí
def monitor_folder(folder_path):
    while True:
        # Získá pouze složky (adresáře)
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
    print("✅ Spouštím fotogrammetrickou analýzu...")

    # Spustí Plant3D.py ve stejném adresáři
    python_path = r'C:\Program Files\Python39\python.exe'
    script_path = os.path.join(os.path.dirname(__file__), "Plant3D.py")
    subprocess.run([python_path, script_path])  

# Změň na skutečnou cestu k síťové složce
folder_path = config.get("SOURCE_FOLDER_PATH", None)
monitor_folder(folder_path)