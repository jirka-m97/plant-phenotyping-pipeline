% =========================================================================
%  tif_4band.m  —  STEP 4: Merge RGB + NIR into a four-band TIFF
% =========================================================================
%  Purpose:
%    Combines a pair of reflectance frames (3-band RGB + 1-band NIR) into a
%    single four-band composite TIFF (R, G, B, NIR) that serves as the input
%    for the photogrammetric reconstruction in Agisoft Metashape.
%
%  Input:
%    Img_<N>_reflectance_RGB.tif  +  Img_<N>_reflectance_NIR.tif
%
%  Output:
%    Img_<N>_reflectance.tif  (4 bands, 32-bit float)
%    The name without the _RGB suffix is also the camera "label" in Metashape;
%    NDVI_3D_model.m uses it to match cameras with their images.
%
%  Next step: photogrammetry in Metashape -> NDVI_3D_model.m
% =========================================================================

clc;
clear;

%% 1. PATHS — EDIT BEFORE EVERY RUN
input_folder  = "<PATH_TO_INPUT_FOLDER>";
output_folder = "<PATH_TO_OUTPUT_FOLDER>";

if ~exist(output_folder, 'dir')
    mkdir(output_folder);
end

%% 2. FIND THE FRAMES
rgb_files = dir(fullfile(input_folder, 'Img_*_reflectance_RGB.tif'));
fprintf('RGB frames found: %d\n', length(rgb_files));

%% 3. MAIN LOOP
for i = 1:length(rgb_files)

    rgb_name = rgb_files(i).name;
    nir_name = strrep(rgb_name, 'RGB', 'NIR');

    rgb_path = fullfile(input_folder, rgb_name);
    nir_path = fullfile(input_folder, nir_name);

    if ~exist(nir_path, 'file')
        fprintf('Missing NIR for: %s\n', rgb_name);
        continue;
    end

    rgb = imread(rgb_path);
    nir = imread(nir_path);

    % The NIR image must be single-band
    if size(nir, 3) > 1
        nir = nir(:,:,1);
    end

    if size(rgb,1) ~= size(nir,1) || size(rgb,2) ~= size(nir,2)
        fprintf('Resolution mismatch: %s\n', rgb_name);
        continue;
    end

    % Stack into a four-band image: R, G, B, NIR
    img4 = single(cat(3, rgb(:,:,1), rgb(:,:,2), rgb(:,:,3), nir));

    % Name without the _RGB suffix
    out_name = strrep(rgb_name, '_RGB', '');
    out_path = fullfile(output_folder, out_name);

    % --- Write the four-band TIFF (32-bit float, uncompressed) ---
    % The 4th band (NIR) is flagged as an ExtraSample to keep the TIFF valid
    tagstruct = struct();
    tagstruct.ImageLength         = size(img4, 1);
    tagstruct.ImageWidth          = size(img4, 2);
    tagstruct.SamplesPerPixel     = 4;
    tagstruct.BitsPerSample       = 32;
    tagstruct.SampleFormat        = Tiff.SampleFormat.IEEEFP;
    tagstruct.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
    tagstruct.Photometric         = Tiff.Photometric.RGB;
    tagstruct.Compression         = Tiff.Compression.None;
    tagstruct.ExtraSamples        = Tiff.ExtraSamples.Unspecified;

    t = Tiff(out_path, 'w');
    t.setTag(tagstruct);
    t.write(img4);
    t.close();

    fprintf('%d/%d: %s\n', i, length(rgb_files), out_name);
end

fprintf('\nDone.\n');
