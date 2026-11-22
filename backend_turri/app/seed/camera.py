"""Plausible summary features for deterministic, preset-score camera demo sessions."""

from __future__ import annotations

import random

from app.services.scoring import camera_duration_s

SEED_VERSION = "camera-seed"
DURATION_MS = {level: int((camera_duration_s(level) or 30.0) * 1000) for level in (1, 2, 3)}
N_CUES = {1: 7, 2: 5, 3: 5}

# Healthy reference means pooled from the camera model's reference data.
_HAND = {"open_level": 1.57, "fist_level": 0.758}
_ARM = {
    2: {"top_level": 104.8, "rest_level": 16.9, "lean_deg": 1.7, "hike": 0.16},
    3: {"top_level": 2.10, "rest_level": -1.24, "lean_deg": 3.2, "hike": 0.19},
}
_ZERO_AT = {"hand": 0.5, "arm": 0.25}


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def features(level: int, score: float, rng: random.Random) -> dict[str, float]:
    """Generate plausible camera features for a story's preset score."""
    repetitions = 1.0 if score >= 30 else 0.8
    position = _clip((score / 100.0 - 0.15 * repetitions) / 0.85)
    fps = round(rng.uniform(19.5, 29.5), 1)
    common = {
        "fps": fps,
        "detect_frac": round(rng.uniform(0.96, 1.0), 3),
        "quality_ok": 1.0,
        "n_reps": float(round(N_CUES[level] * repetitions)),
        "part_position": round(position, 3),
        "part_reps": repetitions,
    }
    if level == 1:
        opening = _clip(position - abs(rng.gauss(0.0, 0.03)))
        closing = _clip(position * position / opening) if opening > 0 else 0.0
        zero_at = _ZERO_AT["hand"]
        span = _HAND["open_level"] - _HAND["fist_level"]
        open_level = _HAND["fist_level"] + span * (zero_at + (1 - zero_at) * opening)
        fist_level = _HAND["open_level"] - span * (zero_at + (1 - zero_at) * closing)
        return {
            **common,
            "open_level": round(open_level, 3),
            "fist_level": round(fist_level, 3),
            "open_range": round(open_level - fist_level, 3),
            "part_open": round(opening, 3),
            "part_close": round(closing, 3),
            "visibility": 1.0,
        }
    reference = _ARM[level]
    zero_at = _ZERO_AT["arm"]
    rest = reference["rest_level"] + rng.gauss(
        0.0, 0.03 * abs(reference["top_level"] - reference["rest_level"])
    )
    top = rest + (reference["top_level"] - reference["rest_level"]) * (
        zero_at + (1 - zero_at) * position
    )
    return {
        **common,
        "top_level": round(top, 3),
        "rest_level": round(rest, 3),
        "lean_deg": round(reference["lean_deg"] + abs(rng.gauss(0.0, 1.0)), 2),
        "hike": round(reference["hike"] + abs(rng.gauss(0.0, 0.03)), 3),
        "top_visibility": round(rng.uniform(0.85, 0.99), 3),
        "part_lean_penalty": 0.0,
        "part_hike_penalty": 0.0,
    }
