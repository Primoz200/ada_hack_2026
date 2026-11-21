"""Preprocessing of one tracer attempt (GameResult) -> hand-made features + time sequence.

Used by both models (training) and by score_session (inference), so it must only use what the
frontend actually sends: level, durationMs, completed, series{t, x, y, strokeId} (x, y in 0-1).

Steps
-----
1. Coordinates 0-1 -> level units 0-1000 (same as shared/tracer_levels.json).
2. Resample on a fixed time grid (GRID_HZ). Inside a stroke, gaps in t mean the pointer was still
   (no events), so the position is held; between strokes the button was up (down = 0).
3. For every grid point: distance to the path, signed lateral deviation, progress along the path.
4. Features are relative to the channel width / path length where possible, so one model fits all
   levels; the level itself is also a model input.
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.signal import welch

from levels import CANVAS_UNITS, Level

GRID_HZ = 50.0
HOLD_GAP_MS = 60.0  # gaps longer than this inside a stroke = pointer standing still
PAUSE_SPEED = 15.0  # units/s of progress along the path below which the patient counts as stopped
SEQ_CHANNELS = ["lateral", "dist", "progress", "prog_speed", "down"]

FEATURE_NAMES = [
    "dev_rms", "dev_mean", "dev_p90", "dev_max", "pct_outside",
    "lat_hf_rms", "tremor_ratio",
    "coverage", "completed", "duration_s", "time_ratio",
    "prog_speed", "prog_speed_cv", "pause_frac", "n_pauses", "n_lifts", "up_frac",
    "path_ratio", "sparc", "ldlj",
]


def parse(series: dict, level: Level):
    t = np.asarray(series["t"], dtype=float)
    xy = np.column_stack([series["x"], series["y"]]).astype(float) * CANVAS_UNITS
    stroke = np.asarray(series.get("strokeId", np.zeros(len(t))), dtype=int)
    order = np.argsort(t, kind="stable")
    return t[order], xy[order], stroke[order]


def resample(t, xy, stroke, duration_ms=None):
    """Fixed-rate grid. Returns grid_t [s], xy [n,2], down [n] (bool)."""
    end = max(float(t[-1]), float(duration_ms or 0.0))
    g = np.arange(0.0, end + 1e-9, 1000.0 / GRID_HZ)
    if len(t) < 2:
        return g / 1000.0, np.repeat(xy[:1], len(g), 0), np.zeros(len(g), bool)
    i = np.clip(np.searchsorted(t, g, side="right") - 1, 0, len(t) - 1)  # last sample at or before g
    j = np.minimum(i + 1, len(t) - 1)
    span = t[j] - t[i]
    w = np.where((span > 0) & (span <= HOLD_GAP_MS), (g - t[i]) / np.maximum(span, 1e-9), 0.0)
    w = np.clip(w, 0.0, 1.0)[:, None]
    out = xy[i] * (1 - w) + xy[j] * w  # linear inside dense data, hold over gaps
    down = (stroke[i] == stroke[j]) | (g >= t[-1])  # in a gap between two strokes = button up
    down &= g >= t[0]
    return g / 1000.0, out, down


def path_coords(level: Level, xy):
    """Distance to the path, signed lateral deviation (+ = along the path normal) and arc position."""
    d, s = level.distance_to_path(xy)
    p, n = level.point_at(s)
    lateral = np.einsum("ij,ij->i", xy - p, n)
    closed = np.hypot(*(level.xy[0] - level.xy[-1])) < 1.0
    if closed:  # circle: start == end, nearest-point arc position wraps around
        s = np.unwrap(s / level.length * 2 * np.pi) / (2 * np.pi) * level.length
        s = s - np.floor(s[0] / level.length + 0.5) * level.length  # start near s = 0
    return d, lateral, np.clip(s, 0.0, level.length)


def sparc(speed, fs, fc=10.0, amp_th=0.05, pad=4):
    """Spectral arc length (Balasubramanian 2012/2015); closer to 0 = smoother."""
    if len(speed) < 8 or speed.max() <= 0:
        return 0.0
    nfft = int(2 ** (np.ceil(np.log2(len(speed))) + pad))
    f = np.arange(nfft) * fs / nfft
    mag = np.abs(np.fft.fft(speed, nfft))
    mag = mag / (mag.max() + 1e-12)
    sel = f <= fc
    f, mag = f[sel], mag[sel]
    above = np.nonzero(mag >= amp_th)[0]
    if len(above) < 2:
        return 0.0
    f, mag = f[: above[-1] + 1], mag[: above[-1] + 1]
    df = np.diff(f) / (f[-1] - f[0] + 1e-12)
    return float(-np.sum(np.sqrt(df ** 2 + np.diff(mag) ** 2)))


def ldlj(xy, fs):
    """Log dimensionless jerk of the (smoothed) trajectory; more negative = jerkier."""
    if len(xy) < 10:
        return 0.0
    xs = gaussian_filter1d(xy, 2.0, axis=0)
    v = np.gradient(xs, 1 / fs, axis=0)
    j = np.gradient(np.gradient(v, 1 / fs, axis=0), 1 / fs, axis=0)
    T = len(xy) / fs
    vpeak = np.hypot(*v.T).max()
    if vpeak <= 0:
        return 0.0
    return float(-np.log(T ** 3 / vpeak ** 2 * np.sum(np.sum(j ** 2, axis=1)) / fs + 1e-12))


def preprocess(series: dict, level: Level, duration_ms=None):
    """Everything the features and the CNN need, on the fixed time grid."""
    t, xy, stroke = parse(series, level)
    gt, gxy, down = resample(t, xy, stroke, duration_ms)
    d, lat, s = path_coords(level, gxy)
    # progress = furthest point reached so far, ignoring single-sample jumps (e.g. near maze corridors)
    progress = np.maximum.accumulate(median_filter(s, size=int(0.3 * GRID_HZ) | 1, mode="nearest"))
    prog_speed = np.gradient(gaussian_filter1d(s, 0.1 * GRID_HZ), 1 / GRID_HZ)  # units/s along the path
    return dict(t=gt, xy=gxy, down=down, dist=d, lateral=lat, s=s, progress=progress,
                prog_speed=prog_speed, n_strokes=int(stroke.max() - stroke.min() + 1) if len(stroke) else 0,
                raw_xy=xy)


def extract_features(pre: dict, level: Level, completed: bool) -> dict:
    cw, L, fs = level.channel_width, level.length, GRID_HZ
    dn = pre["down"]
    d, lat = pre["dist"][dn], pre["lateral"][dn]
    if len(d) == 0:
        d = lat = np.zeros(1)
    duration = float(pre["t"][-1]) if len(pre["t"]) else 0.0

    # coverage: share of the path (in 2 % bins) passed within the channel
    bins = np.zeros(50, bool)
    ok = dn & (pre["dist"] <= cw)
    bins[np.clip((pre["s"][ok] / L * 50).astype(int), 0, 49)] = True
    coverage = float(bins.mean())

    # lateral jitter: high-passed lateral deviation (> ~2 Hz) and the 4-8 Hz tremor share of its power
    hf = lat - gaussian_filter1d(lat, fs / (2 * np.pi * 2.0))
    if len(lat) >= 64:
        f, pxx = welch(lat - lat.mean(), fs=fs, nperseg=min(256, len(lat)))
        band = (f >= 4) & (f <= 8)
        tremor_ratio = float(pxx[band].sum() / (pxx[f >= 1].sum() + 1e-12))
    else:
        tremor_ratio = 0.0

    ps = pre["prog_speed"][dn]
    moving = ps > PAUSE_SPEED
    stopped = dn & (pre["prog_speed"] <= PAUSE_SPEED)
    # pause episodes >= 0.2 s
    edges = np.diff(np.concatenate([[0], stopped.astype(int), [0]]))
    lens = np.nonzero(edges == -1)[0] - np.nonzero(edges == 1)[0]
    n_pauses = int((lens >= 0.2 * fs).sum())

    raw = pre["raw_xy"]
    drawn = float(np.hypot(*np.diff(raw, axis=0).T).sum()) if len(raw) > 1 else 0.0
    passed = float(pre["progress"][-1]) if len(pre["progress"]) else 0.0

    return {
        "dev_rms": float(np.sqrt(np.mean(d ** 2)) / cw),
        "dev_mean": float(d.mean() / cw),
        "dev_p90": float(np.percentile(d, 90) / cw),
        "dev_max": float(d.max() / cw),
        "pct_outside": float(np.mean(d > cw / 2) * 100),
        "lat_hf_rms": float(np.sqrt(np.mean(hf ** 2)) / cw),
        "tremor_ratio": tremor_ratio,
        "coverage": coverage,
        "completed": float(bool(completed)),
        "duration_s": duration,
        "time_ratio": duration / level.time_limit_s,
        "prog_speed": passed / max(duration, 1e-3),
        "prog_speed_cv": float(ps[moving].std() / (ps[moving].mean() + 1e-9)) if moving.sum() > 5 else 0.0,
        "pause_frac": float(stopped.sum() / max(dn.sum(), 1)),
        "n_pauses": float(n_pauses),
        "n_lifts": float(max(pre["n_strokes"] - 1, 0)),
        "up_frac": float(1.0 - dn.mean()) if len(dn) else 0.0,
        "path_ratio": drawn / max(passed, 1.0),  # >1: wiggles on top of the progress
        "sparc": sparc(np.abs(pre["prog_speed"][dn]), fs),
        "ldlj": ldlj(pre["xy"][dn], fs),
    }


def sequence(pre: dict, level: Level) -> np.ndarray:
    """CNN input [len(SEQ_CHANNELS), T], level-relative and roughly unit-scaled."""
    cw, L = level.channel_width, level.length
    return np.stack([
        np.clip(pre["lateral"] / cw, -3, 3),
        np.clip(pre["dist"] / cw, 0, 3),
        pre["progress"] / L,
        np.clip(pre["prog_speed"] / 250.0, -3, 3),
        pre["down"].astype(float),
    ]).astype(np.float32)
