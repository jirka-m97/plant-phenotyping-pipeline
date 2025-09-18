% =========================================================================
% Plant Segmentation with DeepLab v3+ (MATLAB script, en-GB)
% Author: Jiří Mach
% Institution: UCT Prague, Faculty of Food and Biochemical Technology, Laboratory of Bioengineering
% Licence: Apache 2.0
% Date: 2025-09-18
% Description:
%   Trains and evaluates a DeepLab v3+ network with ResNet-50 backbone
%   for semantic segmentation of plant imagery. Includes dataset loading,
%   data augmentation, train–test split, network training, prediction,
%   visualisation, and evaluation with standard metrics.
% =========================================================================
%%

%% Clean workspace
clear all 
clc

%% === Folder paths ===
imageDir = fullfile(".\ObjDet_RGB");         % images
labelDir = fullfile(".\ObjDet_mask_png");    % masks

%% === Dataset loading ===
imds = imageDatastore(imageDir, 'FileExtensions', '.png');

classes  = ["background", "plant"];
labelIDs = [0, 255]; % 0 = background, 255 = plant

pxds = pixelLabelDatastore(labelDir, classes, labelIDs);

assert(numel(imds.Files) == numel(pxds.Files), ...
    "The number of images and masks does not match.");

for i = 1:numel(imds.Files)
    I = imread(imds.Files{i});
    L = imread(pxds.Files{i});
    if size(I,1) ~= size(L,1) || size(I,2) ~= size(L,2)
        error("Image and mask dimensions do not match: %s", imds.Files{i});
    end
end

%% === Train–test split ===
numImages = numel(imds.Files);
rng(0) % reproducibility
shuffledIndices = randperm(numImages);
numTrain = round(0.8 * numImages);

trainIdx = shuffledIndices(1:numTrain);
testIdx  = shuffledIndices(numTrain+1:end);

imdsTrain = subset(imds, trainIdx);
imdsTest  = subset(imds, testIdx);

pxdsTrain = subset(pxds, trainIdx);
pxdsTest  = subset(pxds, testIdx);

%% === Image size ===
I = readimage(imdsTrain, 1);
imageSize  = [size(I,1), size(I,2), size(I,3)];
numClasses = numel(classes);

%% === Data augmentation ===
augmenter = imageDataAugmenter( ...
    'RandXReflection', true, ...
    'RandRotation',    [-10 10], ...
    'RandXTranslation',[-15 15], ...
    'RandYTranslation',[-15 15]);

pximdsTrain = pixelLabelImageDatastore(imdsTrain, pxdsTrain, ...
    'DataAugmentation', augmenter, ...
    'OutputSize', imageSize);

pximdsTest = pixelLabelImageDatastore(imdsTest, pxdsTest, ...
    'OutputSize', imageSize);

%% === DeepLab v3+ with ResNet-50 ===
lgraph = deeplabv3plusLayers(imageSize, numClasses, 'resnet50');

%% === Class weights ===
classWeights = [1, 20];
pxLayer = pixelClassificationLayer('Name','labels', ...
    'Classes', classes, ...
    'ClassWeights', classWeights);

lgraph = replaceLayer(lgraph, 'classification', pxLayer);

%% === Training options ===
options = trainingOptions('adam', ...
    'InitialLearnRate', 0.001, ...
    'MaxEpochs', 25, ...
    'MiniBatchSize', 4, ...
    'Shuffle', 'every-epoch', ...
    'Plots', 'training-progress', ...
    'ExecutionEnvironment', 'auto');

%% === Network training ===
net_resnet50_finetune_wider = trainNetwork(pximdsTrain, lgraph, options);

%% === Quick visual check on a test image ===
Itest = readimage(imdsTest, 1);
C = semanticseg(Itest, net_resnet50_finetune_wider);

% Overlay predicted segmentation in red
mask_pred = C == "plant";
figure; imshow(Itest); hold on;
h = imshow(cat(3, ones(size(mask_pred)), zeros(size(mask_pred)), zeros(size(mask_pred))));
set(h, 'AlphaData', 0.4 * mask_pred);
hold off;
title('Predicted segmentation overlay (red)');

%% === Evaluation ===
pxdsResults = semanticseg(imdsTest, net_resnet50_finetune_wider, ...
    'MiniBatchSize', 4, ...
    'Verbose', false);

metrics = evaluateSemanticSegmentation(pxdsResults, pxdsTest, ...
    'Verbose', false);

disp(metrics.DataSetMetrics)
disp(metrics.ClassMetrics)
