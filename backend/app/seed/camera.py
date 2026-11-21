"""Seeded camera exercise sessions: score from the story curve, a few plausible features.

There are NO fake landmarks: a seeded camera session has an empty series (nothing was
recorded) and only the summary features the clinician's feature table shows, under the
names of Primož's camera scorer (backend/models/camera/scoring.py, `part_*` = the parts of
the score as the bridge app.services.camera_model stores them). Values are derived from the
score the way his scorer works backwards (position share of the healthy movement, all
repetitions done), around his healthy reference means.
"""
import random

from app.services import scoring

SEED_VERSION = "camera-seed"  # not scored by the camera model: the score is the story's
DURATION_MS = {lv: int((scoring.camera_duration_s(lv) or 30.0) * 1000) for lv in (1, 2, 3)}
N_CUES = {1: 7, 2: 5, 3: 5}

# healthy reference means (backend/models/camera/artifacts/camera_reference.json, pooled)
_HAND = {"open_level": 1.57, "fist_level": 0.758}
_ARM = {2: {"top_level": 104.8, "rest_level": 16.9, "lean_deg": 1.7, "hike": 0.16},  # abduction [deg]
        3: {"top_level": 2.10, "rest_level": -1.24, "lean_deg": 3.2, "hike": 0.19}}  # wrist height [shoulder widths]
_ZERO_AT = {"hand": 0.5, "arm": 0.25}  # share of the healthy movement that scores 0 (scoring.ZERO_AT)


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def features(level: int, score: float, rng: random.Random) -> dict[str, float]:
    """Plausible camera features for a score (worse score -> smaller movement)."""
    reps = 1.0 if score >= 30 else 0.8
    position = _clip((score / 100.0 - 0.15 * reps) / 0.85)
    fps = round(rng.uniform(19.5, 29.5), 1)
    common = {"fps": fps, "detect_frac": round(rng.uniform(0.96, 1.0), 3), "quality_ok": 1.0,
              "n_reps": float(round(N_CUES[level] * reps)), "part_position": round(position, 3),
              "part_reps": reps}
    if level == 1:
        opening = _clip(position - abs(rng.gauss(0.0, 0.03)))
        closing = _clip(position * position / opening) if opening > 0 else 0.0
        z = _ZERO_AT["hand"]
        span = _HAND["open_level"] - _HAND["fist_level"]
        open_level = _HAND["fist_level"] + span * (z + (1 - z) * opening)
        fist_level = _HAND["open_level"] - span * (z + (1 - z) * closing)
        return {**common, "open_level": round(open_level, 3), "fist_level": round(fist_level, 3),
                "open_range": round(open_level - fist_level, 3), "part_open": round(opening, 3),
                "part_close": round(closing, 3), "visibility": 1.0}
    ref = _ARM[level]
    z = _ZERO_AT["arm"]
    rest = ref["rest_level"] + rng.gauss(0.0, 0.03 * abs(ref["top_level"] - ref["rest_level"]))
    top = rest + (ref["top_level"] - ref["rest_level"]) * (z + (1 - z) * position)
    return {**common, "top_level": round(top, 3), "rest_level": round(rest, 3),
            "lean_deg": round(ref["lean_deg"] + abs(rng.gauss(0.0, 1.0)), 2),
            "hike": round(ref["hike"] + abs(rng.gauss(0.0, 0.03)), 3),
            "top_visibility": round(rng.uniform(0.85, 0.99), 3),
            "part_lean_penalty": 0.0, "part_hike_penalty": 0.0}
