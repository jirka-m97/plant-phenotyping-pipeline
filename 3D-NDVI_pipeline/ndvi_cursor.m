function txt = ndvi_cursor(~, event)
% NDVI_CURSOR  Data cursor callback that adds the NDVI value to the data tip.
%
%   Used in NDVI_3D_model.m:
%       dcm = datacursormode(gcf);
%       set(dcm, 'UpdateFcn', @ndvi_cursor);
%
%   Returns a cell array of the lines shown in the data tip bubble: the X, Y
%   and Z coordinates of the picked point and the NDVI value of the
%   corresponding face/vertex.

    try
        idx   = event.DataIndex;
        cdata = event.Target.FaceVertexCData;
        n_faces = size(cdata, 1);

        % The data tip index can exceed the length of CData (vertices vs.
        % faces), so it is wrapped back into the valid range
        idx_valid = mod(idx - 1, n_faces) + 1;
        ndvi_val  = cdata(idx_valid);

        txt = {sprintf('X: %.4f', event.Position(1)), ...
               sprintf('Y: %.4f', event.Position(2)), ...
               sprintf('Z: %.4f', event.Position(3)), ...
               sprintf('NDVI: %.4f', ndvi_val)};

    catch e
        % If the value cannot be resolved, at least report the coordinates
        fprintf('Error: %s\n', e.message);
        txt = {sprintf('X: %.4f', event.Position(1)), ...
               sprintf('Y: %.4f', event.Position(2)), ...
               sprintf('Z: %.4f', event.Position(3)), ...
               'NDVI: N/A'};
    end
end
