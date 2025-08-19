# NDVI Post-Processing Pipeline

This folder contains a MATLAB script implementing the **multispectral NDVI workflow** for plant phenotyping.  
The pipeline processes raw RGB and NIR images, applies calibration routines, computes NDVI, and performs plant-specific analysis.

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
   - Computes NDVI = (NIR − Red) / (NIR + Red).
   - Stores the NDVI map in the MATLAB workspace for further use.

6. **Plant segmentation**
   - Loads a pre-trained ResNet50 semantic segmentation model.
   - Generates a binary plant mask.
   - Refines the mask by removing small objects and applying NDVI thresholds to exclude background, soil, and artefacts.

7. **NDVI for plant pixels only**
   - Applies the refined plant mask to retain only valid plant pixels.
   - Computes mean ± standard deviation of NDVI for plant areas.

8. **Visualisation**
   - Displays RGB image with ROI overlays.
   - Displays NDVI maps with jet colour scale fixed to range [-1, 1].

## Requirements

- **MATLAB** (tested with R2023a or later)  
- Toolboxes:
  - Image Processing Toolbox  
  - Deep Learning Toolbox  
- Pre-trained semantic segmentation network:
  - Included in this repository: `/multispectral_workflow/cucSegNDVI_v7.mat`
  - Default path defined in the script:
    ```matlab
    segModelPath = "cucSegNDVI_v7.mat";
    ```
  - Model based on a ResNet50 architecture fine-tuned for plant segmentation.
- Input data:
  - Raw RGB and NIR images in `.bin` format  
  - Calibration folders containing averaged **BIAS**, **DARK**, and **FLAT** frames  

## Notes

- All variables are created in the MATLAB base workspace for debugging.  
- Chip coordinates are fixed but can be adjusted if the test chart position changes.  

