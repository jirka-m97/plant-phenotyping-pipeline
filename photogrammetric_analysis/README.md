# Photogrammetric Analysis Pipeline

This repository contains the Python script `fotogramm_analysis.py`, which automates a complete photogrammetric acquisition workflow by integrating robotic positioning, camera control, automated image capture, and QR-based sample identification. The system was designed for controlled imaging of plants with the purpose of generating structured datasets suitable for three-dimensional reconstruction and advanced phenotyping studies.

---

## Overview

The workflow coordinates three main hardware components:

- **Robotic arm** controlled by a Teensy 4.1 microcontroller through serial communication  
- **Motorised turntable** operated by Arduino sketches for both zero positioning and continuous rotation  
- **Industrial camera** controlled through the Daheng Galaxy SDK (`gxipy`), capturing sequential images in 8-bit RGB format at a resolution of 4024 × 3036 pixels  

A QR code placed on the cuvette containing the plant is captured at the beginning of the workflow with an extended exposure of **180 ms**. This exposure increases the contrast between black and white code areas, improving software decoding reliability. The decoded QR string is then used to generate a dedicated directory for storing all images associated with the specific plant, ensuring systematic organisation and unambiguous traceability of datasets.

---

## Key Features

- Robotic arm control via **serial communication** with high-level textual commands converted by the **Teensy 4.1 microcontroller**  
- Motorised turntable control with Arduino firmware (Arduino IDE or `arduino-cli`) for **zero positioning** and **continuous rotation**  
- Camera control through **gxipy**, including device detection, exposure control, buffer clearing, and sequential image capture  
- Image acquisition in **8-bit RGB JPEG** format at **4024 × 3036 px**, saved under incremented filenames (e.g. `Img_001.jpg`, `Img_002.jpg`)  
- QR code-based sample identification for **reliable dataset traceability** and **automatic directory creation**  
- Closed-loop synchronisation between robotic positioning and image capture, enabled by **stepper motors with encoders** providing feedback to the Teensy 4.1  

---

## Software Requirements

- **Python**: version 3.9 – 3.11 (Windows environment recommended)  
- **Drivers**:  
  - Valid USB drivers for the industrial camera  
  - Valid drivers for serial communication  
- **Arduino environment**: Arduino IDE or `arduino-cli` for uploading sketches  
- **Daheng Galaxy SDK** (with `gxipy` Python binding and necessary shared libraries)  
- **ZBar system library** (required by `pyzbar` for QR code decoding)  

### Python Packages

Installable with `pip`:  

### Supplied directly with the Galaxy SDK

- `gxipy`  

---

## Local Modules

Two local modules must be present in the same directory:  

- `arduino_upload.py` → provides `upload_arduino` function for flashing Arduino sketches  
- `single_capture.py` → provides `capture_single_image` function for camera operation and frame saving  

---

## Workflow Summary

1. **Zeroing**: Upload the Arduino sketch that sets the turntable to its zero position.  
2. **QR capture**: Move the robotic arm into the QR pose, capture the QR code image at 180 ms exposure, and decode it to generate a target directory.  
3. **Continuous rotation**: Upload the Arduino sketch for continuous rotation of the turntable.  
4. **Image acquisition**: Move the robotic arm through predefined poses. At each pose, images are captured according to exposure and timing parameters.  
5. **Final positioning**: After acquisition, the arm is moved to its final pose, the serial port is closed, and resources are released.  

---

## Data Organisation

- Each dataset is stored in a uniquely generated directory, named according to the decoded QR string and timestamp.  
- Filenames follow a consistent **zero-padded convention** (e.g. `Img_001.jpg`, `Img_002.jpg`), ensuring proper ordering when sorted alphabetically.  
- This organisation guarantees that every dataset is unequivocally linked to the correct plant and is ready for downstream photogrammetric reconstruction.  

---

## Validation and Diagnostics

- **gxipy** → `DeviceManager` can be used to detect connected cameras and verify serial numbers  
- **ZBar** → check by importing `pyzbar` and verifying QR symbol availability  
- **pyserial** → `list_ports` can be used to display available COM devices  
- **Environment variables** → ensure that PATH includes locations of the Galaxy SDK and ZBar libraries  

---

## Applications

This workflow provides a robust pipeline for:  

- **Photogrammetric reconstruction** of plants in three dimensions  
- **Phenotyping studies** requiring accurate, repeatable, and traceable datasets  
- **Automated imaging experiments** demanding reproducibility without manual intervention  

