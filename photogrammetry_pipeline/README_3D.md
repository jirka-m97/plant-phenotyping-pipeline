# Photogrammetric analysis pipeline

This repository contains software for a complete photogrammetric workflow divided into two phases:

- **Phase 1 — Hardware control and data acquisition** (`photogrammetry_analysis.py`) — automates robotic positioning, camera control, image capture, and QR-based sample identification.
- **Phase 2 — Image data processing and 3D model generation** (`Photogram3D.py`, `Plant3D.py`) — handles dataset monitoring, photogrammetric reconstruction, model cropping, post-processing, and morphometric analysis using the Agisoft Metashape Python API.

The system was designed for controlled imaging of plants with the purpose of generating structured datasets suitable for three-dimensional reconstruction and advanced phenotyping studies.

---

## Hardware Control and Data Acquisition

---

## Overview

The workflow coordinates three main hardware components:

- Robotic arm controlled by a Teensy 4.1 microcontroller through serial communication
- Motorised turntable operated by Arduino sketches for both zero positioning and continuous rotation
- Industrial camera controlled through the Daheng Galaxy SDK (`gxipy`), capturing sequential images in 8-bit RGB format at a resolution of 4024 × 3036 pixels

A QR code placed on the plant pot (cultivation vessel) containing the plant is captured at the beginning of the workflow with an extended exposure of 180 ms. This exposure increases the contrast between black and white code areas, improving software decoding reliability. The decoded QR string is then used to generate a dedicated directory for storing all images associated with the specific plant, ensuring systematic organisation and unambiguous traceability of datasets.

---

## Key features

- Robotic arm control via serial communication with high-level textual commands converted by the Teensy 4.1 microcontroller
- Motorised turntable control with Arduino firmware (Arduino IDE or `arduino-cli`) for zero positioning and continuous rotation
- Camera control through `gxipy`, including device detection, exposure control, buffer clearing, and sequential image capture
- Image acquisition in 8-bit RGB JPEG format at 4024 × 3036 px, saved under incremented filenames (e.g. `Img_001.jpg`, `Img_002.jpg`)
- QR code-based sample identification for reliable dataset traceability and automatic directory creation
- Optional bypass of QR-based identification via the `USE_QR` flag — when set to `False`, images are saved directly into the base output directory without QR capture or folder creation
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
- must be present in the same directory 

### Local modules
- `arduino_upload.py` → provides the function `upload_arduino` for flashing Arduino sketches

### Arduino scripts
- `turntable_continuous_rotation.ino` → Arduino sketch for continuous rotation of the turntable
- `turntable_zero_position.ino` → Arduino sketch for setting the turntable to its zero position
- `turntable_markers.txt` → coordinates of 16 circular 12-bit coded reference markers placed on the turntable lid, used for camera alignment and workspace scaling in

### Metashape calibration XML file
- `calib_calibrationField.xml` → XML file containing intrinsic camera calibration parameters, used for improved alignment accuracy in Plant3D.py

Pretrained poses of AR4 robotic arm
- `P_QR`, `P_redset_120`, `P_fullset_360`, `P_end` → pre-recorded robot pose sequences stored in binary format (pickle), defining the joint positions of the robotic arm for QR capture, image acquisition, and final positioning. The poses were taught using the AR4 graphical user interface provided by the manufacturer (Annin Robotics).
---

## Workflow summary

1. **Zeroing:** Upload the Arduino sketch that sets the turntable to its zero position.
2. **QR capture:** Move the robotic arm into the QR pose, capture the QR code image at 180 ms exposure, and decode it to generate a target directory. This step can be skipped by setting `USE_QR = False` in the script, in which case images are saved directly into the base output directory.
3. **Continuous rotation:** Upload the Arduino sketch for continuous rotation of the turntable.
4. **Image acquisition:** Move the robotic arm through predefined poses. At each pose, images are captured according to exposure and timing parameters.
5. **Final positioning:** After acquisition, the arm is moved to its final pose, the serial port is closed, and resources are released.

---

## Data organisation

- Each dataset is stored in a uniquely generated directory, named according to the decoded QR string and timestamp.
- Filenames follow a consistent zero-padded convention (e.g. `Img_001.jpg`, `Img_002.jpg`), ensuring proper ordering when sorted alphabetically.
- This organisation guarantees that every dataset is unequivocally linked to the correct plant and is ready for downstream photogrammetric reconstruction.

---

## Validation and diagnostics

- `gxipy` → `DeviceManager` can be used to detect connected cameras and verify serial numbers
- ZBar → check by importing `pyzbar` and verifying QR symbol availability
- `pyserial` → `list_ports` can be used to display available COM devices
- Environment variables → ensure that PATH includes locations of the Galaxy SDK and ZBar libraries

---

## 3D Reconstruction and Data Processing Pipeline

---

This workflow provides a **fully automated and robust pipeline for photogrammetric data processing**, designed to minimise manual intervention while ensuring reproducibility and accuracy when handling large image datasets.

The pipeline consists of two cooperating console applications:

- **Photogram3D.py** – monitors the input directory, verifies dataset completeness, and initiates processing.
- **Plant3D.py** – performs photogrammetric reconstruction using the Agisoft Metashape Python API and supporting libraries.

All key parameters are defined in a central configuration file `config.json`, allowing flexible adjustment of processing conditions without modifying the codebase.

---

### Key features
- **Automated data monitoring** – verifies the number of subfolders and images in the input directory.
- **Safe execution** – processing starts only once datasets are confirmed complete.
- **Support for external camera calibration** – improved accuracy via imported XML calibration file `calib_calibrationField.xml`.
- **Reference-based alignment** – use of coded markers and known coordinates for metric anchoring.
- **Automated model cropping** – cylindrical cropping to remove the plant pot (cultivation vessel) and background artefacts.
- **Integrated post-processing** – smoothing, noise removal, hole filling.
- **Morphometric analysis** – calculation of height, surface area, and volume.
- **Automated reports and notifications** – structured outputs and webhook alerts (e.g. Discord).

---

### Architecture

#### Photogram3D.py
- Built with standard Python libraries (`os`, `time`, `json`, `subprocess`).
- Continuously monitors the input directory and checks:
  - `FOLDER_AMOUNT` – required number of subfolders.
  - `IMAGE_AMOUNT` – exact number of images per subfolder.
- Once the conditions are satisfied, **Plant3D.py** is launched automatically.

#### Plant3D.py
- Powered by the **Agisoft Metashape Python API** and modules including `json`, `os`, `math`, `traceback`, and `requests`.
- Processing steps:
  1. **Load configuration** and validate parameters.
  2. **Camera calibration** – import XML with lens parameters.
  3. **Image alignment** – generate sparse cloud and estimate camera poses.
  4. **Reference-based anchoring** – apply metric reference markers.
  5. **Depth map and dense cloud generation**.
  6. **Mesh reconstruction** with optional tuning (`TWEAK_1`, `TWEAK_2`).
  7. **Cylindrical cropping** – remove plant pot (cultivation vessel) geometry and background.
  8. **Post-processing** – smoothing, filtering, hole filling.
  9. **Morphometrics** – compute object height, surface area, volume.
  10. **Export results** and send **notifications**.

---

## Applications

- **Plant phenotyping**
  - Generation of accurate 3D reconstructions for the quantitative assessment of growth, morphology, and structural variation.
  - Automated, reproducible image acquisition in laboratory environments with reduction of operator bias and manual workload.
  - High-throughput acquisition of plant traits for studying the effects of biotic and abiotic stress factors, as well as for biostimulant and biopesticide development.

- **Quality control and technical inspection**
  - Consistent 3D reconstruction of objects with known geometry to validate system calibration and reproducibility.
  - Adaptability to non-biological specimens, enabling applications in engineering, materials testing, and industrial inspection.

- **Educational and research infrastructure**
  - Demonstration of end-to-end photogrammetry workflows in academic teaching.
  - Establishment of reproducible pipelines in multi-user laboratories where standardisation is essential.
