# Plant phenotyping platform 

This repository contains software developed for a lab-scale prototype of a multifunctional robotic system for non-destructive plant phenotyping, created at the Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague.  

The apparatus comprises a [robotic arm AR4](https://anninrobotics.com/), a custom-made motorised turntable, a dedicated lighting system combining halogen and LED sources, a [multispectral camera FS 3200D 10GE](https://ftp.stemmer-imaging.com/webdavs/docmanager/150153-JAI-FS-3200D-10GE-Datasheet.pdf), and an [industrial RGB camera MER2-1220-32U3C](https://en.daheng-imaging.com/show-106-1997-1.html). These components are integrated into a unified platform that allows flexible sensor positioning, standardised imaging conditions, and the acquisition of complementary spectral and structural datasets. The system also provides workflows for data evaluation and post-processing, ensuring robust interpretation of multispectral and photogrammetric outputs. Beyond its technical capabilities, the system offers potential applications in studying plant interactions with both biotic factors (e.g., microbial biostimulants) and abiotic factors, thereby providing valuable insights into plant health, physiology, and adaptive responses. 

The repository is intended as a resource for researchers and engineers in plant sciences, bioengineering, and precision agriculture, providing modular and extensible code for both laboratory and applied environments.

 ---

## Features

### 1. Robot and turntable control
- Control algorithms for the robotic arm (serving as a sensor carrier for multispectral and industrial cameras) and the custom-built motorised turntable.
- Accurate synchronisation of plant positioning with sensor operation, ensuring consistency across repeated measurements.
- Flexible sensor positioning within the working space, enabling reproducible measurement conditions across diverse phenotyping tasks.

### 2. Multispectral analysis
- Multispectral camera control routines enabling automated RGB and NIR image acquisition, data management, and storage.
- Processing pipelines for handling multispectral datasets.  
- Implementation of vegetation index (NDVI) computation to assess plant vitality and stress status.  
- Implementation of an automatic image segmentation module (Deeplab v3+ with backbone ResNet-50) for reliable separation of plant material from the background prior to analysis.  

### 3. Photogrammetric analysis
- Software for industrial RGB camera operation and automated RGB image acquisition.  
- Integration with [the Metashape API](https://www.agisoft.com/pdf/metashape_python_api_2_0_0.pdf) for three-dimensional plant reconstruction, enabling detailed analysis of morphology and growth dynamics.  

---

## Structure
- `/robot_and_turntable_control` – robotic arm and turntable control modules.  
- `/multispectral_workflow` – tools for multispectral imaging, NDVI-based health assessment, and automatic segmentation.  
- `/photogrammetry_workflow` – industrial RGB camera control and 3D reconstruction workflows.  

---

## License
This project is released under the Apache 2.0 Licence – see the [LICENSE](./LICENSE) file for details.  

---

## Acknowledgement
Developed at the Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague,  
in collaboration with the Department of Radioelectronics, Faculty of Electrical Engineering, Czech Technical University in Prague,  
and the Department of Forensic Experts in Transportation, Faculty of Transportation Sciences, Czech Technical University in Prague.  

We also acknowledge the technical support provided by  
- [JAI Support](https://support.jai.com/hc/en-us) for the multispectral camera control, and  
- [Agisoft Metashape Support](https://www.agisoftmetashape.com/support/?srsltid=AfmBOopHtxRqLW6budwORrpX34QVnSkSQnkvERqKRR9fFE1lLZ1-gCzI) for guidance on setting advanced parameters of the evaluation process in photogrammetric workflows.  

---

## Related Publications
Mach, J., et al., Development of low-cost multifunctional robotic apparatus for high-throughput plant phenotyping. Smart Agricultural Technology, 2024. 9: p. 17. [https://doi.org/10.1016/j.atech.2024.100654](https://doi.org/10.1016/j.atech.2024.100654)

---
