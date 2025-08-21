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

```bash
pip install opencv-python pillow pyserial pyzbar numpy
