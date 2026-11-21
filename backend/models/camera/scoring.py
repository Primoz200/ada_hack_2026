"""Rule-based scoring of one camera recording against the healthy reference (no ML).

Principles (agreed 2026-11-21):
  * POSITION is the main signal: how far the hand opens / closes, how high the arm gets.
  * Going beyond the reference (higher arm, wider opening, tighter fist) is never penalised (capped at 100 %).
  * Timing is NOT scored (patients may be too fast or off-beat); only whether all repetitions were done.
    Timing lag / jitter are still reported as features for the clinician.
  * Within the natural healthy variation (reference sd, at least 5 % of the movement span) = full marks.

measure()        raw series -> flat features (dict[str, float]) + per-repetition detail
combine()        detail + reference -> score 0-100 and breakdown (each component 0-1)
score_camera()   score_session-compatible entry point
"""
import json
import os
import warnings
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks

from exercises import EXERCISES, POSE, cue_times_ms
from signals import FS, arm_signals, hand_openness, hand_openness_3d, resample, smooth, visibility, _arr

warnings.filterwarnings("ignore", category=RuntimeWarning)  # all-NaN frames (dropped detections) are expected
HERE = Path(__file__).resolve().parent
# CAMERA_DATA_DIR (tests): recordings + reference go there instead of the project folders
TEST_DIR = os.environ.get("CAMERA_DATA_DIR")
REFERENCE_FILE = Path(TEST_DIR) / "camera_reference.json" if TEST_DIR else HERE / "artifacts" / "camera_reference.json"
MODEL_VERSION = "camera-rules-0.3"
CLASSES = ["normal", "mild", "moderate", "severe"]
THRESHOLDS = (85, 65, 40)  # same as tracer (backend/models/tracer/common.py)

MIN_DETECT_FRAC = 0.8      # quality: share of frames with a detection
MIN_FPS = 15.0             # quality: camera frame rate
MIN_TOP_VISIBILITY = 0.5   # quality (arms): wrist visibility at the top of the movement (arm left the frame?)
TOL_MIN_FRAC = 0.05        # tolerance at least 5 % of the reference movement span

WEIGHTS = {
    "hand": {"position": 0.85, "reps": 0.15},  # position = geometric mean of open and close
    "arm": {"position": 0.85, "reps": 0.15},
}
PENALTY = {  # arms only: compensation beyond reference + allowance, full penalty at allowance + span
    "lean": {"allow": 5.0, "span": 15.0, "max": 0.20},   # lateral trunk lean [deg]
    "hike": {"allow": 0.10, "span": 0.30, "max": 0.10},  # shoulder hiking [shoulder widths]
}
MIN_PROMINENCE = {"hand": 0.10, "shoulder_abduction": 10.0, "arm_raise": 0.20}
MIN_REP_FRAC = 0.25        # a repetition counts only if the movement covers >= 25 % of the healthy span
# Strictness: share of the healthy movement that still gives 0 points for position (linear up to 100 % = full).
# Hand 0.5 = reaching only half of the healthy opening / closing scores 0 (small hand deficits matter clinically).
ZERO_AT = {"hand": 0.5, "arm": 0.25}


def score_to_class(score):
    for c, th in zip(CLASSES, THRESHOLDS):
        if score >= th:
            return c
    return "severe"


def _med(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(np.median(x)) if len(x) else float("nan")


def _pct(x, q):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(np.percentile(x, q)) if len(x) else float("nan")


def _clean(v):
    """float, or None for missing/NaN (keeps the result JSON-compliant)."""
    return float(v) if v is not None and np.isfinite(v) else None


def _extrema(x, min_prom, min_dist_s, sign=1):
    """Indices of peaks (sign=1) or troughs (sign=-1); prominence relative to the signal's own spread,
    but never below min_prom (so sensor noise of a motionless patient is not counted as repetitions)."""
    if not np.isfinite(x).any():
        return np.array([], int)
    spread = _pct(x, 95) - _pct(x, 5)
    xf = np.where(np.isfinite(x), sign * x, np.nanmin(sign * x))
    pk, _ = find_peaks(xf, prominence=max(0.3 * spread, min_prom), distance=max(1, int(min_dist_s * FS)))
    return pk


def count_phases(x, lo, hi, min_s=0.2):
    """Number of 'up' phases (signal rises above hi after having been below lo, or starts above hi),
    lasting at least min_s. Hysteresis makes it robust to noise; plateaus at the recording edges count too."""
    state, n, run = None, 0, 0
    for v in x:
        if not np.isfinite(v):
            continue
        if v >= hi:
            run += 1
            if state != "up" and run >= min_s * FS:
                state, n = "up", n + 1
        else:
            run = 0
            if v <= lo:
                state = "down"
    return n


def _quality(series, key_idx):
    t = np.array(series["t"], float)
    present = np.isfinite(_arr(series, f"lm{key_idx[0]}_x"))
    dt = np.diff(t)
    vis = visibility(series, key_idx)
    return {
        "fps": float(1000.0 / np.median(dt)) if len(dt) else 0.0,
        "detect_frac": float(present.mean()) if len(present) else 0.0,
        "visibility": float(np.nanmean(vis)) if np.isfinite(vis).any() else 0.0,
    }


# ---------------- measurement ----------------

def _measure_hand(series, ex, w, h):
    grid, x = resample(series["t"], hand_openness_3d(series))
    x = smooth(x)
    pk = _extrema(x, MIN_PROMINENCE["hand"], 0.4)
    tr = _extrema(x, MIN_PROMINENCE["hand"], 0.4, sign=-1)
    opens = x[pk] if len(pk) else np.array([_pct(x, 95)])
    fists = x[tr] if len(tr) else np.array([_pct(x, 5)])
    # timing (information only): upward crossings of the half-open level vs. the beeps
    mid = 0.5 * (_med(opens) + _med(fists))
    up = np.where((x[:-1] < mid) & (x[1:] >= mid))[0]
    onsets = grid[up]
    cues = np.array(series.get("cueT") or cue_times_ms(ex), float)
    asyn = np.array([onsets[np.argmin(np.abs(onsets - c))] - c for c in cues]) if len(onsets) else np.array([])
    lag = _med(asyn)
    _, x2d = resample(series["t"], hand_openness(series, w, h))
    feats = {
        "open_level": _med(opens),          # typical fully-open hand (fingertips-wrist / palm, 3D)
        "fist_level": _med(fists),          # typical fist
        "open_range": _med(opens) - _med(fists),
        "n_reps": float(count_phases(x, mid - 0.25 * (_med(opens) - _med(fists)),
                                     mid + 0.25 * (_med(opens) - _med(fists)))),  # open phases
        "open_range_2d": _pct(x2d, 95) - _pct(x2d, 5),
        "timing_lag_ms": lag,                                    # info only
        "timing_jitter_ms": _med(np.abs(asyn - lag)) if len(asyn) else float("nan"),  # info only
    }
    detail = {"t": grid, "signal": x, "peaks": pk, "troughs": tr, "opens": opens, "fists": fists, "cues": cues}
    return feats, detail


def _measure_arm(series, ex, hand, w, h):
    main = "abduction" if ex["key"] == "shoulder_abduction" else "height"
    other_side = "left" if hand == "right" else "right"
    sig = {k: smooth(resample(series["t"], v)[1]) for k, v in arm_signals(series, hand, w, h).items()}
    grid = resample(series["t"], np.zeros(len(series["t"])))[0]
    x = sig[main]
    x_o = smooth(resample(series["t"], arm_signals(series, other_side, w, h)[main])[1])
    rest = _pct(x, 10)
    pk = _extrema(x, MIN_PROMINENCE[ex["key"]], 1.0)
    tops = x[pk] if len(pk) else np.array([_pct(x, 95)])
    top = _med(tops)
    up = x > rest + 0.5 * (top - rest)                 # frames in the raised phase
    n_up = count_phases(x, rest + 0.3 * (top - rest), rest + 0.7 * (top - rest))
    down = x < rest + 0.2 * (top - rest)
    rest_tilt, rest_gap = _med(sig["tilt"][down]), _med(sig["ear_gap"][down])
    wv = _arr(series, f"lm{POSE[hand + '_wrist']}_v")
    _, wv = resample(series["t"], wv)
    rest_o = _pct(x_o, 10)
    feats = {
        "top_level": top,                                   # abduction [deg] / wrist height [shoulder widths]
        "rest_level": rest,
        "n_reps": float(n_up),
        "lean_deg": _pct(np.abs(sig["tilt"][up] - rest_tilt), 95) if up.any() else 0.0,
        "hike": _pct(rest_gap - sig["ear_gap"][up], 95) if up.any() else 0.0,
        "top_visibility": _med(wv[up]) if up.any() else 0.0,
        "symmetry": (top - rest) / (_pct(x_o, 95) - rest_o) if _pct(x_o, 95) - rest_o > 0 else float("nan"),
    }
    detail = {"t": grid, "signal": x, "signal_other": x_o, "peaks": pk, "tops": tops, "rest": rest,
              "tilt": sig["tilt"], "ear_gap": sig["ear_gap"],
              "cues": np.array(series.get("cueT") or cue_times_ms(ex), float)}
    return feats, detail


def measure(level, hand, series, client_meta):
    """Flat features (floats / None) + per-repetition detail for scoring and plots."""
    ex = EXERCISES[int(level)]
    w = float(client_meta.get("videoW") or 1280)
    h = float(client_meta.get("videoH") or 720)
    if ex["detector"] == "hand":
        q = _quality(series, [0, 9, 12])
        f, detail = _measure_hand(series, ex, w, h)
        ok = q["detect_frac"] >= MIN_DETECT_FRAC and q["fps"] >= MIN_FPS
    else:
        idx = [POSE[f"{s}_{j}"] for s in ("left", "right") for j in ("shoulder", "elbow")]
        q = _quality(series, idx)
        f, detail = _measure_arm(series, ex, hand, w, h)
        ok = (q["detect_frac"] >= MIN_DETECT_FRAC and q["fps"] >= MIN_FPS
              and (f["top_visibility"] or 0) >= MIN_TOP_VISIBILITY)
    f.update(q)
    f["quality_ok"] = float(ok)
    return {k: _clean(v) for k, v in f.items()}, detail


# ---------------- reference + score ----------------

def load_reference(path=REFERENCE_FILE):
    return json.loads(Path(path).read_text()) if Path(path).exists() else {}


def _ref_for(ref, level, hand):
    """Pooled healthy reference ("any" = both hands); hand-specific only as a fallback."""
    lv = ref.get(str(level), {})
    return lv.get("any") or lv.get(hand)


def _tol(ref, key, span):
    sd = ref["sd"].get(key) or 0.0
    return max(sd, TOL_MIN_FRAC * abs(span))


def _frac(v, zero, full, zero_at=0.0):
    """Share of the healthy movement reached (0 at `zero`, 1 at `full`, beyond = no penalty), then made
    stricter: reaching only `zero_at` of the movement already scores 0."""
    if full == zero:
        return 1.0
    f = np.clip((np.asarray(v, float) - zero) / (full - zero), 0, 1)
    return np.clip((f - zero_at) / (1 - zero_at), 0, 1)


def _penalty(v, ref_v, p):
    if v is None:
        return 0.0
    return float(np.clip((v - (ref_v or 0.0) - p["allow"]) / p["span"], 0, 1))


def combine(level, feats, detail, ref):
    """Score 0-100 + breakdown (each component 0-1, 1 = like a healthy person)."""
    ex = EXERCISES[int(level)]
    m = ref["mean"]
    hand = ex["detector"] == "hand"
    span = m["open_level"] - m["fist_level"] if hand else m["top_level"] - m["rest_level"]
    amp = feats["open_range"] if hand else (feats["top_level"] or 0.0) - (feats["rest_level"] or 0.0)
    moved = (amp or 0.0) >= MIN_REP_FRAC * span
    reps = float(min(1.0, (feats["n_reps"] or 0.0) / ex["n_cues"])) if moved else 0.0
    if hand:
        open_full = m["open_level"] - _tol(ref, "open_level", span)
        fist_full = m["fist_level"] + _tol(ref, "fist_level", span)
        o = float(np.mean(_frac(detail["opens"], m["fist_level"], open_full, ZERO_AT["hand"])))
        c = float(np.mean(_frac(-detail["fists"], -m["open_level"], -fist_full, ZERO_AT["hand"])))
        # both ends needed: a permanent fist (or a permanently open hand) is not half a good movement
        b = {"position": float(np.sqrt(o * c)), "open": o, "close": c, "reps": reps}
        wts = WEIGHTS["hand"]
        score = 100 * sum(wts[k] * b[k] for k in wts)
    else:
        full = m["top_level"] - _tol(ref, "top_level", span)
        b = {
            "position": float(np.mean(_frac(detail["tops"], m["rest_level"], full, ZERO_AT["arm"]))),
            "reps": reps,
            "lean_penalty": _penalty(feats["lean_deg"], m.get("lean_deg"), PENALTY["lean"]),
            "hike_penalty": _penalty(feats["hike"], m.get("hike"), PENALTY["hike"]),
        }
        wts = WEIGHTS["arm"]
        score = 100 * sum(wts[k] * b[k] for k in wts)
        score *= 1 - PENALTY["lean"]["max"] * b["lean_penalty"] - PENALTY["hike"]["max"] * b["hike_penalty"]
    return float(np.clip(score, 0, 100)), b


def score_camera(game_type, level, hand, duration_ms, series, client_meta, reference=None):
    """Same signature/result shape as score_session (IMPLEMENTATION_PLAN §5) for gameType "camera"."""
    feats, detail = measure(level, hand, series, client_meta)
    ref = _ref_for(reference if reference is not None else load_reference(), level, hand)
    out = {"features": feats, "model_version": MODEL_VERSION, "quality_ok": bool(feats["quality_ok"])}
    if ref is None:
        out.update(score=None, impairment_class=None, breakdown={}, note="no reference recorded yet")
        return out
    score, b = combine(level, feats, detail, ref)
    out.update(score=round(score, 1), impairment_class=score_to_class(score), breakdown=b)
    return out
