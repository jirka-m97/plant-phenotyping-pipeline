# =========================================================================
# Photogrammetry Acquisition Orchestrator (Python, en-GB)
# Author: Jiří Mach
# Institution: UCT Prague, Faculty of Food and Biochemical Technology, Laboratory of Bioengineering
# Licence: Apache 2.0
# Date: 2025-09-18
# Description:
#   Orchestrates end-to-end acquisition for plant photogrammetry:
#   - decodes QR (pyzbar/OpenCV), creates time-stamped dataset folder,
#   - uploads Arduino sketches (zero / continuous) via CLI helper,
#   - drives AR4 robot over serial (command conversion + handshaking),
#   - captures QR and multi-view images (gxipy / PIL) with exposure control,
#   - manages pose programs (pickle), indexing, and basic logging.
# Dependencies:
#   Python stdlib: os, re, sys, time, pickle, shutil, subprocess
#   Third-party: OpenCV (cv2), numpy, pyzbar, pyserial, gxipy, Pillow (PIL)
#   Local modules: arduino_upload.py, single_capture.py
# =========================================================================


import os
import re
import cv2
import sys
import time
import pickle
import shutil
import serial
import gxipy as gx
from PIL import Image
from datetime import datetime
from pyzbar.pyzbar import decode

from arduino_upload import upload_arduino
from single_capture import capture_single_image

### === Path and parameters setup ===

## QR code
ROB_POS = r".\P_QR"
ARDUINO_ZERO = r".\turntable_zero.ino" 
ARDUINO_PORT = "COM5" # Adjust COM port if needed
fqbn = "arduino:avr:uno"
BASE_FOLDER = r".\Fotogram_source_data"
QR_IMAGE_NAME = "QR_code.jpg"
QR_EXPOSURE = 180_000

## Continuous rotation - turntable
ARDUINO_CON = r".\turntable_continuous.ino"

## Images capture
IMG_EXPOSURE = 50_000
SERIAL_PORT = "COM4"
#IMG_AMOUNT = 60 # For full set 360 images
IMG_AMOUNT = 40 # For reduced set 120 images
#ACQ_PAUSE = 0.25 # For full set 360 images
ACQ_PAUSE = 0.475 # For reduced set 120 images
#P_POSES_ONLY = r".\P_fullset_360" # For full set 360 images
P_POSES_ONLY = r".\P_redset_120" # For reduced set 120 images
CAMERA_SCRIPT_SELFCONTAINED = False

## Last pose - END
P_END = r".\P_end"

TEMP_QR_FOLDER = r".\temp_qr"

# === QR code: processing ===
def decode_qr(image_path):
    img = cv2.imread(image_path)
    decoded = decode(img)
    return decoded[0].data.decode('utf-8') if decoded else None

def create_folder_from_qr(qr_content):
    try:
        name, spec = qr_content.split('_')
        folder_name = f"{datetime.now():%y%m%d}_{spec}_{name}"
        folder_path = os.path.join(BASE_FOLDER, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path
    except Exception as e:
        print(f"[Error] Folder creation: {e}")
        return None

def save_image_to_folder(image_path, destination_folder):
    folder_name = os.path.basename(destination_folder)
    new_image_name = f"{folder_name}_QR_code.jpg"
    new_image_path = os.path.join(destination_folder, new_image_name)
    shutil.move(image_path, new_image_path)

def process_qr_image(image_path):
    qr_content = decode_qr(image_path)
    if not qr_content:
        print("[Error] QR code not found or cannot be decoded.")
        return None

    folder = create_folder_from_qr(qr_content)
    if folder:
        save_image_to_folder(image_path, folder)
        print(f"[OK] QR image saved to: {folder}")
        return folder
    else:
        print("[Error] Failed to create target folder.")
        return None


# === Robot: serial communication ===
def init_serial(port="COM4", baudrate=9600):
    return serial.Serial(port, baudrate, timeout=1)

def convert_command(command):
    if command.startswith("Move J [*]"):
        cmd = command.replace("Move J [*] ", "MJ")
        for part in [" X ", " Y ", " Z ", " Rz ", " Ry ", " Rx ", " J7 ", " J8 ", " J9 ", " Sp ", " Ac ", " Dc ", " Rm ", " $ "]:
            cmd = cmd.replace(part, part.strip())
        cmd += "Lm000000"
        return cmd
    return command

def send_command_wait_for_response(ser, command, timeout=10):
    if command.startswith("Wait Time"):
        wait_val = float(command.split("=")[1].strip())
        print(f"[WAIT] {wait_val:.1f} s")
        time.sleep(wait_val)
        return "[Waiting finished]"

    cmd = convert_command(command)
    ser.write((cmd + "\n").encode())
    print(f"[SEND] {cmd}")

    start = time.time()
    while time.time() - start < timeout:
        response = ser.readline().decode().strip()
        if response:
            print(f"[RECV] {response}")
            if response.startswith("A"):
                return response

    print("[RECV] [No response within timeout]")
    return None


# === Camera + QR workflow ===
def run_camera_qr(output_folder):
    """Takes one QR snapshot and saves it into output_folder as Img_001.jpg"""
    success = capture_single_image(output_folder, index=1, exposure_time=QR_EXPOSURE)
    if not success:
        print("[Error] Failed to capture QR image.")
        return False
    return True

# === Camera + multiple images ===
def capture_multiple_images(folder, count, exposure_time):
    from gxipy import DeviceManager

    dm = DeviceManager()
    devnum, devinfo = dm.update_device_list()
    if devnum == 0:
        print("[Error] Camera not found.")
        sys.exit(1)

    cam = dm.open_device_by_sn(devinfo[0]['sn'])
    cam.ExposureTime.set(exposure_time)
    cam.stream_on()

    # Buffer clearing
    stream = cam.data_stream[0]
    while True:
        img = stream.get_image(timeout=50)
        if img is None or img.get_status() != 0:
            break

    start_idx = get_next_image_index(folder)
    for i in range(start_idx, start_idx + count):
        raw = cam.data_stream[0].get_image(timeout=1000)
        if not raw or raw.get_status() != 0:
            print(f"[Warning] No or incorrect image for the slide {i}")
            continue

        rgb = raw.convert("RGB")
        img_array = rgb.get_numpy_array()
        filename = os.path.join(folder, f"Img_{i:03}.jpg")
        Image.fromarray(img_array).save(filename)
        print(f"[OK] Image saved to: {filename}")

        # time.sleep(ACQ_PAUSE)  # pause between images

    cam.stream_off()
    cam.close_device()

def get_next_image_index(folder):
    pattern = re.compile(r"Img_(\d+)\.jpg")
    max_idx = max(
        (int(match.group(1)) for f in os.listdir(folder)
         if (match := pattern.match(f))),
        default=0
    )
    return max_idx + 1

# === Robot: program execution ===
def load_program(file_path):
    with open(file_path, "rb") as f:
        return pickle.load(f)

# === Main execution ===
if __name__ == "__main__":
    print("[START] Initiating photogrammetric analysis.")
    print("[INFO] Zero positioning...")

    # 1) Upload Arduino for zero position
    if upload_arduino(ARDUINO_ZERO, ARDUINO_PORT, fqbn):
        print("[OK] Arduino code uploaded. (Zero position set)")

        # 2) Robot positioning according to ROB_POS
        try:
            print("[INFO] Starting robot positioning (ROB_POS)...")
            robot_program = load_program(ROB_POS)
            ser = init_serial(SERIAL_PORT, 9600)

            for cmd in robot_program:
                if cmd.startswith("##") or cmd.startswith("Tab Number"):
                    continue
                send_command_wait_for_response(ser, cmd)

            print("[OK] Robot positioned.")
        except Exception as e:
            print(f"[ERROR] Robot positioning failed: {e}")
            sys.exit(1)

        # 3) Capture QR image into temp folder
        os.makedirs(TEMP_QR_FOLDER, exist_ok=True)
        print("[INFO] Waiting 2 seconds before capturing QR image...")
        time.sleep(1)

        success = run_camera_qr(TEMP_QR_FOLDER)
        if not success:
            print("[ERROR] Failed to capture the QR code image. Exiting.")
            sys.exit(1)

        # 4) Process QR image and create main folder
        qr_image_path = os.path.join(TEMP_QR_FOLDER, "Img_001.jpg")
        folder = process_qr_image(qr_image_path)
        if not folder:
            print("[ERROR] Failed to create folder from QR. Exiting.")
            sys.exit(1)

    else:
        print("[ERROR] Arduino code upload failed.")
        sys.exit(1)

    # 5) Upload code for continuous rotation
    if upload_arduino(ARDUINO_CON, ARDUINO_PORT, fqbn):
        print("[OK] Arduino code uploaded. (Starting continuous rotation)")
    else:
        print("[ERROR] Failed to upload continuous rotation code.")
        sys.exit(1)

    # 6) Capture images for each pose in P_POSES_ONLY
    try:
        print("[INFO] Starting positioning for each pose in P_poses_only...")
        poses_program = load_program(P_POSES_ONLY)

        if 'ser' not in locals() or not ser.is_open:
            ser = init_serial(SERIAL_PORT, 9600)

        img_index = 1

        for cmd in poses_program:
            if cmd.startswith("##") or cmd.startswith("Tab Number"):
                continue

            if cmd.startswith("Move J [*]"):
                response = send_command_wait_for_response(ser, cmd)
                if response:
                    print("[INFO] Position reached, starting image capture...")
                    for _ in range(IMG_AMOUNT):
                        success = capture_single_image(folder, img_index, exposure_time=IMG_EXPOSURE)
                        if not success:
                            print(f"[Warning] Image no. {img_index} failed.")
                        else:
                            print(f"[OK] Image no. {img_index} captured.")
                        img_index += 1
                        time.sleep(ACQ_PAUSE)

            elif cmd.startswith("Wait Time"):
                send_command_wait_for_response(ser, cmd)

        print("[OK] Finished positioning and capturing for all poses.")
    except Exception as e:
        print(f"[ERROR] Error during P_poses_only execution: {e}")
        sys.exit(1)

    # 7) Final robot position (P_END)
    try:
        print("[INFO] Starting robot positioning (P_END)...")
        end_program = load_program(P_END)

        if 'ser' not in locals() or not ser.is_open:
            ser = init_serial(SERIAL_PORT, 9600)

        for cmd in end_program:
            if cmd.startswith("##") or cmd.startswith("Tab Number"):
                continue
            send_command_wait_for_response(ser, cmd)

        print("[OK] Robot moved to final position.")
    except Exception as e:
        print(f"[ERROR] Final positioning failed: {e}")

    # 8) Closing serial port
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("[INFO] Serial port closed.")

    print("[DONE] Photogrammetric analysis successfully ended.")
