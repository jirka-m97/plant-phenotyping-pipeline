% =========================================================================
% Multispectral NDVI Pipeline (script version, en-GB)
% Authors: Jiří Mach, Lukáš Krauz
% Institutions: 
%   - UCT Prague, Laboratory of Bioengineering
%   - Department of Radioelectronics, FEE, Czech Technical University in Prague
% Licence: Apache 2.0
% Date: 2025-09-18
% Description:
%   Implements a multispectral image processing workflow for plant NDVI 
%   calculation. Includes radiometric calibration of RGB and NIR data, 
%   reflectance correction using a calibration chart, NDVI computation, 
%   and plant tissue segmentation (manual or CNN-based). Outputs include 
%   calibrated imagery, NDVI maps, and statistical metrics.
% =========================================================================
%%

clc; close all; clearvars;

%% ============ CONFIG ============

width              = 2048;
height             = 1536;
bitDepth           = 'uint8';

% Single frames
pathRGB            = "V:\\Data\\MS_analysis\\_testing\\Img_1_RGB.bin";
pathNIR            = "V:\\Data\\MS_analysis\\_testing\\Img_1_NIR.bin";

% Calibration folders (masters are averaged from *.bin filtered by keyword)
folder_biasRGB     = "V:\\Data\\MS_analysis\\_testing\\Bias";
folder_darkRGB     = "V:\\Data\\MS_analysis\\_testing\\Dark";
folder_flatRGB     = "V:\\Data\\MS_analysis\\_testing\\Flat";

folder_biasNIR     = folder_biasRGB;
folder_darkNIR     = folder_darkRGB;
folder_flatNIR     = folder_flatRGB;

% Test chart ROIs [x y w h]; order must match the reflectance arrays
roi_wbRGB          = [1480, 330, 200, 100]; % reference chip for RGB white balance
roi_wbNIR          = [1480, 330, 200, 100]; % reference chip for NIR normalisation

roi_oecfRGB = [...
    1480, 1290, 200, 100;  % Chip 5
    1460, 1055, 260,  70;  % Chip 4
    1480,  820, 200, 100;  % Chip 3
    1480,  570, 200, 100;  % Chip 2
    1480,  330, 200, 100]; % Chip 1
reflectanceRGB     = [0.67, 4.40, 19.51, 50.65, 92.44];

roi_oecfNIR = [...
    1460, 1055, 260,  70;  % Chip 4
    1480, 1290, 200, 100;  % Chip 5
    1480,  820, 200, 100;  % Chip 3
    1480,  570, 200, 100;  % Chip 2
    1480,  330, 200, 100]; % Chip 1
reflectanceNIR     = [7.29, 11.29, 30.72, 64.51, 95.42];

% Visualisation & outputs
showOverlays       = true;   % draw rectangles and labels
annotateMeans      = true;   % print mean values next to chips
saveOutputs        = false;  % save NDVI/mask/calibration logs
% outputFolder       = "Masked_images";

% Post‑processing & stats
minRegionSize      = 500;    % remove small speckles
ndviLowerThresh    = 0.35;   % remove background remnants
ndviUpperThresh    = 1.00;   % remove soil/high outliers (physically >1 invalid)


%% ============ MASTER FRAMES (folder‑based, keyword filtered) ============

% ---- RGB
rgbBias = create_master_frame(folder_biasRGB, 'RGB', width, height, bitDepth, []);
rgbDark = create_master_frame(folder_darkRGB, 'RGB', width, height, bitDepth, rgbBias);
rgbFlat = create_master_frame(folder_flatRGB, 'RGB', width, height, bitDepth, rgbDark);

% ---- NIR
nirBias = create_master_frame(folder_biasNIR, 'NIR', width, height, bitDepth, []);
nirDark = create_master_frame(folder_darkNIR, 'NIR', width, height, bitDepth, nirBias);
nirFlat = create_master_frame(folder_flatNIR, 'NIR', width, height, bitDepth, nirDark);

%% ============ LOAD & CALIBRATE FRAMES ============

rgbRaw = read_single_bin_image(pathRGB, width, height, bitDepth);
rgbCal = clamp_image(((rgbRaw - rgbBias) - rgbDark) ./ rgbFlat, 0, 1);

nirRaw = read_single_bin_image(pathNIR, width, height, bitDepth);
nirCal = clamp_image(((nirRaw - nirBias) - nirDark) ./ nirFlat, 0, 1);

%% ============ DEMOSAIC + WHITE BALANCE (RGB) ============

rgbDemosaic = im2double(demosaic(im2uint8(rgbCal), "rggb"));

wbROI   = crop_rect(rgbDemosaic, roi_wbRGB);
rgbMean = squeeze(mean(mean(wbROI,1),2));  % [R G B]

coefRG = rgbMean(1) / rgbMean(2);
coefRB = rgbMean(1) / rgbMean(3);

rgbWB = cat(3, ...
    rgbDemosaic(:,:,1), ...
    rgbDemosaic(:,:,2) * coefRG, ...
    rgbDemosaic(:,:,3) * coefRB);

if showOverlays
    show_rects_with_labels(rgbWB, roi_wbRGB, "RGB white balance (AUTO ROI)", ...
        "White balance chip", [], annotateMeans, mean(reshape(wbROI, [], 3), 1));
end

%% ============ OECF — RGB (empirical line) ============

rgbChipMeans = measure_rgb_chips(rgbWB, roi_oecfRGB);
coefR = polyfit(rgbChipMeans(:,1), reflectanceRGB, 1);
coefG = polyfit(rgbChipMeans(:,2), reflectanceRGB, 1);
coefB = polyfit(rgbChipMeans(:,3), reflectanceRGB, 1);

rgbCorrected = zeros(size(rgbWB));
rgbCorrected(:,:,1) = rgbWB(:,:,1) * coefR(1) + coefR(2);
rgbCorrected(:,:,2) = rgbWB(:,:,2) * coefG(1) + coefG(2);
rgbCorrected(:,:,3) = rgbWB(:,:,3) * coefB(1) + coefB(2);

if showOverlays
    show_rects_with_labels(rgbWB, roi_oecfRGB, "OECF — RGB (AUTO ROI)", ...
        "RGB chip %d", rgbChipMeans, annotateMeans, []);
    figure; hold on; grid on;
    plot(rgbChipMeans(:,1), reflectanceRGB, 'r*');
    plot(rgbChipMeans(:,2), reflectanceRGB, 'g*');
    plot(rgbChipMeans(:,3), reflectanceRGB, 'b*');
    xlabel('Image values (–)'); ylabel('Reflectance (%)');
    axis([0 1 0 100]); legend('R','G','B','Location','best');
    title('Calibration curve — RGB reflectance');
    hold off;
end

%% ============ NIR NORMALISATION + OECF ============

nirWB      = crop_rect(nirCal, roi_wbNIR);
nirMean    = mean(nirWB(:));
coefRoverN = rgbMean(1) / nirMean;                 % normalise w.r.t. RGB R‑channel WB
nirEqual   = clamp_image(nirCal * coefRoverN, 0, 1);

nirChipMeans = measure_grey_chips(nirEqual, roi_oecfNIR);
coefNIR = polyfit(nirChipMeans, reflectanceNIR, 1);
nirCorrected = nirEqual * coefNIR(1) + coefNIR(2);

if showOverlays
    show_rects_with_labels(nirCal, roi_wbNIR, "NIR normalisation (AUTO ROI)", ...
        "NIR white balance chip", [], annotateMeans, mean(nirWB(:)));
    show_rects_with_labels(nirEqual, roi_oecfNIR, "OECF — NIR (AUTO ROI)", ...
        "NIR chip %d", nirChipMeans, annotateMeans, []);
    figure; grid on;
    plot(nirChipMeans, reflectanceNIR, 'k*');
    xlabel('Image values (–)'); ylabel('Reflectance (%)');
    axis([0 1 0 100]); title('Calibration curve — NIR reflectance');
end

%% ============ NDVI ============

Rcorr = rgbCorrected(:,:,1);
NDVI  = (nirCorrected - Rcorr) ./ (nirCorrected + Rcorr);

%% ============ PLANT SEGMENTATION (MANUAL) ============
% Open imageSegmenter on the NDVI map. Export variable "Mask" to base workspace.
imageSegmenter(rgbWB);
%%
if ~evalin('base','exist(''Mask'',''var'')')
    warning('Mask was not exported from imageSegmenter. Please export variable "Mask" and re‑run the next block.');
end
Mask = evalin('base','Mask');

%% ============ MASK REFINEMENT & NDVI STATS ============
% 1) Remove small objects from the raw mask
Mask = bwareaopen(Mask, minRegionSize);

% 2) Apply NDVI‑based filtering to the mask (lower & upper bounds)
Mask(NDVI < ndviLowerThresh) = 0;
Mask(NDVI > ndviUpperThresh) = 0;

% 3) Clean again after thresholding
Mask = bwareaopen(Mask, minRegionSize);

% 4) Masked NDVI and statistics
NDVI_masked = NDVI .* double(Mask);
validMask   = (Mask & NDVI_masked > ndviLowerThresh);
validVals   = NDVI_masked(validMask);

if ~isempty(validVals)
    avgNDVI = mean(validVals);
    sdNDVI  = std(validVals);
    fprintf('Mean NDVI (leaf area): %.3f ± %.3f\n', avgNDVI, sdNDVI);
else
    warning('No valid pixels for NDVI computation.');
end

% Visualisation
figure; imshow(NDVI_masked, []);
colormap(gca, jet); colorbar; caxis([-1, 1]);
title('NDVI — plants only (post NDVI‑threshold filtering)');

%% ============ SAVE OUTPUTS (optional) ============
if saveOutputs
    if ~exist(outputFolder, 'dir'); mkdir(outputFolder); end
    [~, baseRGB, ~] = fileparts(string(pathRGB));
    save(fullfile(outputFolder, baseRGB + "_mask.mat"), "Mask");
    save(fullfile(outputFolder, baseRGB + "_NDVI.mat"), "NDVI_masked");
    calib.rgb.coefR = coefR; calib.rgb.coefG = coefG; calib.rgb.coefB = coefB;
    calib.nir.coef  = coefNIR;
    calib.wb.rgbMean = rgbMean; calib.wb.nirMean = nirMean; calib.coefRoverN = coefRoverN;
    save(fullfile(outputFolder, baseRGB + "_calibration.mat"), "calib");
end


%% ====================== HELPER FUNCTIONS ======================
% Keep helper functions at the end of the script (MATLAB script convention)

function master = create_master_frame(folderPath, keyword, w, h, bitDepth, subtractFrame)
% Build a master frame by averaging all *.bin images containing 'keyword'
% (RGB/NIR). Optionally subtract a prior master (bias/dark) before averaging.
    files = dir(fullfile(folderPath, '*.bin'));
    files = files(contains({files.name}, keyword));
    assert(~isempty(files), "No files found in %s containing keyword '%s'.", folderPath, keyword);

    stack = cell(1, numel(files));
    for i = 1:numel(files)
        fid = fopen(fullfile(folderPath, files(i).name));
        raw = fread(fid, inf, bitDepth);
        fclose(fid);
        img = reshape(raw, [w, h])';
        if ~isempty(subtractFrame)
            img = img - subtractFrame;
        end
        stack{i} = img;
    end
    master = mean(cat(3, stack{:}), 3, 'native');
end

function img = read_single_bin_image(path, w, h, bitDepth)
% Read a single *.bin image with given geometry and depth.
    fid = fopen(path);
    raw = fread(fid, w*h, bitDepth);
    fclose(fid);
    img = reshape(raw, [w, h])';
end

function out = clamp_image(in, a, b)
% Clamp values to the closed interval <a, b>.
    out = in;
    out(out < a) = a;
    out(out > b) = b;
end

function roi = crop_rect(img, rect)
% Crop by rect = [x y w h]; supports 2D and 3D arrays.
    x = rect(1); y = rect(2); w = rect(3); h = rect(4);
    roi = img(y:(y+h-1), x:(x+w-1), :);
end

function meansRGB = measure_rgb_chips(imgRGB, rects)
% Return Nx3 means over provided chip rectangles.
    N = size(rects,1);
    meansRGB = zeros(N,3);
    for i = 1:N
        roi = crop_rect(imgRGB, rects(i,:));
        meansRGB(i,:) = squeeze(mean(mean(roi,1,'omitnan'),2,'omitnan'))';
    end
end

function meansGrey = measure_grey_chips(imgGrey, rects)
% Return Nx1 means over provided chip rectangles (single‑channel).
    N = size(rects,1);
    meansGrey = zeros(N,1);
    for i = 1:N
        roi = crop_rect(imgGrey, rects(i,:));
        meansGrey(i) = mean(roi(:), 'omitnan');
    end
end

function show_rects_with_labels(img, rects, figTitle, labelFmt, values, annotateMeans, wbMean)
% Visualise rectangles with labels; optionally annotate with mean values.
% - rects: 1x4 (WB) or Nx4 (OECF)
% - labelFmt: e.g. 'RGB chip %d' / 'NIR chip %d' / 'White balance chip'
% - values: [] or Nx3/Nx1 (means), WB may pass []
% - wbMean: scalar or 1x3 for WB (optional)
    figure; imshow(img, []); hold on;
    if size(rects,1) == 1
        rectangle('Position', rects, 'EdgeColor','c','LineWidth',2);
        if contains(labelFmt, '%d')
            text(rects(1)+50, rects(2)-16, sprintf(labelFmt, 1), ...
                'Color','c','FontSize',12,'FontWeight','bold');
        else
            text(rects(1)+50, rects(2)-16, labelFmt, ...
                'Color','c','FontSize',12,'FontWeight','bold');
        end
        if annotateMeans && ~isempty(wbMean)
            if numel(wbMean)==3
                txt = sprintf('mean: R=%.3f G=%.3f B=%.3f', wbMean(1), wbMean(2), wbMean(3));
            else
                txt = sprintf('mean: %.3f', wbMean);
            end
            text(rects(1)+5, rects(2)+rects(4)+18, txt, 'Color','c','FontSize',11,'FontWeight','bold');
        end
    else
        for i = 1:size(rects,1)
            r = rects(i,:);
            rectangle('Position', r, 'EdgeColor','c','LineWidth',2);
            text(r(1)+50, r(2)-16, sprintf(labelFmt, i), ...
                'Color','c','FontSize',11,'FontWeight','bold');
            if annotateMeans && ~isempty(values)
                if size(values,2)==3
                    txt = sprintf('R=%.3f G=%.3f B=%.3f', values(i,1), values(i,2), values(i,3));
                else
                    txt = sprintf('mean=%.3f', values(i));
                end
                text(r(1)+5, r(2)+r(4)+18, txt, 'Color','c','FontSize',10,'FontWeight','bold');
            end
        end
    end
    title(figTitle); hold off;
end
