# =========================================================================
# Single Image Capture Utility (Python, en-GB)
# Author: Jiří Mach
# Institution: UCT Prague, Faculty of Food and Biochemical Technology,
#              Laboratory of Bioengineering
# Licence: Apache 2.0
# Date: 2025-09-18
# Description:
#   Provides a helper function `capture_single_image()` for grabbing one
#   RGB frame from a Daheng camera using the gxipy SDK. The captured frame
#   is converted (gxipy → NumPy → Pillow) and saved as a JPEG with a
#   sequential index in the specified output folder.
# Dependencies:
#   Python stdlib: os, time
#   Third-party: gxipy (Daheng SDK), Pillow (PIL)
# =========================================================================

import os
import time
import gxipy as gx
from PIL import Image

def capture_single_image(output_folder, index, exposure_time=50000.0):
    dm = gx.DeviceManager()
    devnum, devinfo_list = dm.update_device_list()
    if devnum == 0:
        print("[Error] Camera not found.")
        return False

    cam = dm.open_device_by_sn(devinfo_list[0]['sn'])

    if cam.ExposureTime.is_writable():
        cam.ExposureTime.set(exposure_time)

    cam.stream_on()
    raw_image = cam.data_stream[0].get_image(timeout=1000)

    if not raw_image or raw_image.get_status() != 0:
        print(f"[Error] Image no. {index} could not be captured.")
        cam.stream_off()
        cam.close_device()
        return False

    rgb_image = raw_image.convert("RGB")
    numpy_image = rgb_image.get_numpy_array()
    image = Image.fromarray(numpy_image)

    filename = os.path.join(output_folder, f"Img_{index:03}.jpg")
    image.save(filename)

    cam.stream_off()
    cam.close_device()
    print(f"[OK] Image saved: {filename}")
    return True

if __name__ == "__main__":
    output_folder = r".\photogram_source_data"
    os.makedirs(output_folder, exist_ok=True)
    
    # Call of the function with parameters, e.g. index=1 and exposure_time=50000.0
    capture_single_image(output_folder, index=1, exposure_time=50000.0)
