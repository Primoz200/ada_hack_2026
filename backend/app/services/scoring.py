"""Scoring adapter (plan section 5).

score_session() is the only entry point the platform calls. It tries Primož's model
first and falls back to the stand-in scorer, so the platform never waits on the model.
Primož's code is consumed read-only; it still uses the old format (0-1000 units,
level ids line/circle/maze), so the adapter converts: level 1/2/3 <-> line/circle/maze,
coordinates x1000.
"""
import importlib
import logging
import math
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from app.services.types import ScoreResult

STANDIN_VERSION = "standin-0.1"
LEVEL_IDS = {1: "line", 2: "circle", 3: "maze"}


def score_to_class(score: float) -> str:
    # thresholds from Primož's generator (models/tracer/generator.py)
    if score >= 85:
        return "normal"
    if score >= 65:
        return "mild"
    if score >= 40:
        return "moderate"
    return "severe"


log = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_DIR = _BACKEND_DIR.parent
_SCALE = 1000.0  # old model format: 0-1000 canvas units
_COORD_KEYS = ("targetX", "targetY", "x", "y")

# state of the external-model hook; loaded lazily, at most one import attempt per process
_hook: dict[str, Any] = {"tried": False, "fn": None, "version": None, "failed": False}


def _load_hook() -> Optional[Callable]:
    """Import `score_session` from `models.tracer.score` (repo-root models/ or backend/models/)."""
    if _hook["tried"]:
        return _hook["fn"]
    _hook["tried"] = True
    for base in (_REPO_DIR, _BACKEND_DIR):
        if (base / "models" / "tracer" / "score.py").exists() and str(base) not in sys.path:
            sys.path.append(str(base))
    try:
        mod = importlib.import_module("models.tracer.score")
        fn = getattr(mod, "score_session")
        _hook["fn"] = fn
        _hook["version"] = str(getattr(mod, "MODEL_VERSION", "") or "tracer-model")
    except Exception as e:  # ImportError, AttributeError, a broken module ...
        log.info("external tracer model unavailable (%s); using stand-in scorer", e)
    return _hook["fn"]


def current_model_version() -> str:
    """Version of the scorer that is active now (the external model only after it loaded
    and its last call succeeded)."""
    if _load_hook() is not None and not _hook["failed"]:
        return _hook["version"]
    return STANDIN_VERSION


def _external_trace(fn: Callable, level: int, hand: str, duration_ms: int,
                    series: dict[str, list[float]], client_meta: dict) -> ScoreResult:
    """Call Primož's model in his old format: level id line/circle/maze, coordinates x1000."""
    conv = {k: ([v * _SCALE for v in vals] if k in _COORD_KEYS else list(vals))
            for k, vals in series.items()}
    out = fn("trace", LEVEL_IDS[level], hand, duration_ms, conv, client_meta)
    get = (lambda k: out[k]) if isinstance(out, dict) else (lambda k: getattr(out, k))
    score = float(get("score"))
    if not math.isfinite(score):
        raise ValueError("non-finite score")
    score = max(0.0, min(100.0, score))
    cls = get("impairment_class")
    if cls not in ("normal", "mild", "moderate", "severe"):
        cls = score_to_class(score)
    features = {str(k): float(v) for k, v in dict(get("features")).items()}
    return ScoreResult(features, round(score, 1), cls, str(get("model_version")))


def _standin_trace(duration_ms: int, series: dict[str, list[float]]) -> ScoreResult:
    """Mean distance of the trace from the target polyline + time -> 0-100."""
    tx, ty = series.get("targetX", []), series.get("targetY", [])
    xs, ys = series.get("x", []), series.get("y", [])
    if len(tx) < 2 or not xs:
        return ScoreResult({}, 0.0, "severe", STANDIN_VERSION)

    def dist(px: float, py: float) -> float:
        best = math.inf
        for i in range(len(tx) - 1):
            ax, ay, bx, by = tx[i], ty[i], tx[i + 1], ty[i + 1]
            dx, dy = bx - ax, by - ay
            den = dx * dx + dy * dy
            u = 0.0 if den == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / den))
            best = min(best, math.hypot(px - (ax + u * dx), py - (ay + u * dy)))
        return best

    step = max(1, len(xs) // 300)  # cap the work for long traces
    dists = [dist(xs[i], ys[i]) for i in range(0, len(xs), step)]
    mean_dev = sum(dists) / len(dists)
    duration_s = duration_ms / 1000.0
    # 0.06 = channel width in normalised units; a mean deviation of one channel width -> 0 accuracy
    accuracy = max(0.0, 1.0 - mean_dev / 0.06)
    speed = max(0.0, min(1.0, 1.0 - (duration_s - 8.0) / 40.0))
    score = round(100.0 * (0.8 * accuracy + 0.2 * speed), 1)
    features = {"mean_dev": round(mean_dev, 4), "duration_s": round(duration_s, 2)}
    return ScoreResult(features, score, score_to_class(score), STANDIN_VERSION)


def score_session(game_type: str, level: int, hand: str, duration_ms: int,
                  series: dict[str, list[float]], client_meta: dict) -> ScoreResult:
    if game_type == "trace":
        fn = _load_hook()
        if fn is not None and level in LEVEL_IDS:
            try:
                res = _external_trace(fn, level, hand, duration_ms, series, client_meta)
                _hook["failed"] = False
                return res
            except Exception as e:  # any failure: the platform must never wait on the model
                _hook["failed"] = True
                log.warning("tracer model failed (%s); falling back to stand-in", e)
        return _standin_trace(duration_ms, series)
    return ScoreResult({}, 50.0, "moderate", STANDIN_VERSION)
