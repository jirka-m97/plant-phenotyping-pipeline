# NDVI Post-Processing Pipeline

This folder provides two variants of the multispectral NDVI workflow script:  

- `MS_pipeline_v8.m` – baseline workflow without automatic segmentation, suitable for general NDVI computation from RGB and NIR data.  
- `MS_pipeline_v8_cuc.m` – extended workflow including a pre-trained semantic segmentation model (DeepLab v3+ with ResNet50 backbone) enabling automatic plant segmentation, currently fine-tuned only for *Cucumis sativus*.  

## Main Steps

1. **RGB image calibration**
   - Reads master BIAS, DARK, and FLAT frames (RGB only).
   - Applies corrections to the raw `.bin` image.
   - Demosaics to RGB and applies white balance using a predefined grey-chip ROI.

2. **NIR image calibration**
   - Reads master BIAS, DARK, and FLAT frames (NIR only).
   - Applies corrections to the raw `.bin` image.
   - Normalises intensity to the RGB red channel using a reference grey-chip ROI.

3. **Automatic test-chart ROI selection**
   - Uses predefined coordinates for the Danes Picta GC5 chart (five grey chips).
   - Overlays chip ROIs for visual inspection and misalignment detection.

4. **Empirical line calibration**
   - Measures average pixel values in each grey-chip ROI.
   - Fits first-order polynomials (per RGB channel, single channel for NIR).
   - Produces reflectance-corrected RGB and NIR images.

5. **NDVI computation**
   - Computes
     \[
     \text{NDVI} = \frac{NIR - Red}{NIR + Red}
     \].
   - Stores the NDVI map in the MATLAB workspace for further use.

6. **Plant segmentation**
   (withnout segmentator)
   - 
   
   (only for *Cucumis sativus*)
   - Loads a pre-trained ResNet50 semantic segmentation model.
   - Generates a binary plant mask.
   - Refines the mask by removing small objects and applying NDVI thresholds to exclude background, soil, and artefacts.

8. **NDVI for plant pixels only**
   - Applies the refined plant mask to retain only valid plant pixels.
   - Computes mean ± standard deviation of NDVI for plant areas.

9. **Visualisation**
   - Displays RGB image with ROI overlays.
   - Displays NDVI maps with jet colour scale fixed to range [-1, 1].

## Requirements

- MATLAB (tested with R2023a or later)  
- Toolboxes:
  - Image Processing Toolbox  
  - Deep Learning Toolbox  
- Pre-trained semantic segmentation network (trained and validated for *Cucumis sativus* datasets):
  - Available via Zenodo: [https://doi.org/10.5281/zenodo.16902271](https://doi.org/10.5281/zenodo.16902271)  
  - After download, place the file into `/multispectral_workflow/`  
  - Default path defined in the script:
    ```matlab
    segModelPath = "cucSegNDVI_v7.mat";
    ```
  - Semantic segmentation model based on a DeepLab v3+ architecture with a ResNet50 backbone, fine-tuned for plant segmentation (*Cucumis sativus*).
- Input data:
  - Raw RGB and NIR images in 8-bit binary format (`.bin`)  
  - Image dimensions: 2048 × 1536 pixels 
  - Calibration frames (BIAS, DARK, FLAT) for both RGB and NIR sensors  
  - Danes Picta GC5 chart for empirical line calibration    

## Notes

- All variables are created in the MATLAB base workspace for debugging.  
- Chip coordinates are fixed but can be adjusted if the test chart position changes.  

