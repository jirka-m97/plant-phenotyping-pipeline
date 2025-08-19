# Non-Destructive Plant Phenotyping Platform

This repository provides software resources for non-destructive plant phenotyping, developed at the **Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague**.  

The codebase supports both **hardware control** and **data analysis** within a multifunctional robotic phenotyping system.

---

## Features

### 1. Robotic Control
- Control algorithms for a robotic arm (serving as a sensor carrier for the multispectral and industrial cameras) and a motorised turntable.  
- Enables flexible sensor positioning and precise, reproducible plant monitoring.  

### 2. Multispectral Analysis
- Control routines for a multispectral camera.  
- Automated data acquisition, storage, and processing of spectral images.  
- NDVI computation for assessing plant physiological status and health.  

### 3. Photogrammetric Analysis
- Control software for an industrial RGB camera.  
- Automated image capture and data storage.  
- Integration with the Metashape API for 3D photogrammetric reconstruction of plants.  

---

## Structure
- `/hardware` – robotic arm and turntable control.  
- `/multispectral` – multispectral imaging, NDVI computation.  
- `/photogrammetry` – industrial camera control, 3D reconstruction workflows.  

---

## License
This project is licensed under the **Apache 2.0 License** – see the [LICENSE](./LICENSE) file for details.

---

## Acknowledgement
This work was developed at the **Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague (UCT Prague)**,  
in collaboration with the **Department of Radioelectronics, Faculty of Electrical Engineering, Czech Technical University in Prague (CTU)**,  
and the **Department of Forensic Experts in Transportation, Faculty of Transportation Sciences, CTU in Prague**.  

---
