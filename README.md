# Multifunctional platform for plant phenotyping: multispectral and photogrammetric pipelines

This repository contains software developed for a laboratory-scale prototype of a multifunctional robotic platform designed for non-destructive plant phenotyping at the Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague.  

The apparatus integrates a [robotic arm AR4](https://anninrobotics.com/), a custom-built motorised turntable, and a dedicated lighting system combining halogen and LED sources with two complementary imaging devices: a [multispectral camera FS 3200D 10GE](https://ftp.stemmer-imaging.com/webdavs/docmanager/150153-JAI-FS-3200D-10GE-Datasheet.pdf) and an [industrial RGB camera MER2-1220-32U3C](https://en.daheng-imaging.com/show-106-1997-1.html). Together, these components form a unified platform enabling flexible sensor positioning, reproducible imaging conditions, and the acquisition of both spectral and structural datasets. The software provides automated workflows for sensor control, data acquisition, organisation, and post-processing, ensuring synchronised operation of the robotic arm, cameras, and turntable. In this way, a comprehensive software ecosystem has been created and implemented into the developed multifunctional platform.  

Beyond its technical capabilities, the system is applicable to studies of plant interactions with biotic factors such as microbial biostimulants, as well as abiotic factors including light, temperature, or nutrient availability. In this way, the platform provides valuable insights into plant health, physiology, and adaptive responses under controlled experimental conditions.  

The repository is intended as a resource for researchers and engineers in plant sciences, bioengineering, and precision agriculture, offering modular and extensible code suitable for both laboratory research and applied phenotyping environments.

 ---

## Features

### 1. Multispectral analysis
- Multispectral camera control routines enabling automated RGB and NIR image acquisition, data management, and storage.  
- Processing pipelines for handling multispectral datasets.  
- Implementation of vegetation index (NDVI) computation to assess plant vitality and stress status.  
- Implementation of an automatic image segmentation module (Deeplab v3+ with backbone ResNet-50) for reliable separation of plant material from the background prior to analysis.  

### 2. Photogrammetric analysis
- Control algorithms for the robotic arm (serving as a sensor carrier for industrial RGB cameras) and the custom-built motorised turntable.  
- Accurate synchronisation of plant positioning with sensor operation, ensuring consistency across repeated measurements.  
- Flexible sensor positioning within the working space, enabling reproducible measurement conditions across diverse phenotyping tasks.  
- Software for industrial RGB camera operation and automated image acquisition.  
- Integration with [the Metashape API](https://www.agisoft.com/pdf/metashape_python_api_2_0_0.pdf) was employed for three-dimensional reconstruction of plants, enabling detailed analysis of morphology and growth dynamics.  

---

## Structure

- `/multispectral_workflow` – tools for multispectral imaging, automatic image segmentation, and subsequent NDVI-based plant health assessment.  
- `/photogrammetry_workflow` – modules for robotic arm and motorised turntable control, operation of the industrial RGB camera, and workflows for three-dimensional plant reconstruction.  
---

## License
All codes forming this project are distributed under the Apache 2.0 Licence, which allows users to freely use, modify, and redistribute the software for both academic and commercial purposes, provided that proper attribution is given to the original authors. For the complete licence terms, please see the [LICENSE](./LICENSE) file.  

---

## Acknowledgement
Developed at the Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague,  
in collaboration with the Department of Radioelectronics, Faculty of Electrical Engineering, Czech Technical University in Prague,  
and the Department of Forensic Experts in Transportation, Faculty of Transportation Sciences, Czech Technical University in Prague.  

---

## Applications

The multifunctional platform integrates multispectral imaging and photogrammetric reconstruction, enabling a wide range of experimental and applied use cases:

### Multispectral analysis
- **Plant health monitoring** – non-destructive detection of physiological stress through vegetation indices such as NDVI.  
- **Assessment of abiotic stress responses** – evaluation of the influence of light quality, nutrient regimes, temperature, and water availability on plant vitality.  
- **Biotic interaction studies** – monitoring the effects of microbial biostimulants or pathogens on leaf reflectance characteristics.  
- **High-throughput screening** – systematic acquisition of spectral datasets under controlled and reproducible imaging conditions.  

### 3D photogrammetry
- **Morphological characterisation** – precise reconstruction of plant geometry for quantifying height, volume, and surface area.  
- **Growth dynamics** – temporal monitoring of plant structure to assess developmental stages and stress-induced changes.  
- **Phenotyping under controlled conditions** – reproducible, automated acquisition of structural datasets without manual intervention.  
- **Quality control and validation** – use of reference markers and calibration procedures for metric accuracy and reproducibility.  
- **Transferable workflows** – applicability beyond plant sciences, e.g. technical inspection of small components, materials testing, or educational demonstrations of photogrammetric methods.  

--- 

We also acknowledge the technical support provided by  
- [JAI Support](https://support.jai.com/hc/en-us) for the multispectral camera control, and  
- [Agisoft Metashape Support](https://www.agisoftmetashape.com/support/?srsltid=AfmBOopHtxRqLW6budwORrpX34QVnSkSQnkvERqKRR9fFE1lLZ1-gCzI) for guidance on setting advanced parameters of the evaluation process in photogrammetric workflows.  

---

## Related publications
Mach, J., et al., Development of low-cost multifunctional robotic apparatus for high-throughput plant phenotyping. Smart Agricultural Technology, 2024. 9: p. 17. [https://doi.org/10.1016/j.atech.2024.100654](https://doi.org/10.1016/j.atech.2024.100654)

---
