# MS camera control and data acquisition
## Core functionality

 - Automatic device detection and connection via the GigE Vision interface.
 - Stream negotiation, packet size optimisation, and buffer allocation.
 - Configuration of camera parameters (resolution, exposure time, frame rate, acquisition mode).
 - Acquisition of multispectral images with alternating retrieval from RGB and NIR sensors.
   - RGB sensor (Source0)
   - NIR sensor (Source1)
 - Handling of multiple payload formats, including Pleora-compressed data.
 - Saving raw binary images (.bin) for subsequent processing (RGB and NIR separately).
 - Real-time diagnostic output (frame rate, bandwidth, compression ratio).
 - Acquisition of calibration frames (BIAS, DARK, FLAT) for both sensors.
 - Output plant images are stored as .bin files (2048 × 1536 px) in the specified directory.

## Calibration frames

- BIAS: 1 µs exposure, lens shuttered (RGB and NIR).
- DARK: 985 µs (RGB) and 2850 µs (NIR), lens shuttered.
- FLAT: identical exposure settings as DARK, lens uncovered.
- 20 images per category were acquired at full resolution (2048 × 1536 px), consistent with object images (plants).

## Requirements

- Requires Python 3.x, Pleora eBUS SDK, OpenCV, and NumPy.
- Ensure the Pleora eBUS SDK and drivers are installed on the host system.
- Run the script to acquire paired RGB and NIR images.
  
---
# MS data post-processing pipeline
 
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
   - Computes NDVI as (NIR − Red) / (NIR + Red).
   - Stores the NDVI map in the MATLAB workspace for subsequent processing.

6. **Plant segmentation (manual, without segmentator – applicable to *Cucumis sativus* L., *Solanum lycopersicum* L., *Lactuca sativa* L., and potentially other untested plant species)**
   - Creates a binary mask using the MATLAB Image Segmenter app (Graph Cut tool).
   - Script: MS_pipeline_v8.m

7. **Plant segmentation (automated, with segmentator – *Cucumis sativus* only)**
   - Loads the pre-trained ResNet-50 semantic segmentation model (cucSegNDVI_v7.mat).
   - Generates a binary plant mask.
   - Refines the mask by removing small objects and applying NDVI-based thresholds to exclude background, soil, and artefacts.
   - Script: MS_pipeline_v8_cuc.m

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

   - All variables are created in the MATLAB base workspace (useful for debugging).
   - Chip coordinates are fixed by default but can be adjusted if the test chart position changes.
   - The script segmentator_training.m includes an additional routine for retraining the automated segmentation model.


