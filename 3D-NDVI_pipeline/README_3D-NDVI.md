# 3D NDVI — mapping NDVI onto a photogrammetric plant model

MATLAB scripts that turn raw frames from a dual-sensor (RGB + NIR) camera into
radiometrically calibrated four-band composites, feed them into a
photogrammetric reconstruction in Agisoft Metashape, and finally project NDVI
onto the resulting 3D mesh of the plant — first onto the vertices, then as a
mean value per face.

---

| # | Script | What it does |
|---|--------|--------------|
| 1 | `lin_reg_coef.m` | Interactive calibration on a reference target. Computes the white balance coefficients and the linear OECF mapping (image value → reflectance in %) and stores them in a `.mat` file. |
| 2 | `data_analysis.m` | Batch-processes the whole plant image set: bias/dark/flat correction → demosaic (RGGB) → white balance → reflectance → 32-bit float TIFF. |
| 3 | `rename.m` | *Optional.* Shifts the frame numbering by an offset — needed when several sets are merged into one reconstruction. |
| 4 | `tif_4band.m` | Merges `_RGB.tif` (3 bands) and `_NIR.tif` (1 band) into a single four-band R/G/B/NIR composite. |
| — | *Metashape* | Photogrammetric reconstruction from the four-band images. The finished project yields the **model as `.obj`** and **`cameras.txt` holding the exterior and interior camera orientation**. |
| 5 | `NDVI_3D_model.m` | Back-projects the mesh vertices into the images, reads out NDVI and averages it over the cameras. Renders the result, filters out the background, computes NDVI per face and exports the render plus a cleaned OBJ. |
| — | `ndvi_cursor.m` | Helper function — a data tip that reports the NDVI value under the cursor. |

---

## Requirements

- MATLAB (tested on R2022+), toolboxes: **Image Processing Toolbox**
- Agisoft Metashape (photogrammetry, outside MATLAB)
- Input raw frames: `uint8`, 2048 × 1536, **RGGB** Bayer pattern
- Calibration frame sets: **bias**, **dark**, **flat** — separately for the RGB
  and NIR sensor (told apart by the `RGB` / `NIR` substring in the file name)

---

## How to run it

Every script starts with a **`SETTINGS`** / **`PATHS`** cell that gathers all
paths and parameters you need to edit. No paths are hidden anywhere else in the
code.

**1) Calibration** — once per camera/lens configuration:

```matlab
lin_reg_coef
```

The script opens a sequence of windows and waits for you to drag a rectangle:
the white/grey reference card (RGB) → five chips of the RGB target → the NIR
reference card → five chips of the NIR target. It finishes by printing gains,
biases and **R²**; if R² drops noticeably below 0.99, repeat the chip
selection. The output is `P6.mat`.

> The struct name inside the `.mat` file **must end with `_koefs`** — that is
> how `data_analysis.m` locates it.

**2) Reflectance** — for each image set:

```matlab
data_analysis
```

Results are written to `<input_folder>\reflectance_output\`.

**3) Renumbering** *(only when merging several sets)*:

```matlab
rename
```

**4) Composites for Metashape:**

```matlab
tif_4band
```

**5) Metashape** — photogrammetric reconstruction from the four-band TIFFs.
Once the model has been generated, **two exports** are taken from the project;
the next step cannot run without them:

**a) The object itself in `.obj` format** — the triangular mesh of the plant
(*File → Export → Export Model*). The script reads only the `v` (vertex) and
`f` (face) lines; textures and normals are not needed.

**b) The camera orientations as a text file, `cameras.txt`** — carrying both
the **exterior and interior orientation** of every image:

- **exterior orientation** — position of the projection centre `x, y, z` and
  the rotation matrix `r11 … r33` (camera attitude in the world coordinate
  system),
- **interior orientation** — focal lengths `fx, fy` and the principal point
  `cx, cy` (Metashape reports it as an offset from the image centre, which is
  why the code adds `W/2` and `H/2`).

The export is done with the `cameras_TXT_Metashape_export.txt` script run from
the Metashape console. The resulting table must contain the columns:

```
label  x y z  r11 r12 r13 r21 r22 r23 r31 r32 r33  fx fy  cx cy
```

The `label` value has to match the name of the four-band TIFF without its
extension — `NDVI_3D_model.m` pairs cameras with images through it. In the
script settings the file is expected as `cameras_final.txt` (variable
`cam_file`).

**6) NDVI on the model:**

```matlab
NDVI_3D_model
```

The script is split into cells (`%%`) and can be run step by step
(Ctrl+Enter in the editor):

- **1–3** — load the mesh and cameras, run the NDVI projection *(always required)*
- **4** — quick preview of the full mesh
- **5** — background removal using the `ndvi_threshold` value
- **6** — mean NDVI per face plus the final render with a colour bar
- **7–8** — export of the render (300 dpi) and of the filtered OBJ

---

## How the NDVI projection works

For every camera, all mesh vertices are transformed into camera coordinates
(`pt_cam = R' * (X - C)`) and projected into the image with a pinhole model:

```
u = fx · x/z + cx      v = fy · y/z + cy
```

NDVI = (NIR − R) / (NIR + R) is read from pixel `[v, u]`. Only vertices in
front of the camera (`z > 0`) and inside the image extent are used. The values
are accumulated across all cameras and divided by the number of cameras that
saw the vertex. The NDVI of a face is then the plain mean of its three
vertices.
