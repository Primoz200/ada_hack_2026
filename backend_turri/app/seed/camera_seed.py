"""Deterministic, summary-only camera-session features for synthetic story replay."""

from __future__ import annotations

import random

HAND_REFERENCE = {"open_level": 1.57, "fist_level": 0.758}
ARM_REFERENCE = {
    2: {"top_level": 104.8, "rest_level": 16.9, "lean_deg": 1.7, "hike": 0.16},
    3: {"top_level": 2.10, "rest_level": -1.24, "lean_deg": 3.2, "hike": 0.19},
}
ZERO_AT = {"hand": 0.5, "arm": 0.25}
N_CUES = {1: 7, 2: 5, 3: 5}


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def features(level: int, score: float, rng: random.Random) -> dict[str, float]:
    """Derive reproducible exercise features from the synthetic story score."""
    repetitions = 1.0 if score >= 30 else 0.8
    position = _clip((score / 100.0 - 0.15 * repetitions) / 0.85)
    common = {
        "fps": round(rng.uniform(19.5, 29.5), 1),
        "detect_frac": round(rng.uniform(0.96, 1.0), 3),
        "quality_ok": 1.0,
        "n_reps": float(round(N_CUES[level] * repetitions)),
        "part_position": round(position, 3),
        "part_reps": repetitions,
    }
    if level == 1:
        opening = _clip(position - abs(rng.gauss(0.0, 0.03)))
        closing = _clip(position * position / opening) if opening > 0 else 0.0
        span = HAND_REFERENCE["open_level"] - HAND_REFERENCE["fist_level"]
        open_level = HAND_REFERENCE["fist_level"] + span * (
            ZERO_AT["hand"] + (1.0 - ZERO_AT["hand"]) * opening
        )
        fist_level = HAND_REFERENCE["open_level"] - span * (
            ZERO_AT["hand"] + (1.0 - ZERO_AT["hand"]) * closing
        )
        return {
            **common,
            "open_level": round(open_level, 3),
            "fist_level": round(fist_level, 3),
            "open_range": round(open_level - fist_level, 3),
            "part_open": round(opening, 3),
            "part_close": round(closing, 3),
            "visibility": 1.0,
        }
    reference = ARM_REFERENCE[level]
    rest = reference["rest_level"] + rng.gauss(
        0.0, 0.03 * abs(reference["top_level"] - reference["rest_level"])
    )
    top = rest + (reference["top_level"] - reference["rest_level"]) * (
        ZERO_AT["arm"] + (1.0 - ZERO_AT["arm"]) * position
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
