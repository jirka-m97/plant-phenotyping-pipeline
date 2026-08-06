% =========================================================================
%  NDVI_3D_model.m  —  STEP 5: Projection of NDVI onto the 3D plant model
% =========================================================================
%  Purpose:
%    Loads the photogrammetric mesh of the plant (OBJ) together with the
%    camera orientations exported from Metashape, back-projects every mesh
%    vertex into the four-band images, computes NDVI and assigns it to the
%    vertices (averaged over all cameras that see the vertex). The mean NDVI
%    per face is then derived from its three vertices.
%
%  Input:
%    - <project_dir>\<obj_file>              ... mesh exported from Metashape
%    - <project_dir>\<cam_file>              ... camera table (label, x, y, z,
%                                                r11..r33, fx, fy, cx, cy)
%    - <project_dir>\Source_data_4band\*.tif ... four-band images (tif_4band.m)
%
%  Output:
%    - figures showing the NDVI mesh (interpolated on vertices / flat on faces)
%    - NDVI_model.tif        ... publication-quality render (300 dpi)
%    - 3D_model_filtered.obj ... mesh with the background removed
%
%  The script is split into cells (%%) and can be executed step by step.
%  Cells 1-3 must always be run; cells 4+ are visualisation and export.
%
%  Requires: ndvi_cursor.m (NDVI data tip) in the same folder.
% =========================================================================

clc;
clear;
close all;

%% 0. PATHS — EDIT BEFORE EVERY RUN
project_dir = "<PATH_TO_PROJECT>";

obj_file     = fullfile(project_dir, "<OBJ_MODEL_FILE>");
% cameras_final.txt is exported from Metashape using the script
% "cameras_TXT_Metashape_export.txt"
cam_file     = fullfile(project_dir, "cameras_final.txt");
folder_4band = fullfile(project_dir, "Source_data_4band");

% Export targets 
out_obj = "<PATH_TO_OUTPUT_OBJ>\3D_model_filtered.obj";

% NDVI threshold used to remove the background (cell 5)
ndvi_threshold = 0;

%% 1. LOAD THE OBJ MESH
fid = fopen(obj_file, 'r');
vertices = [];
faces    = [];
colors   = [];

while ~feof(fid)
    line = fgetl(fid);
    if length(line) < 2, continue; end

    if strncmp(line, 'v ', 2)
        % Vertex line: "v x y z [r g b]"
        vals = sscanf(line(3:end), '%f');
        if length(vals) >= 3
            vertices(end+1, :) = vals(1:3)';
        end
        if length(vals) >= 6
            colors(end+1, :) = vals(4:6)';
        end

    elseif strncmp(line, 'f ', 2)
        % Face line: "f v1/vt1/vn1 v2/... v3/..." — only the vertex index is used
        tokens = strsplit(strtrim(line(3:end)));
        idx = zeros(1, 3);
        for i = 1:3
            parts = strsplit(tokens{i}, '/');
            idx(i) = str2double(parts{1});
        end
        faces(end+1, :) = idx;
    end
end
fclose(fid);

fprintf('Mesh loaded: %d vertices, %d faces\n', size(vertices,1), size(faces,1));

%% 2. LOAD CAMERAS AND CHECK THE IMAGES
cams = readtable(cam_file);
fprintf('Cameras loaded: %d\n', height(cams));

files = dir(fullfile(folder_4band, '*.tif'));
fprintf('TIF files in the folder: %d\n', length(files));
if ~isempty(files)
    fprintf('First file: %s\n', files(1).name);
end

%% 3. PROJECT NDVI ONTO THE VERTICES
% For every camera: the vertices are transformed into camera coordinates,
% projected into the image with a pinhole model and the NDVI of the hit pixel
% is read out. Contributions are accumulated and finally divided by the number
% of cameras that saw each vertex.
ndvi_sum   = zeros(size(vertices, 1), 1);
ndvi_count = zeros(size(vertices, 1), 1);

for i = 1:height(cams)
    cam = cams(i, :);

    % The image is matched to the camera through the Metashape label
    img_name = fullfile(folder_4band, [cam.label{1}, '.tif']);
    if ~exist(img_name, 'file')
        continue;
    end

    img = single(imread(img_name));
    red = img(:,:,1);
    nir = img(:,:,4);

    ndvi_img = (nir - red) ./ (nir + red + 1e-10);
    [H, W] = size(ndvi_img);

    % Exterior orientation: rotation matrix + camera position
    R = [cam.r11, cam.r12, cam.r13;
         cam.r21, cam.r22, cam.r23;
         cam.r31, cam.r32, cam.r33];
    pos = [cam.x, cam.y, cam.z]';

    % Interior orientation (in Metashape cx, cy are offsets from the image centre)
    fx = cam.fx;
    fy = cam.fy;
    cx = cam.cx + W/2;
    cy = cam.cy + H/2;

    % World coordinates -> camera coordinates
    pt     = bsxfun(@minus, vertices, pos');
    pt_cam = (R' * pt')';

    % Projection into the image (only points in front of the camera)
    valid = pt_cam(:,3) > 0;
    u = round(fx * pt_cam(:,1) ./ pt_cam(:,3) + cx);
    v = round(fy * pt_cam(:,2) ./ pt_cam(:,3) + cy);

    % Clip to the image extent
    valid = valid & u >= 1 & u <= W & v >= 1 & v <= H;

    idx = sub2ind([H W], v(valid), u(valid));
    ndvi_vals = ndvi_img(idx);

    ndvi_sum(valid)   = ndvi_sum(valid)   + ndvi_vals;
    ndvi_count(valid) = ndvi_count(valid) + 1;

    if mod(i, 10) == 0
        fprintf('Camera %d/%d\n', i, height(cams));
    end
end

ndvi_vertex = ndvi_sum ./ max(ndvi_count, 1);
fprintf('NDVI min: %.4f, max: %.4f\n', min(ndvi_vertex), max(ndvi_vertex));

%% 4. QUICK PREVIEW OF THE FULL MESH
figure();
patch('Vertices', vertices, ...
      'Faces', faces, ...
      'FaceVertexCData', ndvi_vertex, ...
      'FaceColor', 'interp', ...
      'EdgeColor', 'none');
colormap(jet);
colorbar;
caxis([-1 1]);
axis equal;
title('NDVI mesh model');
xlabel('X'); ylabel('Y'); zlabel('Z');
view(3);

%% 5. CLEANED MODEL WITHOUT BACKGROUND
% Faces whose three vertices all fall below the threshold (typically the
% background and soil) are discarded. The vertex list stays untouched —
% only the face list changes.
keep_vertices = ndvi_vertex >= ndvi_threshold;
keep_faces    = all(keep_vertices(faces), 2);

vertices_clean = vertices;
faces_clean    = faces(keep_faces, :);
ndvi_clean     = ndvi_vertex;

fprintf('Faces before cleaning: %d\n', size(faces, 1));
fprintf('Faces after cleaning: %d\n', size(faces_clean, 1));

figure();
patch('Vertices', vertices_clean, ...
      'Faces', faces_clean, ...
      'FaceVertexCData', ndvi_clean, ...
      'FaceColor', 'interp', ...
      'EdgeColor', 'none');
colormap(jet);
colorbar;
caxis([-1 1]);
axis equal;
title('NDVI mesh model - cleaned');
xlabel('X'); ylabel('Y'); zlabel('Z');
view(3);

%% 6. NDVI PER FACE + FINAL RENDER
% Mean NDVI of the three vertices of each face -> one value per face.
ndvi_faces = mean(ndvi_clean(faces_clean), 2);

% Centre the vertices around the origin (makes view rotation predictable)
center            = mean(vertices_clean);
vertices_centered = bsxfun(@minus, vertices_clean, center);

figure('Color', 'white');
p = patch('Vertices', vertices_centered, ...
          'Faces', faces_clean, ...
          'FaceVertexCData', ndvi_faces, ...
          'FaceColor', 'flat', ...
          'EdgeColor', 'none', ...
          'FaceLighting', 'none', ...
          'AmbientStrength', 0.7, ...
          'DiffuseStrength', 0.6, ...
          'SpecularStrength', 0.05);

colormap(jet);
cb = colorbar;
caxis([-1 1]);
axis equal;
axis off;
set(gca, 'Color', 'white');

cb.FontName = 'Times New Roman';
cb.FontSize = 26;
ylabel(cb, 'NDVI', 'FontName', 'Times New Roman', 'FontSize', 26);

view(100, 0);
axis vis3d;
axis tight;
set(gca, 'Clipping', 'off');

light('Position', [1 1 1],  'Style', 'infinite');
light('Position', [-1 -1 1], 'Style', 'infinite');

% The data tip reports the NDVI value under the cursor (see ndvi_cursor.m)
dcm = datacursormode(gcf);
set(dcm, 'UpdateFcn', @ndvi_cursor);

%% 7. EXPORT THE RENDER
for i = 1:numel(export_tif_paths)
    exportgraphics(gcf, export_tif_paths{i}, ...
        'BackgroundColor', 'white', ...
        'Resolution', 300);
    fprintf('Render exported: %s\n', export_tif_paths{i});
end

%% 8. EXPORT THE CLEANED OBJ (back into Metashape)
fid = fopen(out_obj, 'w');

% Vertices
for i = 1:size(vertices_clean, 1)
    fprintf(fid, 'v %.6f %.6f %.6f\n', ...
        vertices_clean(i,1), vertices_clean(i,2), vertices_clean(i,3));
end

% Faces
for i = 1:size(faces_clean, 1)
    fprintf(fid, 'f %d %d %d\n', ...
        faces_clean(i,1), faces_clean(i,2), faces_clean(i,3));
end

fclose(fid);
fprintf('OBJ exported: %s\n', out_obj);
