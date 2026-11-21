"""Game-session scoring with an optional lazily loaded tracer model."""

from __future__ import annotations

import importlib
import logging
import math
import os
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
STANDIN_VERSION = "standin-0.1"
CLASS_NORMAL_MIN = 85.0
CLASS_MILD_MIN = 65.0
CLASS_MODERATE_MIN = 40.0
EXTERNAL_COORDINATE_SCALE = 1000.0
EXTERNAL_LEVEL_IDS = {1: "line", 2: "circle", 3: "maze"}

ExternalScorer = Callable[
    [str, str, str, int, dict[str, list[float]], dict[str, Any]], dict[str, Any]
]
_external_scorer: ExternalScorer | None = None
_external_model_version = STANDIN_VERSION
_external_last_call_failed = False
_external_load_attempted = False
_external_lock = threading.Lock()


def impairment_class(score: float) -> str:
    """Map a score to its specified impairment class."""
    if score >= CLASS_NORMAL_MIN:
        return "normal"
    if score >= CLASS_MILD_MIN:
        return "mild"
    if score >= CLASS_MODERATE_MIN:
        return "moderate"
    return "severe"


def _load_external_scorer() -> ExternalScorer | None:
    """Load the tracer bridge on demand, caching success or failure for this process."""
    global _external_scorer, _external_model_version, _external_load_attempted
    with _external_lock:
        if _external_load_attempted:
            return _external_scorer
        _external_load_attempted = True
        try:
            model_dir = Path(
                os.getenv("APP_MODELS_DIR", str(Path(__file__).resolve().parents[2] / "models"))
            )
            tracer_dir = model_dir / "tracer"
            artifact = tracer_dir / "artifacts" / "tracer_gbm.joblib"
            if str(tracer_dir) not in sys.path:
                sys.path.insert(0, str(tracer_dir))
            np = importlib.import_module("numpy")
            joblib = importlib.import_module("joblib")
            common = importlib.import_module("common")
            features = importlib.import_module("features")
            levels = importlib.import_module("levels")
            bundle = joblib.load(artifact)
            model = bundle["model"]
            _external_model_version = str(bundle.get("version", "tracer-gbm"))
            loaded_levels = levels.load_levels()
            feature_names = features.FEATURE_NAMES
            coord_keys = ("x", "y", "targetX", "targetY")
            canvas_units = levels.CANVAS_UNITS

            def score_with_external(
                game_type: str,
                level_id: str,
                hand: str,
                duration_ms: int,
                series: dict[str, list[float]],
                client_meta: dict[str, Any],
            ) -> dict[str, Any]:
                level = loaded_levels[level_id]
                if len(series.get("t", [])) < 2:
                    raise ValueError("trace too short to score")
                normalized = {
                    key: (
                        [value / canvas_units for value in values] if key in coord_keys else values
                    )
                    for key, values in series.items()
                }
                processed = features.preprocess(normalized, level, duration_ms)
                extracted = features.extract_features(processed, level, True)
                inputs = np.array(
                    [
                        [extracted[name] for name in feature_names]
                        + [level.number == 1, level.number == 2, level.number == 3]
                    ],
                    dtype=np.float32,
                )
                score = float(np.clip(model.predict(inputs)[0], 0.0, 100.0))
                return {
                    "score": score,
                    "impairment_class": common.score_to_class(score),
                    "features": {name: round(float(extracted[name]), 4) for name in feature_names},
                    "model_version": _external_model_version,
                }

            _external_scorer = score_with_external
        except Exception:
            logger.exception("Could not load external tracer model from %s", artifact)
            _external_scorer = None
        return _external_scorer


def _paired_points(x_values: list[float], y_values: list[float]) -> list[tuple[float, float]]:
    return list(zip(x_values, y_values, strict=False))


def _distance_to_segment(
    point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]
) -> float:
    px, py = point
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return math.hypot(px - sx, py - sy)
    fraction = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / length_squared))
    return math.hypot(px - (sx + fraction * dx), py - (sy + fraction * dy))


def _standin_score(duration_ms: int, series: dict[str, list[float]]) -> dict[str, Any]:
    target = _paired_points(series.get("targetX", []), series.get("targetY", []))
    trace = _paired_points(series.get("x", []), series.get("y", []))
    if len(target) < 2 or not trace:
        return {
            "score": 0.0,
            "impairment_class": "severe",
            "features": {},
            "model_version": STANDIN_VERSION,
        }

    stride = max(1, len(trace) // 300)
    sampled = trace[::stride]
    segment_pairs = list(zip(target, target[1:], strict=False))
    deviations = [
        min(_distance_to_segment(point, start, end) for start, end in segment_pairs)
        for point in sampled
    ]
    mean_deviation = sum(deviations) / len(deviations)
    accuracy = max(0.0, 1.0 - mean_deviation / 0.06)
    duration_seconds = duration_ms / 1000
    speed = max(0.0, min(1.0, 1.0 - (duration_seconds - 8) / 40))
    score = round(100 * (0.8 * accuracy + 0.2 * speed), 1)
    return {
        "score": score,
        "impairment_class": impairment_class(score),
        "features": {
            "mean_dev": round(mean_deviation, 4),
            "duration_s": round(duration_seconds, 2),
        },
        "model_version": STANDIN_VERSION,
    }


def score_session(
    game_type: str,
    level: int,
    hand: str,
    duration_ms: int,
    series: dict[str, list[float]],
    client_meta: dict[str, Any],
) -> dict[str, Any]:
    """Score a completed game, falling back to the stand-in when the tracer is unavailable."""
    if game_type != "trace":
        return {
            "score": 50.0,
            "impairment_class": "moderate",
            "features": {},
            "model_version": STANDIN_VERSION,
        }
    if level not in EXTERNAL_LEVEL_IDS:
        return _standin_score(duration_ms, series)

    global _external_last_call_failed
    scorer = _load_external_scorer()
    if scorer is not None:
        scaled_series = {
            key: [value * EXTERNAL_COORDINATE_SCALE for value in values]
            if key in {"targetX", "targetY", "x", "y"}
            else values
            for key, values in series.items()
        }
        try:
            external = scorer(
                game_type,
                EXTERNAL_LEVEL_IDS[level],
                hand,
                duration_ms,
                scaled_series,
                client_meta,
            )
            raw_score = float(external["score"])
            if not math.isfinite(raw_score):
                raise ValueError("tracer returned a non-finite score")
            score = round(max(0.0, min(100.0, raw_score)), 1)
            returned_class = external.get("impairment_class")
            valid_classes = {"normal", "mild", "moderate", "severe"}
            class_name = (
                returned_class if returned_class in valid_classes else impairment_class(score)
            )
            _external_last_call_failed = False
            return {
                "score": score,
                "impairment_class": class_name,
                "features": external.get("features", {}),
                "model_version": external.get("model_version", _external_model_version),
            }
        except Exception:
            _external_last_call_failed = True
            logger.exception(
                "External tracer scoring failed for game type %s level %s", game_type, level
            )
    return _standin_score(duration_ms, series)


def active_model_version() -> str:
    """Return the active scorer version, attempting the lazy model load if needed."""
    _load_external_scorer()
    if _external_scorer is not None and not _external_last_call_failed:
        return _external_model_version
    return STANDIN_VERSION
