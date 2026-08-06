% =========================================================================
%  rename.m  —  STEP 3 (optional): Renumber frames by an offset
% =========================================================================
%  Purpose:
%    Shifts the sequential numbers in the reflectance frame names by a given
%    offset. Each of the six camera positions yields 60 frames numbered from
%    1 to 60. Since all 360 frames enter a single photogrammetric
%    reconstruction, the numbering of every set is shifted so that the file
%    names remain unique across the whole dataset.
%
%  Input:
%    Img_<N>_reflectance_RGB.tif  /  Img_<N>_reflectance_NIR.tif
%
%  Output:
%    Img_<N+offset>_reflectance_RGB.tif  /  ..._NIR.tif  (renamed in place)
%
%  WARNING:
%    - Renaming happens IN PLACE (movefile); the original names are gone and
%      the operation cannot be undone.
%    - Choose an offset larger than the highest existing number in the target
%      set, otherwise files will be overwritten.
%
%  Next step: tif_4band.m
% =========================================================================

clc;
clear;

%% 1. SETTINGS — EDIT BEFORE EVERY RUN
folder = "<PATH_TO_OUTPUT_FOLDER>";
offset = 60; %120, 180, 240, 300

%% 2. FIND THE FILES
files = dir(fullfile(folder, 'Img_*_reflectance_*.tif'));
fprintf('Files found: %d\n', length(files));

%% 3. RENAME
for i = 1:length(files)
    name = files(i).name;

    % Extract the sequential number and the band (RGB / NIR) from the name
    tokens = regexp(name, 'Img_(\d+)_reflectance_(RGB|NIR)\.tif$', 'tokens');
    if isempty(tokens)
        fprintf('Skipped: %s\n', name);
        continue;
    end

    num     = str2double(tokens{1}{1});
    channel = tokens{1}{2};

    new_name = sprintf('Img_%d_reflectance_%s.tif', num + offset, channel);

    movefile(fullfile(folder, name), fullfile(folder, new_name));
    fprintf('%s  ->  %s\n', name, new_name);
end

fprintf('\nDone.\n');
