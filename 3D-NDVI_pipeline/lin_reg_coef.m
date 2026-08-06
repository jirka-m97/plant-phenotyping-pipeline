% =========================================================================
%  lin_reg_coef.m  —  STEP 1: Radiometric sensor calibration
% =========================================================================
%  Purpose:
%    From a single frame of the calibration target (RGB + NIR), compute:
%      - white balance coefficients (G and B scaled to R, NIR equalised to R)
%      - OECF coefficients (linear mapping image value -> reflectance [%])
%
%  Input:
%    - Img_*_RGB.bin, Img_*_NIR.bin  ... raw target frames (uint8, 2048x1536)
%    - Bias / Dark / Flat folders    ... calibration frames for both sensors
%
%  Output:
%    - <output_mat_name>.mat holding the struct <struct_var_name> with
%      fields R, G, B, NIR (gain/bias) and WB_g, WB_b, WB_nir
%
%  Interaction:
%    The script is interactive. It opens a sequence of windows in which you
%    drag a rectangle: (1) RGB white/grey reference card, (2..6) the five
%    RGB target chips, (7) NIR reference card, (8..12) the five NIR chips.
%
%  Next step: data_analysis.m
% =========================================================================

clc;
clear;
close all;

%% 1. SETTINGS — EDIT BEFORE EVERY RUN
% Calibration target frames
img_path     = "<PATH_TO_RGB_PLANT_IMAGES>";
img_path_NIR = "<PATH_TO_NIR_PLANT_IMAGES>";

% Output .mat file and the name of the struct stored inside it.
% NOTE: the struct name MUST end with "_koefs" — data_analysis.m looks it up
% by that suffix.
output_mat_name = "P1.mat";
struct_var_name = "P1_koefs";

% Calibration frames (bias / dark / flat) — shared by the RGB and NIR sensor
folder_bias = "<PATH_TO_BIAS_IMAGES>";
folder_dark = "<PATH_TO_DARK_IMAGES>";
folder_flat = "<PATH_TO_FLAT_IMAGES>";

% Known reflectance of the calibration target chips [%]
reflectances_rgb = [0.67, 4.40, 19.51, 50.65, 92.44];
reflectances_nir = [7.29, 11.29, 30.72, 64.51, 95.42];
number_of_chips  = 5;

% Raw frame parameters
width          = 2048;
height         = 1536;
bit_depth      = 'uint8';
file_extension = '*.bin';

%% 2. MASTER BIAS / DARK / FLAT — RGB sensor
master_bias = load_master(folder_bias, file_extension, 'RGB', width, height, bit_depth);
master_dark = load_master(folder_dark, file_extension, 'RGB', width, height, bit_depth, master_bias);
master_flat = load_master(folder_flat, file_extension, 'RGB', width, height, bit_depth, master_dark);

%% 3. LOAD AND RADIOMETRICALLY CORRECT — RGB
fid = fopen(img_path);
image_data = fread(fid, width * height, 'uint8');
fclose(fid);
I = reshape(image_data, [width, height])';

% (raw - bias - dark) / flat, clipped to [0, 1]
I_processed = ((double(I) - double(master_bias)) - double(master_dark)) ./ double(master_flat);
I_processed(I_processed < 0) = 0;
I_processed(I_processed > 1) = 1;

% Debayer the RGGB Bayer pattern
I_rgb_processed = im2double(demosaic(im2uint8(I_processed), "rggb"));

%% 4. WHITE BALANCE — select the grey/white reference card
figure('Name', 'RGB: select the white/grey reference card')
imshow(I_rgb_processed, [])
h_rect   = imrect();
pos_rect = round(h_rect.getPosition());
close

gray_card_values = I_rgb_processed(pos_rect(2)+(0:pos_rect(4)), pos_rect(1)+(0:pos_rect(3)), :);
means = reshape(mean(mean(gray_card_values)), [1 3]);

% WB coefficients (G and B scaled relative to R)
wb_coef_g = means(1) / means(2);
wb_coef_b = means(1) / means(3);

I_wb_processed = cat(3, I_rgb_processed(:,:,1), ...
                        I_rgb_processed(:,:,2) * wb_coef_g, ...
                        I_rgb_processed(:,:,3) * wb_coef_b);

%% 5. OECF CALIBRATION — RGB target
% For every chip of the target, take the mean value in each channel
gray_values_rgb = zeros(number_of_chips, 3);

for i = 1:number_of_chips
    figure('Name', ['RGB: select chip no. ', num2str(i)])
    imshow(I_wb_processed, [])
    h_rect   = imrect();
    pos_rect = round(h_rect.getPosition());
    close

    gray_value = I_wb_processed(pos_rect(2)+(0:pos_rect(4)), pos_rect(1)+(0:pos_rect(3)), :);
    gray_values_rgb(i, :) = reshape(mean(gray_value, [1 2]), [1, 3]);
end

% Linear regression: image value [0-1] -> reflectance [%]
coef_r = polyfit(gray_values_rgb(:,1), reflectances_rgb, 1);
coef_g = polyfit(gray_values_rgb(:,2), reflectances_rgb, 1);
coef_b = polyfit(gray_values_rgb(:,3), reflectances_rgb, 1);

%% 6. MASTER BIAS / DARK / FLAT — NIR sensor
master_bias_nir = load_master(folder_bias, file_extension, 'NIR', width, height, bit_depth);
master_dark_nir = load_master(folder_dark, file_extension, 'NIR', width, height, bit_depth, master_bias_nir);
master_flat_nir = load_master(folder_flat, file_extension, 'NIR', width, height, bit_depth, master_dark_nir);

%% 7. LOAD AND RADIOMETRICALLY CORRECT — NIR
fid = fopen(img_path_NIR);
image_data = fread(fid, inf, 'uint8');
fclose(fid);
I_nir = reshape(image_data, [width, height])';

I_nir_processed = ((double(I_nir) - double(master_bias_nir)) - double(master_dark_nir)) ./ double(master_flat_nir);
I_nir_processed(I_nir_processed < 0) = 0;
I_nir_processed(I_nir_processed > 1) = 1;

%% 8. NIR EQUALISATION — select the reference card
figure('Name', 'NIR: select the reference card for equalisation')
imshow(I_nir_processed, [])
h_rect   = imrect();
pos_rect = round(h_rect.getPosition());
close

gray_card_values_nir = I_nir_processed(pos_rect(2)+(0:pos_rect(4)), pos_rect(1)+(0:pos_rect(3)), :);
means_nir = mean(mean(gray_card_values_nir));

% NIR equalisation coefficient (normalised to the R channel of the RGB sensor)
wb_coef_nir = means(1) / means_nir;

I_equalized_nir = I_nir_processed * wb_coef_nir;
I_equalized_nir(I_equalized_nir < 0) = 0;
I_equalized_nir(I_equalized_nir > 1) = 1;

%% 9. OECF CALIBRATION — NIR target
gray_values_nir = zeros(number_of_chips, 1);

for i = 1:number_of_chips
    figure('Name', ['NIR: select chip no. ', num2str(i)])
    imshow(I_equalized_nir, [])
    h_rect   = imrect();
    pos_rect = round(h_rect.getPosition());
    close

    gray_value = I_equalized_nir(pos_rect(2)+(0:pos_rect(4)), pos_rect(1)+(0:pos_rect(3)), :);
    gray_values_nir(i, 1) = reshape(mean(gray_value, [1 2]), [1, 1]);
end

coef_nir = polyfit(gray_values_nir(:,1), reflectances_nir, 1);

%% 10. GOODNESS OF FIT (R²)
compute_R2 = @(p, x, y) 1 - abs(sum((y(:) - polyval(p, x(:))).^2) / sum((y(:) - mean(y(:))).^2));

R2_R   = compute_R2(coef_r,   gray_values_rgb(:,1), reflectances_rgb);
R2_G   = compute_R2(coef_g,   gray_values_rgb(:,2), reflectances_rgb);
R2_B   = compute_R2(coef_b,   gray_values_rgb(:,3), reflectances_rgb);
R2_NIR = compute_R2(coef_nir, gray_values_nir(:,1), reflectances_nir);

%% 11. SAVE TO .MAT — OECF + WB coefficients
eval(struct_var_name + ".R   = coef_r;");
eval(struct_var_name + ".G   = coef_g;");
eval(struct_var_name + ".B   = coef_b;");
eval(struct_var_name + ".NIR = coef_nir;");

% The WB coefficients are required for correct application in data_analysis.m
eval(struct_var_name + ".WB_g   = wb_coef_g;");
eval(struct_var_name + ".WB_b   = wb_coef_b;");
eval(struct_var_name + ".WB_nir = wb_coef_nir;");

save(output_mat_name, struct_var_name);
fprintf('Saved: "%s" -> "%s"\n', struct_var_name, output_mat_name);

%% 12. PLOTS AND STATISTICS
fig1 = figure(101); clf(fig1);
set(fig1, 'Name', ['RGB calibration - ' char(struct_var_name)], 'NumberTitle', 'off');
hold on
x_fit = linspace(0, 1, 100);
plot(gray_values_rgb(:,1), reflectances_rgb, 'r*', 'MarkerSize', 8)
plot(gray_values_rgb(:,2), reflectances_rgb, 'g*', 'MarkerSize', 8)
plot(gray_values_rgb(:,3), reflectances_rgb, 'b*', 'MarkerSize', 8)
plot(x_fit, polyval(coef_r, x_fit), 'r-', 'LineWidth', 1)
plot(x_fit, polyval(coef_g, x_fit), 'g-', 'LineWidth', 1)
plot(x_fit, polyval(coef_b, x_fit), 'b-', 'LineWidth', 1)
xlabel('Image values (-)');
ylabel('Reflectance (%)');
axis([0 1 0 100]);
grid on
title(['RGB OECF - ' char(struct_var_name)], 'Interpreter', 'none')

fig2 = figure(102); clf(fig2);
set(fig2, 'Name', ['NIR calibration - ' char(struct_var_name)], 'NumberTitle', 'off');
hold on
plot(gray_values_nir(:,1), reflectances_nir, 'k*', 'MarkerSize', 8)
plot(x_fit, polyval(coef_nir, x_fit), 'k-', 'LineWidth', 1)
xlabel('Image values (-)');
ylabel('Reflectance (%)');
axis([0 1 0 100]);
grid on
title(['NIR OECF - ' char(struct_var_name)], 'Interpreter', 'none')

fprintf('\n--- STATISTICS %s ---\n', char(struct_var_name));
fprintf('Red:   Gain = %.4f, Bias = %.4f, R² = %.4f\n', coef_r(1),   coef_r(2),   R2_R);
fprintf('Green: Gain = %.4f, Bias = %.4f, R² = %.4f\n', coef_g(1),   coef_g(2),   R2_G);
fprintf('Blue:  Gain = %.4f, Bias = %.4f, R² = %.4f\n', coef_b(1),   coef_b(2),   R2_B);
fprintf('NIR:   Gain = %.4f, Bias = %.4f, R² = %.4f\n', coef_nir(1), coef_nir(2), R2_NIR);
fprintf('WB:    G = %.4f, B = %.4f, NIR = %.4f\n', wb_coef_g, wb_coef_b, wb_coef_nir);

%% =========================================================================
%  HELPER FUNCTION
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
