# Multifunctional Platform for Plant Phenotyping: Multispectral and Photogrammetric Pipelines

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20080759.svg)](https://doi.org/10.5281/zenodo.20080759)

This repository contains software developed for a laboratory-scale prototype of a multifunctional robotic platform designed for non-destructive plant phenotyping at the Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague.

The apparatus integrates a [robotic arm AR4](https://anninrobotics.com/), a custom-built motorised turntable, and a dedicated lighting system combining halogen and LED sources with two complementary imaging devices: a [multispectral camera FS 3200D 10GE](https://ftp.stemmer-imaging.com/webdavs/docmanager/150153-JAI-FS-3200D-10GE-Datasheet.pdf) and an [industrial RGB camera MER2-1220-32U3C](https://en.daheng-imaging.com/show-106-1997-1.html). Together, these components form a unified platform enabling flexible sensor positioning, reproducible imaging conditions, and the acquisition of both spectral and structural datasets. The software provides automated workflows for sensor control, data acquisition, organisation, and post-processing, ensuring synchronised operation of the robotic arm, cameras, and turntable.

Beyond its technical capabilities, the system is applicable to studies of plant interactions with biotic factors such as microbial biostimulants, as well as abiotic factors including light, temperature, or nutrient availability. The platform thereby provides valuable insights into plant health, physiology, and adaptive responses under controlled experimental conditions.

The repository is intended as a resource for researchers and engineers in plant sciences, bioengineering, and precision agriculture, offering modular and extensible code suitable for both laboratory research and applied phenotyping environments.

---

## Features

### 1. Multispectral analysis
- Multispectral camera control routines enabling automated RGB and NIR image acquisition, data management, and storage.
- Processing pipelines for handling multispectral datasets.
- Implementation of vegetation index (NDVI) computation to assess plant vitality and stress status.
- Implementation of an automatic image segmentation module (DeepLab v3+ with ResNet-50 backbone) for reliable separation of plant material from the background prior to analysis.

### 2. Photogrammetric analysis
- Control algorithms for the robotic arm (serving as a sensor carrier for industrial RGB cameras) and the custom-built motorised turntable.
- Accurate synchronisation of plant positioning with sensor operation, ensuring consistency across repeated measurements.
- Flexible sensor positioning within the working space, enabling reproducible measurement conditions across diverse phenotyping tasks.
- Software for industrial RGB camera operation and automated image acquisition.
- Integration with the [Metashape API](https://www.agisoft.com/pdf/metashape_python_api_2_0_0.pdf) for three-dimensional reconstruction of plants, enabling detailed analysis of morphology and growth dynamics.

---

## Repository structure

```
plant-phenotyping-pipeline/
├── multispectral_pipeline/   # Multispectral imaging, segmentation, and NDVI-based health assessment
├── photogrammetry_pipeline/  # Robotic arm control, turntable control, RGB camera, and 3D reconstruction
├── LICENSE
└── README.md
```

---

## Requirements

### Multispectral pipeline
- MATLAB R2021b or later
- Deep Learning Toolbox
- Computer Vision Toolbox
- Deep Learning Toolbox Model for ResNet-50 Network (Add-On)
- [JAI SDK](https://www.jai.com/support-software) (for multispectral camera control)

### Photogrammetric pipeline
- Python 3.8 or later
- [Agisoft Metashape Professional](https://www.agisoft.com/downloads/installer/) 
- [Daheng Galaxy SDK](https://en.daheng-imaging.com/list-57-1.html) (for RGB camera control)

---

## Quick start

1. Clone the repository:
   ```bash
   git clone https://github.com/jirka-m97/plant-phenotyping-pipeline.git
   ```

2. Navigate to the pipeline of interest:
   ```bash
   cd multispectral_pipeline   # or photogrammetry_pipeline
   ```

3. Follow the instructions in the respective `README.md` file within each subfolder.

> **Note:** The trained segmentation model (`cucSegNDVI_v7.mat`) and the source dataset are available on [Zenodo](https://zenodo.org/records/20080759).

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

## Acknowledgement

Developed at the Laboratory of Bioengineering, Institute of Biotechnology, University of Chemistry and Technology Prague,
in collaboration with the Department of Radioelectronics, Faculty of Electrical Engineering, Czech Technical University in Prague,
and the Department of Forensic Experts in Transportation, Faculty of Transportation Sciences, Czech Technical University in Prague.

We also acknowledge the technical support provided by:
- [JAI Support](https://support.jai.com/hc/en-us) for the multispectral camera control, and
- [Agisoft Metashape Support](https://www.agisoft.com/support/) for guidance on setting advanced parameters in photogrammetric workflows.

---

## Related publications

Mach, J., *et al*. Development of low-cost multifunctional robotic apparatus for high-throughput plant phenotyping. *Smart Agricultural Technology*, 2024, 9, 17. [https://doi.org/10.1016/j.atech.2024.100654](https://doi.org/10.1016/j.atech.2024.100654)

Mach, J., *et al*. Implementation of an SfM-MVS-based photogrammetry approach for detailed 3D reconstruction of plants. *Plant Methods*, 2025, 21, 1. [https://doi.org/10.21203/rs.3.rs-7178236/v1](https://doi.org/10.21203/rs.3.rs-7178236/v1)

---

## License

All code in this repository is distributed under the Apache 2.0 Licence, which permits free use, modification, and redistribution for both academic and commercial purposes, provided that proper attribution is given to the original authors. For the complete licence terms, please see the [LICENSE](./LICENSE) file.
