import os
import math
import time
import json
import requests
import Metashape
import tkinter as tk
import traceback

# ==========================
# Load & validate config
# ==========================
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# REQUIRED keys: core I/O + crop/cuvette parameters (used by cut_cuvette)
REQUIRED_KEYS = [
    "SOURCE_FOLDER_PATH",
    "RESULTS_FOLDER_PATH",
    "PROJECT_NAME",
    "CENTER_X",
    "CENTER_Y",
    "RADIUS",
    "Z_MIN",
    "Z_MAX",
    "Z_LIM"
]
missing = [k for k in REQUIRED_KEYS if config.get(k) in (None, "")]
if missing:
    raise KeyError(f"Missing required keys in config.json: {missing}")

# -----------------------
# Global variables
# -----------------------
reference_file_path = config.get("CONTROL_POINTS_COORDINATES")  # may be None
main_folder = config["SOURCE_FOLDER_PATH"]
output_base_path = config["RESULTS_FOLDER_PATH"]
project_name = config["PROJECT_NAME"]
output_project_path = os.path.join(output_base_path, f"{project_name}.psx")
metrics_path = os.path.join(output_base_path, f"{project_name}_cut_metrics.txt")  # single text file with CUT metrics

# Optional post-processing parameters (with sane defaults)
SMOOTHING = int(config.get("SMOOTHING", 1))
COMPONENT_SIZE = int(config.get("COMPONENT_SIZE", 100000))
HOLES_SIZE = int(config.get("HOLES_SIZE", 100))

# Optional tweaks (None => keep Metashape defaults)
def tweak_set(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip())
    except Exception:
        return None

tweak_1 = tweak_set(config.get("TWEAK_1"))
tweak_2 = tweak_set(config.get("TWEAK_2"))

doc = Metashape.Document()

# -------------
# Logging helpers
# -------------
def log(*args):   print("[INFO]", *args)
def debug(*args): print("[DEBUG]", *args)
def error(*args): print("[ERROR]", *args)

# --------------------------------
# Import sensor calibration (XML)
# --------------------------------
def import_calibration(chunk, config):
    """
    Loads user calibration from XML and assigns it to the first sensor in the chunk.
    Call after addPhotos(), before alignCameras().
    """
    calib_path = config.get("CALIBRATION_FILE")
    if calib_path and os.path.isfile(calib_path):
        if not chunk.cameras:
            log("No cameras in chunk – skipping calibration.")
            return
        try:
            debug(f"Loading calibration: {calib_path}")
            if not chunk.sensors:
                log("No sensors in chunk – skipping calibration.")
                return
            sensor = chunk.sensors[0]
            calib = Metashape.Calibration()
            calib.width, calib.height = sensor.width, sensor.height
            calib.load(calib_path, format=Metashape.CalibrationFormatXML)
            sensor.user_calib = calib
            cur = sensor.calibration
            debug("Focal length (f):", getattr(cur, "f", None))
            debug("Principal point cx:", getattr(cur, "cx", None))
            debug("Principal point cy:", getattr(cur, "cy", None))
            log("Calibration assigned successfully.")
        except Exception as e:
            error("Calibration import failed:", e)
            log(traceback.format_exc())
    else:
        log("Calibration file is not set or does not exist – skipping calibration import.")

# ------------------------------------
# Markers / reference and transform
# ------------------------------------
def read_reference_coordinates(file_path):
    """
    Reads reference coordinates (tab separated file: ID \t X \t Y \t Z).
    Returns: dict {marker_label: Metashape.Vector([x, y, z])}
    """
    reference_coords = {}
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split('\t')
            if len(parts) != 4:
                print(f"Invalid line format: {line}")
                continue
            marker_id = parts[0].strip()
            try:
                x, y, z = map(float, parts[1:])
                reference_coords[marker_id] = Metashape.Vector([x, y, z])
            except ValueError:
                print(f"Error parsing coordinates for marker {marker_id}: {parts[1:]}")
    return reference_coords

def assign_marker_coordinates(chunk, reference_coords):
    """
    Assigns reference XYZ to detected markers in the chunk by label.
    """
    for marker in chunk.markers:
        marker_id = marker.label.strip()
        if marker_id in reference_coords:
            marker.reference.location = reference_coords[marker_id]
            marker.reference.enabled = True
            print(f"Assigned coordinates {reference_coords[marker_id]} to marker {marker_id}.")
        else:
            print(f"Marker ID {marker_id} not found in reference data.")

def coordinate_assignment_complete(chunk, path):
    """
    Sets CRS to local (meters), imports reference coordinates and updates chunk transform.
    """
    chunk_name = chunk.label
    print(f"Processing chunk: {chunk_name}")
    chunk.crs = Metashape.CoordinateSystem('LOCAL_CS["Local CS", LOCAL_DATUM["Local Datum", 0], UNIT["metre", 1]]')
    reference_coords = read_reference_coordinates(path)
    assign_marker_coordinates(chunk, reference_coords)
    chunk.updateTransform()
    print("Chunk transform updated.")

# -------------------------------
# Region (Bounding Box)
# -------------------------------
def set_chunk_region(chunk):
    """
    Sets a generic region (BBox) based on current transform and CRS.
    """
    T = chunk.transform.matrix
    v_t = T.mulp(Metashape.Vector([0, 0, 0]))
    if chunk.crs:
        m = chunk.crs.localframe(v_t)
    else:
        m = Metashape.Matrix().Diag([1, 1, 1, 1])
    m = m * T
    scale = math.sqrt(m[0,0]**2 + m[0,1]**2 + m[0,2]**2)
    R = Metashape.Matrix([[m[0,0], m[0,1], m[0,2]],
                          [m[1,0], m[1,1], m[1,2]],
                          [m[2,0], m[2,1], m[2,2]]]) * (1.0/scale)
    geo_size = Metashape.Vector([190, 190, 180])
    geo_center = Metashape.Vector([0, 0, 160])
    region = Metashape.Region()
    region.rot = R.t()
    region.size = geo_size / scale
    region.center = T.inv().mulp(geo_center)
    chunk.region = region

# -------------------------------------------------------
# Switch active model by label (after BuildModel in main)
# -------------------------------------------------------
def ensure_adjusted_model_active(chunk, config):
    """
    If a model labeled as config['ADJUSTED_MODEL_NAME'] exists, set it active.
    Logs available models and the current one.
    """
    try:
        if not getattr(chunk, "model", None):
            error("Clean skipped: no active model.")
            return False
        models = getattr(chunk, "models", None)
        if models is None:
            debug("Chunk has no 'models' attribute.")
            debug("Active model:", chunk.model.label if chunk.model else None)
            return True

        for m in (models or []):
            prefix = "***" if (chunk.model and m.key == chunk.model.key) else "   "
            debug(prefix, "Model: key:", getattr(m, "key", None), ", label:", getattr(m, "label", None))
        debug("Active model:", chunk.model.label if chunk.model else None)

        target_label = config.get("ADJUSTED_MODEL_NAME", "adjusted")
        if chunk.model and chunk.model.label == target_label:
            debug("Active model already equals:", target_label)
            return True
        for m in (models or []):
            if getattr(m, "label", None) == target_label:
                chunk.model = m
                debug("Active model switched to:", chunk.model.label)
                return True
        debug(f"Model '{target_label}' not found – keeping current:", chunk.model.label)
        return False
    except Exception as e:
        error("ensure_adjusted_model_active failed:", e)
        log(traceback.format_exc())
        return False

# ------------------------------------------
# Duplicate chunk: keep original + cut copy
# ------------------------------------------
def duplicate_chunk_for_cut(doc, chunk, suffix_orig="-orig", suffix_cut="-cut"):
    """
    Renames the original chunk to *-orig, creates an exact copy *-cut, and returns the cut chunk.
    """
    try:
        base_label = chunk.label
        if not base_label.endswith(suffix_orig) and not base_label.endswith(suffix_cut):
            chunk.label = f"{base_label} {suffix_orig}"
        else:
            debug("Chunk already appears renamed, keeping:", chunk.label)
        cut_chunk = chunk.copy()
        root = base_label.replace(suffix_orig, "").replace(suffix_cut, "").strip()
        cut_chunk.label = f"{root} {suffix_cut}"
        log(f"Chunk duplicated: '{chunk.label}' (original), '{cut_chunk.label}' (cut).")
        return cut_chunk
    except Exception as e:
        error("Chunk duplication failed:", e)
        log(traceback.format_exc())
        return None

# ---------------------------------------------------
# Cylindrical crop + remove below Z_LIM (CUT model)
# ---------------------------------------------------
def cut_cuvette(chunk):
    """
    Duplicates the active model as 'cut' (label overridable via CUT_MODEL_NAME) and
    removes faces outside cylinder [CENTER_X, CENTER_Y, RADIUS] in Z range [Z_MIN, Z_MAX],
    and anything below Z_LIM. All in chunk CRS.
    """
    try:
        if not chunk.model:
            error("Cut skipped: no active model.")
            return False

        new_model = chunk.model.copy()
        new_model.label = config.get("CUT_MODEL_NAME", "cut")
        chunk.model = new_model

        cx = float(config["CENTER_X"]); cy = float(config["CENTER_Y"])
        radius = float(config["RADIUS"])
        bottom_z = float(config["Z_MIN"]); top_z = float(config["Z_MAX"])
        z_lim = float(config["Z_LIM"])

        T = chunk.transform.matrix
        crs = chunk.crs

        count_sel = 0
        total = len(new_model.faces)

        for face in new_model.faces:
            inside_cyl = True
            below_lim = False
            for vid in face.vertices:
                local = new_model.vertices[vid].coord
                geoc = T.mulp(local)
                if crs:
                    geo = crs.project(geoc); x, y, z = geo.x, geo.y, geo.z
                else:
                    x, y, z = geoc.x, geoc.y, geoc.z
                dx, dy = x - cx, y - cy
                if not (dx*dx + dy*dy <= radius*radius and bottom_z <= z <= top_z):
                    inside_cyl = False
                if z < z_lim:
                    below_lim = True
            if inside_cyl and (not below_lim):
                face.selected = True; count_sel += 1
            else:
                face.selected = False

        debug(f"Faces selected for removal: {count_sel} / {total}")
        new_model.removeSelection()
        debug("Faces after removal:", len(new_model.faces))
        return True
    except Exception as e:
        error("Cutting cuvette failed:", e)
        log(traceback.format_exc())
        return False

# -----------------------------------------
# Height in CRS + surface/volume of the mesh
# -----------------------------------------
def calculate_height_crs(chunk, model=None):
    """
    Returns height (maxZ - minZ) in chunk CRS, transforming vertices with chunk.transform.
    """
    m = model or chunk.model
    if not m:
        return None
    T = chunk.transform.matrix
    crs = chunk.crs
    min_z, max_z = float("inf"), float("-inf")
    for v in m.vertices:
        geoc = T.mulp(v.coord)
        z = crs.project(geoc).z if crs else geoc.z
        if z < min_z: min_z = z
        if z > max_z: max_z = z
    return max_z - min_z

def compute_area_volume(model):
    """
    Returns (area, volume). volume is absolute value to ignore normal orientation.
    """
    if not model:
        return (None, None)
    try:
        area = float(model.area())
    except Exception:
        area = None
    try:
        vol = float(model.volume())
        volume = abs(vol)
    except Exception:
        volume = None
    return (area, volume)

# ---------------
# Notification
# ---------------
def notification(project_name, dur_s, dur_m, dur_h):
    WEBHOOK_URL = "https://discord.com/api/webhooks/..."
    data = {"content": f'Project "{project_name}" finished successfully! Duration: {dur_s} s ({dur_m} m, {dur_h} h).'}
    try:
        response = requests.post(WEBHOOK_URL, json=data, timeout=10)
        if response.status_code == 204:
            print("Notification sent to Discord.")
        else:
            print(f"Notification failed: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Notification could not be sent: {e}")

# =====================
# Main evaluation loop
# =====================
s = time.time()

# Prepare metrics file header (once)
if not os.path.isfile(metrics_path):
    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write("chunk\tH[m]\tS[m2]\tV[m3]\n")

for folder_name in os.listdir(main_folder):
    s_indiv = time.time()
    folder_path = os.path.join(main_folder, folder_name)
    if not os.path.isdir(folder_path):
        continue

    chunk = doc.addChunk()
    chunk.label = folder_name

    # Add photos
    image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff'))]
    if image_files:
        chunk.addPhotos(image_files)

    # Calibration before alignment
    import_calibration(chunk, config)

    # Alignment
    chunk.matchPhotos(downscale=1, generic_preselection=True, reference_preselection=False,
                      filter_stationary_points=True, keypoint_limit=0, keypoint_limit_per_mpx=1000,
                      tiepoint_limit=0)
    chunk.alignCameras(adaptive_fitting=True)

    # Markers + transform + region (only if control points file exists)
    if reference_file_path and os.path.isfile(reference_file_path):
        chunk.detectMarkers(target_type=Metashape.CircularTarget12bit, tolerance=69)
        coordinate_assignment_complete(chunk, reference_file_path)
        set_chunk_region(chunk)
    else:
        log("CONTROL_POINTS_COORDINATES not set or file does not exist – skipping reference points.")

    # Depth maps + model build
    chunk.buildDepthMaps(downscale=1, filter_mode=Metashape.MildFiltering, reuse_depth=True)

    task = Metashape.Tasks.BuildModel()
    if tweak_1 is not None:
        task["ooc_surface_blow_up"] = tweak_1
    if tweak_2 is not None:
        task["ooc_surface_blow_off"] = tweak_2
    task.surface_type = Metashape.Arbitrary
    task.source_data = Metashape.DepthMapsData
    task.vertex_confidence = True
    task.keep_depth = True
    task.apply(chunk)  # -> original model lives here

    # Optionally switch active model by name (if you use a named intrinsics-adjusted model)
    ensure_adjusted_model_active(chunk, config)

    # Duplicate chunk and crop only in the copy
    cut_chunk = duplicate_chunk_for_cut(doc, chunk, suffix_orig="-orig", suffix_cut="-cut")
    if cut_chunk:
        ensure_adjusted_model_active(cut_chunk, config)
        if cut_chunk.model:
            ok = cut_cuvette(cut_chunk)
            if not ok:
                log("Cut cuvette: proceeding without crop (cut chunk).")
            cut_chunk.smoothModel(strength=SMOOTHING)
            cut_chunk.model.removeComponents(COMPONENT_SIZE)
            cut_chunk.model.closeHoles(HOLES_SIZE)

            # --- CUT metrics: height, surface, volume (append to one TXT) ---
            height = calculate_height_crs(cut_chunk, cut_chunk.model)
            area, volume = compute_area_volume(cut_chunk.model)

            def _fmt(x, nd=3):
                return "NA" if x is None else f"{x:.{nd}f}"

            with open(metrics_path, "a", encoding="utf-8") as f:
                f.write(f"{cut_chunk.label}\t{_fmt(height)}\t{_fmt(area)}\t{_fmt(volume)}\n")

            log(f"Metrics (H,S,V) written: {metrics_path}  (chunk '{cut_chunk.label}')")
    else:
        log("Cut chunk copy was not created; keeping original only for this iteration.")

    # Save project (incremental)
    doc.save(output_project_path)
    print(f"Project saved: {output_project_path}")

    # Time log per folder
    e_indiv = time.time()
    duration_indiv = e_indiv - s_indiv
    with open(os.path.join(output_base_path, f"{project_name}_times.txt"), "a", encoding="utf-8") as file:
        file.write(f"{folder_name}: {duration_indiv/3600:.4f} h, {duration_indiv/60:.4f} min, {duration_indiv:.3f} s.\n")

# Final save & notification
Metashape.app.update()
doc.save(output_project_path)

e = time.time()
duration = e - s
notification(project_name, round(duration,3), round(duration/60,4), round(duration/3600,4))

