# Plant Phenotyping Platform 

This repository hosts software developed for a lab-scale prototype of a multifunctional robotic system** designed for non-destructive plant phenotyping, created at the Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague.  

The apparatus consists of a robotic arm [AR4](https://anninrobotics.com/), a custom-made motorised turntable, a dedicated lighting system (halogen and LED sources), a multispectral camera [FS 3200D 10GE](https://ftp.stemmer-imaging.com/webdavs/docmanager/150153-JAI-FS-3200D-10GE-Datasheet.pdf), and an industrial RGB camera [MER2-1220-32U3C](https://en.daheng-imaging.com/show-106-1997-1.html). These components are integrated into a single platform enabling flexible sensor positioning, reproducible imaging conditions, and the acquisition of complementary spectral and structural datasets.  

The platform combines robotic hardware control with advanced data acquisition and processing workflows. It enables reproducible and scalable monitoring of plant traits using multispectral and photogrammetric approaches. Beyond its technical scope, the system has potential applications in the study of plant interactions with both biotic factors (e.g., microbial biostimulants) and abiotic factors, providing valuable insights into plant health, physiology, and adaptive responses.  

The repository is intended as a resource for researchers and engineers in plant sciences, bioengineering, and precision agriculture, providing modular and extensible code for both laboratory and applied environments.

 ---

## Features

### 1. Robot and Turntable Control
- Algorithms for controlling a robotic arm (serving as a sensor carrier for multispectral and industrial cameras) and a motorised turntable.  
- Provides accurate synchronisation between plant positioning and sensor operation.  
- Ensures flexible and repeatable measurement conditions for a wide range of phenotyping tasks.  

### 2. Multispectral Analysis
- Camera control routines supporting automated image capture, data management, and storage.  
- Processing pipelines for handling multispectral datasets.  
- Implementation of vegetation index (NDVI) computation to assess plant vitality and stress status.  
- Development and implementation of an automatic image segmentation module for reliable separation of plant material from the background prior to analysis.  

### 3. Photogrammetric Analysis
- Software for industrial RGB camera operation and automated image acquisition.  
- Integration with the Metashape API for three-dimensional plant reconstruction, enabling detailed analysis of morphology and growth dynamics.  

---

## Structure
- `/robot_and_turntable_control` – robotic arm and turntable control modules.  
- `/multispectral_workflow` – tools for multispectral imaging, NDVI-based health assessment, and automatic segmentation.  
- `/photogrammetry_workflow` – industrial camera control and 3D reconstruction workflows.  

---

## License
This project is released under the **Apache 2.0 Licence** – see the [LICENSE](./LICENSE) file for details.  

---

## Acknowledgement
Developed at the **Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague (UCT Prague)**,  
in collaboration with the **Department of Radioelectronics, Faculty of Electrical Engineering, Czech Technical University in Prague (CTU)**,  
and the **Department of Forensic Experts in Transportation, Faculty of Transportation Sciences, CTU in Prague**.  

---

## Related Publications
Mach, J., et al., Development of low-cost multifunctional robotic apparatus for high-throughput plant phenotyping. Smart Agricultural Technology, 2024. 9: p. 17. [https://doi.org/10.1016/j.atech.2024.100654](https://doi.org/10.1016/j.atech.2024.100654)

---
