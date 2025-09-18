# Photogrammetric analysis pipeline

This repository contains the Python script `fotogramm_analysis.py`, which automates a complete photogrammetric acquisition workflow by integrating robotic positioning, camera control, automated image capture, and QR-based sample identification. The system was designed for controlled imaging of plants with the purpose of generating structured datasets suitable for three-dimensional reconstruction and advanced phenotyping studies.

---

## Overview

The workflow coordinates three main hardware components:

- Robotic arm controlled by a Teensy 4.1 microcontroller through serial communication  
- Motorised turntable operated by Arduino sketches for both zero positioning and continuous rotation  
- Industrial camera controlled through the Daheng Galaxy SDK (`gxipy`), capturing sequential images in 8-bit RGB format at a resolution of 4024 × 3036 pixels  

A QR code placed on the cuvette containing the plant is captured at the beginning of the workflow with an extended exposure of 180 ms. This exposure increases the contrast between black and white code areas, improving software decoding reliability. The decoded QR string is then used to generate a dedicated directory for storing all images associated with the specific plant, ensuring systematic organisation and unambiguous traceability of datasets.

---

## Key features

- Robotic arm control via serial communication with high-level textual commands converted by the Teensy 4.1 microcontroller
- Motorised turntable control with Arduino firmware (Arduino IDE or `arduino-cli`) for zero positioning and continuous rotation  
- Camera control through gxipy, including device detection, exposure control, buffer clearing, and sequential image capture  
- Image acquisition in 8-bit RGB JPEG format at 4024 × 3036 px, saved under incremented filenames (e.g. `Img_001.jpg`, `Img_002.jpg`)  
- QR code-based sample identification for reliable dataset traceability and automatic directory creation  
- Closed-loop synchronisation between robotic positioning and image capture, enabled by stepper motors with encoders providing feedback to the Teensy 4.1  

---

## Software requirements

- Python: version 3.9 – 3.11 (Windows environment recommended)  
- Drivers:  
  - Valid USB drivers for the industrial camera  
  - Valid drivers for serial communication  
- Arduino environment: Arduino IDE or `arduino-cli` for uploading sketches  
- Daheng Galaxy SDK (with `gxipy` Python binding and necessary shared libraries)  
- ZBar system library (required by `pyzbar` for QR code decoding)  

### Python packages

Installable with `pip`:  
- `opencv-python` (image handling)
- `pillow` (image input/output)
- `pyserial` (serial communication)
- `pyzbar` (QR code decoding, requires ZBar installed)
- `numpy` (numerical backend)

### Supplied directly with the Galaxy SDK

- `gxipy`  

---
## Local modules and external scripts

Two local modules and two external Arduino sketches must be present in the same directory  

- arduino_upload.py → provides the function upload_arduino for flashing Arduino sketches  
- single_capture.py → provides the function capture_single_image for camera operation and frame saving  (the folder "Fotogram_source_data" must be created)  
- turntable_continuous.ino → Arduino sketch for continuous rotation of the turntable  
- turntable_zero.ino → Arduino sketch for setting the turntable to its zero position

---

## Workflow summary

1. Zeroing: Upload the Arduino sketch that sets the turntable to its zero position.  
2. QR capture: Move the robotic arm into the QR pose, capture the QR code image at 180 ms exposure, and decode it to generate a target directory.  
3. Continuous rotation: Upload the Arduino sketch for continuous rotation of the turntable.  
4. Image acquisition: Move the robotic arm through predefined poses. At each pose, images are captured according to exposure and timing parameters.  
5. Final positioning: After acquisition, the arm is moved to its final pose, the serial port is closed, and resources are released.  

---

## Data organisation

- Each dataset is stored in a uniquely generated directory, named according to the decoded QR string and timestamp.  
- Filenames follow a consistent zero-padded convention (e.g. `Img_001.jpg`, `Img_002.jpg`), ensuring proper ordering when sorted alphabetically.  
- This organisation guarantees that every dataset is unequivocally linked to the correct plant and is ready for downstream photogrammetric reconstruction.  

---

## Validation and diagnostics

- gxipy → `DeviceManager` can be used to detect connected cameras and verify serial numbers  
- ZBar → check by importing `pyzbar` and verifying QR symbol availability  
- pyserial → `list_ports` can be used to display available COM devices  
- Environment variables → ensure that PATH includes locations of the Galaxy SDK and ZBar libraries  

---

## Image Data Post-Processing Pipeline

This workflow provides a **fully automated and robust pipeline for photogrammetric data processing**, designed to minimise manual intervention while ensuring reproducibility and accuracy when handling large image datasets.  

The pipeline consists of two cooperating console applications:  

- **Photogram3D** – monitors the input directory, verifies dataset completeness, and initiates processing.  
- **Plant3D** – performs photogrammetric reconstruction using the Agisoft Metashape Python API and supporting libraries.  

All key parameters are defined in a central configuration file `config.json`, allowing flexible adjustment of processing conditions without modifying the codebase.  

---

### Key Features
- **Automated data monitoring** – verifies the number of subfolders and images in the input directory.  
- **Safe execution** – processing starts only once datasets are confirmed complete.  
- **Support for external camera calibration** – improved accuracy via imported XML calibration file `calib_calibrationField.xml`.  
- **Reference-based alignment** – use of coded markers and known coordinates for metric anchoring.  
- **Automated model cropping** – cylindrical cropping to remove artefacts (e.g. cuvettes).  
- **Integrated post-processing** – smoothing, noise removal, hole filling.  
- **Morphometric analysis** – calculation of height, surface area, and volume.  
- **Automated reports and notifications** – structured outputs and webhook alerts (e.g. Discord).  

---

### Architecture

#### Photogram3D
- Built with standard Python libraries (`os`, `time`, `json`, `subprocess`).  
- Continuously monitors the input directory and checks:  
  - `FOLDER_AMOUNT` – required number of subfolders.  
  - `IMAGE_AMOUNT` – exact number of images per subfolder.  
- Once the conditions are satisfied, **Plant3D** is launched automatically.  

#### Plant3D
- Powered by the **Agisoft Metashape Python API** and modules including `json`, `os`, `math`, `traceback`, and `requests`.  
- Processing steps:  
1. **Load configuration** and validate parameters.  
1. **Camera calibration** – import XML with lens parameters.  
1. **Image alignment** – generate sparse cloud and estimate camera poses.  
1. **Reference-based anchoring** – apply metric reference markers.  
1. **Depth map and dense cloud generation**.  
1. **Mesh reconstruction** with optional tuning (`TWEAK_1`, `TWEAK_2`).  
1. **Cylindrical cropping** – remove cuvette geometry and background.  
1. **Post-processing** – smoothing, filtering, hole filling.  
1. **Morphometrics** – compute object height, surface area, volume.  
1. **Export results** and send **notifications**.  


## Applications

This workflow provides a robust pipeline for:  

- Close-range photogrammetric reconstruction of plants in the context of plant phenotyping  
- Phenotyping studies requiring accurate, repeatable, and traceable datasets, including the study of the influence of biotic or abiotic factors on plant growth  
- Automated imaging experiments demanding reproducibility without manual intervention  
 

