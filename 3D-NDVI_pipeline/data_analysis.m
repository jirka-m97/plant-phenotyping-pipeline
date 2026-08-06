% =========================================================================
%  data_analysis.m  —  STEP 2: Batch conversion of raw frames to reflectance
% =========================================================================
%  Purpose:
%    Batch-process every RGB+NIR frame pair of the plant in a folder.
%
%  Pipeline:
%    raw (.bin) -> bias/dark/flat -> demosaic -> WB -> OECF coefficients
%               -> reflectance [0-1] -> 32-bit float TIFF
%
%  Input:
%    - Img_*_RGB.bin + Img_*_NIR.bin in input_folder
%    - .mat file with the calibration coefficients from lin_reg_coef.m
%    - Bias / Dark / Flat folders
%
%  Output:
%    - <input_folder>\reflectance_output\*_reflectance_RGB.tif  (3 bands, float32)
%    - <input_folder>\reflectance_output\*_reflectance_NIR.tif  (1 band,  float32)
%
%  Next step: rename.m (only when merging several sets) -> tif_4band.m
% =========================================================================

clc;
clear;
close all;

%% 1. PATHS — EDIT BEFORE EVERY RUN
% Folder holding the raw (.bin) frames of the plant
input_folder = "<PATH_TO_PLANT_IMAGES>";

% Calibration coefficients produced by lin_reg_coef.m
mat_file_path = "<PATH_TO_CALIBRATION_COEFFICIENTS>";

% Calibration frames (bias / dark / flat) — shared by the RGB and NIR sensor
folder_bias = "<PATH_TO_BIAS_IMAGES>";
folder_dark = "<PATH_TO_DARK_IMAGES>";
folder_flat = "<PATH_TO_FLAT_IMAGES>";

% Raw frame parameters
width          = 2048;
height         = 1536;
bit_depth      = 'uint8';
file_extension = '*.bin';

% The output folder is created automatically next to the input folder
output_folder = fullfile(input_folder, "reflectance_output");
if ~exist(output_folder, 'dir')
    mkdir(output_folder);
end

%% 2. LOAD CALIBRATION COEFFICIENTS
load(mat_file_path);

% The coefficient struct is located by its "_koefs" suffix (see lin_reg_coef.m)
workspace_vars = whos('*_koefs');
if isempty(workspace_vars)
    error('No coefficient struct with the _koefs suffix was found in the .mat file.');
end
koefs = eval(workspace_vars(1).name);

% Verify that the .mat file also carries the WB coefficients
if ~isfield(koefs, 'WB_g') || ~isfield(koefs, 'WB_b') || ~isfield(koefs, 'WB_nir')
    error(['File "%s" does not contain the WB coefficients (WB_g, WB_b, WB_nir).\n' ...
           'Re-run the calibration script lin_reg_coef.m and save a new .mat file.'], mat_file_path);
end

% White balance coefficients
wb_g   = koefs.WB_g;
wb_b   = koefs.WB_b;
wb_nir = koefs.WB_nir;

% OECF coefficients: reflectance [%] = gain * value + bias
gain_r   = koefs.R(1);      bias_r       = koefs.R(2);
gain_g   = koefs.G(1);      bias_g       = koefs.G(2);
gain_b   = koefs.B(1);      bias_b       = koefs.B(2);
gain_nir = koefs.NIR(1);    bias_nir_val = koefs.NIR(2);

%% 3. RADIOMETRIC MASTERS — RGB
fprintf('Loading radiometric masters for RGB...\n');

master_bias = load_master(folder_bias, file_extension, 'RGB', width, height, bit_depth);
master_dark = load_master(folder_dark, file_extension, 'RGB', width, height, bit_depth, master_bias);
master_flat = load_master(folder_flat, file_extension, 'RGB', width, height, bit_depth, master_dark);

%% 4. RADIOMETRIC MASTERS — NIR
fprintf('Loading radiometric masters for NIR...\n');

master_bias_nir = load_master(folder_bias, file_extension, 'NIR', width, height, bit_depth);
master_dark_nir = load_master(folder_dark, file_extension, 'NIR', width, height, bit_depth, master_bias_nir);
master_flat_nir = load_master(folder_flat, file_extension, 'NIR', width, height, bit_depth, master_dark_nir);

%% 5. FIND THE FRAMES
rgb_files = dir(fullfile(input_folder, '*RGB*.bin'));
if isempty(rgb_files)
    error('No RGB files (*.bin) were found in folder "%s".', input_folder);
end
fprintf('\nFound %d RGB frames to process.\n\n', length(rgb_files));

%% 6. MAIN LOOP
for k = 1:length(rgb_files)

    rgb_filename = rgb_files(k).name;
    rgb_path     = fullfile(input_folder, rgb_filename);

    % The matching NIR frame is derived from the RGB file name
    nir_filename = strrep(rgb_filename, 'RGB', 'NIR');
    nir_path     = fullfile(input_folder, nir_filename);

    if ~isfile(nir_path)
        warning('No NIR file found for: %s - frame skipped.', rgb_filename);
        continue;
    end

    fprintf('[%d/%d] Processing: %s\n', k, length(rgb_files), rgb_filename);

    % --- RGB: read ---
    fid = fopen(rgb_path);
    image_data = fread(fid, width * height, 'uint8');
    fclose(fid);
    I = reshape(image_data, [width, height])';

    % --- RGB: bias / dark / flat correction ---
    I_processed = ((double(I) - double(master_bias)) - double(master_dark)) ./ double(master_flat);
    I_processed(I_processed < 0) = 0;
    I_processed(I_processed > 1) = 1;

    % --- RGB: demosaic (RGGB Bayer pattern) ---
    I_rgb = im2double(demosaic(im2uint8(I_processed), "rggb"));

    % --- RGB: white balance (G and B relative to R) ---
    I_rgb(:,:,2) = I_rgb(:,:,2) * wb_g;
    I_rgb(:,:,3) = I_rgb(:,:,3) * wb_b;
    I_rgb = min(max(I_rgb, 0), 1);

    % --- RGB: convert to reflectance [%] and normalise to [0-1] ---
    I_reflectance_rgb = zeros(size(I_rgb));
    I_reflectance_rgb(:,:,1) = I_rgb(:,:,1) .* gain_r + bias_r;
    I_reflectance_rgb(:,:,2) = I_rgb(:,:,2) .* gain_g + bias_g;
    I_reflectance_rgb(:,:,3) = I_rgb(:,:,3) .* gain_b + bias_b;
    I_normal_rgb = single(min(max(I_reflectance_rgb ./ 100, 0), 1));

    % --- NIR: read ---
    fid = fopen(nir_path);
    image_data = fread(fid, inf, 'uint8');
    fclose(fid);
    I_nir = reshape(image_data, [width, height])';

    % --- NIR: bias / dark / flat correction ---
    I_nir_processed = ((double(I_nir) - double(master_bias_nir)) - double(master_dark_nir)) ./ double(master_flat_nir);
    I_nir_processed(I_nir_processed < 0) = 0;
    I_nir_processed(I_nir_processed > 1) = 1;

    % --- NIR: equalisation relative to the R channel ---
    I_nir_eq = min(max(I_nir_processed * wb_nir, 0), 1);

    % --- NIR: convert to reflectance [%] and normalise to [0-1] ---
    I_reflectance_nir = I_nir_eq .* gain_nir + bias_nir_val;
    I_normal_nir = single(min(max(I_reflectance_nir ./ 100, 0), 1));

    % --- Output file names ---
    [~, base_name, ~] = fileparts(rgb_filename);
    base_clean = regexprep(base_name, '_RGB$', '', 'ignorecase');
    output_tiff_rgb = fullfile(output_folder, sprintf('%s_reflectance_RGB.tif', base_clean));
    output_tiff_nir = fullfile(output_folder, sprintf('%s_reflectance_NIR.tif', base_clean));

    % --- Write the RGB TIFF (3 bands, 32-bit float) ---
    t_rgb = Tiff(output_tiff_rgb, 'w');
    t_rgb.setTag('ImageLength',         size(I_normal_rgb, 1));
    t_rgb.setTag('ImageWidth',          size(I_normal_rgb, 2));
    t_rgb.setTag('Photometric',         Tiff.Photometric.RGB);
    t_rgb.setTag('BitsPerSample',       32);
    t_rgb.setTag('SamplesPerPixel',     3);
    t_rgb.setTag('SampleFormat',        Tiff.SampleFormat.IEEEFP);
    t_rgb.setTag('PlanarConfiguration', Tiff.PlanarConfiguration.Chunky);
    t_rgb.write(I_normal_rgb);
    t_rgb.close();

    % --- Write the NIR TIFF (1 band, 32-bit float) ---
    t_nir = Tiff(output_tiff_nir, 'w');
    t_nir.setTag('ImageLength',         size(I_normal_nir, 1));
    t_nir.setTag('ImageWidth',          size(I_normal_nir, 2));
    t_nir.setTag('Photometric',         Tiff.Photometric.MinIsBlack);
    t_nir.setTag('BitsPerSample',       32);
    t_nir.setTag('SamplesPerPixel',     1);
    t_nir.setTag('SampleFormat',        Tiff.SampleFormat.IEEEFP);
    t_nir.setTag('PlanarConfiguration', Tiff.PlanarConfiguration.Chunky);
    t_nir.write(I_normal_nir);
    t_nir.close();

    fprintf('    -> %s\n', output_tiff_rgb);
    fprintf('    -> %s\n', output_tiff_nir);
end

fprintf('\n=== BATCH EXPORT FOR METASHAPE COMPLETED ===\n');
fprintf('Output folder: %s\n', output_folder);

%% 7. SANITY CHECK OF THE LAST WRITTEN TIFF (optional)
% Quick verification that the stored values fall within the [0-1] range.
tiff_check = Tiff(output_tiff_rgb, 'r');
I_check = tiff_check.read();
tiff_check.close();

fprintf('\nRGB TIFF check:\n');
fprintf('  R band: min=%.4f, max=%.4f, mean=%.4f\n', ...
    min(min(I_check(:,:,1))), max(max(I_check(:,:,1))), mean(mean(I_check(:,:,1))));
fprintf('  G band: min=%.4f, max=%.4f, mean=%.4f\n', ...
    min(min(I_check(:,:,2))), max(max(I_check(:,:,2))), mean(mean(I_check(:,:,2))));
fprintf('  B band: min=%.4f, max=%.4f, mean=%.4f\n', ...
    min(min(I_check(:,:,3))), max(max(I_check(:,:,3))), mean(mean(I_check(:,:,3))));

tiff_check_nir = Tiff(output_tiff_nir, 'r');
I_check_nir = tiff_check_nir.read();
tiff_check_nir.close();

fprintf('NIR TIFF check:\n');
fprintf('  NIR:    min=%.4f, max=%.4f, mean=%.4f\n', ...
    min(I_check_nir(:)), max(I_check_nir(:)), mean(I_check_nir(:)));

%% =========================================================================
%  HELPER FUNCTION  (in a MATLAB script it must sit at the very end of the file)
% =========================================================================

function master = load_master(folder, ext, sensor_tag, w, h, bdepth, subtract)
% LOAD_MASTER  Load all raw frames of a given sensor in a folder and average them.
%
%   folder     — folder containing the .bin frames
%   ext        — file mask, e.g. '*.bin'
%   sensor_tag — 'RGB' or 'NIR' (substring that must appear in the file name)
%   w, h       — frame dimensions
%   bdepth     — bit depth for fread, e.g. 'uint8'
%   subtract   — (optional) master subtracted from every frame
%                (dark = dark - bias, flat = flat - dark)

    files_all = dir(fullfile(folder, ext));
    matched   = files_all(contains({files_all.name}, sensor_tag));

    if isempty(matched)
        error('No files tagged "%s" were found in folder "%s".', sensor_tag, folder);
    end

    frames = cell(1, length(matched));
    for i = 1:length(matched)
        fid  = fopen(fullfile(folder, matched(i).name));
        data = fread(fid, inf, bdepth);
        fclose(fid);

        frame = reshape(data, [w, h])';
        if nargin == 7
            frame = double(frame) - double(subtract);
        end
        frames{i} = frame;
    end

    master = mean(cat(3, frames{:}), 3, 'native');
end
