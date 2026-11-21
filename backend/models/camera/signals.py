"""Raw landmark series -> resampled 1D signals (body-relative, independent of camera distance).

series keys (see docs/camera_data_spec.md): t, lm{i}_x/_y/_z (+ lm{i}_v for pose), cueT.
Missing detections are null. Image coordinates are normalized to the (unmirrored) video frame,
so they are scaled by videoW/videoH before any distance or angle is computed.
"""
import numpy as np

from exercises import HAND_FINGERTIPS, HAND_MIDDLE_MCP, HAND_WRIST, POSE

FS = 30.0             # resampling rate [Hz]
MAX_GAP_MS = 250.0    # interpolate over shorter detection gaps, NaN over longer ones


def _arr(series, key):
    return np.array(series.get(key, []), dtype=float)  # None -> nan


def points(series, i, w, h):
    """Landmark i as [N, 2] pixel coordinates (y down)."""
    return np.stack([_arr(series, f"lm{i}_x") * w, _arr(series, f"lm{i}_y") * h], axis=1)


def resample(t, values, fs=FS, max_gap_ms=MAX_GAP_MS):
    """Linear interpolation onto a uniform grid; samples farther than max_gap_ms from valid data -> NaN."""
    t = np.asarray(t, float)
    grid = np.arange(0.0, t[-1] + 1e-9, 1000.0 / fs)
    ok = np.isfinite(values) & np.isfinite(t)
    if ok.sum() < 2:
        return grid, np.full_like(grid, np.nan)
    tv, vv = t[ok], values[ok]
    out = np.interp(grid, tv, vv)
    idx = np.clip(np.searchsorted(tv, grid), 1, len(tv) - 1)
    gap = tv[idx] - tv[idx - 1]
    near = np.minimum(np.abs(grid - tv[idx - 1]), np.abs(tv[idx] - grid))
    out[(gap > max_gap_ms) & (near > max_gap_ms / 2)] = np.nan
    out[(grid < tv[0]) | (grid > tv[-1])] = np.nan
    return grid, out


def smooth(x, k=5):
    """Moving average that ignores NaN."""
    m = np.isfinite(x)
    ker = np.ones(k)
    num = np.convolve(np.where(m, x, 0.0), ker, "same")
    den = np.convolve(m.astype(float), ker, "same")
    with np.errstate(invalid="ignore", divide="ignore"):
        out = num / den
    out[~m] = np.nan
    return out


def hand_openness(series, w, h):
    """Mean fingertip-to-wrist distance / palm length (wrist -> middle-finger knuckle). ~1 fist, ~2 open."""
    wrist = points(series, HAND_WRIST, w, h)
    palm = np.linalg.norm(points(series, HAND_MIDDLE_MCP, w, h) - wrist, axis=1)
    tips = np.mean([np.linalg.norm(points(series, i, w, h) - wrist, axis=1) for i in HAND_FINGERTIPS], axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return tips / palm


def points3d(series, i):
    """MediaPipe world landmark i as [N, 3] (metres, hand-centred, independent of image position)."""
    return np.stack([_arr(series, f"w{i}_{a}") for a in "xyz"], axis=1)


def hand_openness_3d(series):
    """Same ratio as hand_openness, but from 3D world landmarks: robust to the hand tilting towards the
    camera (2D makes a tilted fist look half-open). ~0.75 fist, ~1.5 open."""
    wrist = points3d(series, HAND_WRIST)
    palm = np.linalg.norm(points3d(series, HAND_MIDDLE_MCP) - wrist, axis=1)
    tips = np.mean([np.linalg.norm(points3d(series, i) - wrist, axis=1) for i in HAND_FINGERTIPS], axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return tips / palm


def _angle_deg(a, b):
    cos = np.sum(a * b, axis=1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def arm_signals(series, side, w, h):
    """Per-frame arm signals for one side ("left"/"right" = the subject's side).

    abduction  angle between upper arm and the trunk axis [deg]; 0 = arm down, 90 = horizontal, 180 = overhead.
               Trunk axis = perpendicular to the shoulder line (hips are often hidden by the desk).
    height     wrist height above the shoulder / shoulder width (negative = below the shoulder).
    tilt       shoulder-line tilt [deg], + = tested shoulder higher (lateral trunk lean / hiking show up here).
    ear_gap    vertical shoulder-to-ear distance / shoulder width (drops when the shoulder is hiked).
    """
    other = "left" if side == "right" else "right"
    sh = points(series, POSE[f"{side}_shoulder"], w, h)
    sh_o = points(series, POSE[f"{other}_shoulder"], w, h)
    el = points(series, POSE[f"{side}_elbow"], w, h)
    wr = points(series, POSE[f"{side}_wrist"], w, h)
    ear = points(series, POSE[f"{side}_ear"], w, h)
    line = sh_o - sh
    width = np.linalg.norm(line, axis=1)
    down = np.stack([-line[:, 1], line[:, 0]], axis=1)  # perpendicular to the shoulder line ...
    down *= np.where(down[:, 1:2] >= 0, 1.0, -1.0)      # ... pointing down the image (y down)
    with np.errstate(invalid="ignore", divide="ignore"):
        return {
            "abduction": _angle_deg(el - sh, down),
            "height": (sh[:, 1] - wr[:, 1]) / width,
            "tilt": np.degrees(np.arctan2(line[:, 1], np.abs(line[:, 0]))),
            "ear_gap": (sh[:, 1] - ear[:, 1]) / width,
        }


def visibility(series, idx):
    """Mean pose visibility of the given landmarks per frame (hand has no visibility -> 1 where detected)."""
    vals = [_arr(series, f"lm{i}_v") for i in idx]
    if not len(vals[0]):
        return np.isfinite(_arr(series, f"lm{idx[0]}_x")).astype(float)
    return np.nanmean(np.stack(vals), axis=0)
