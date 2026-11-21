"""Scoring adapter (plan section 5).

score_session() is the only entry point the platform calls, for both games:

* trace: Primož's tracer model first, falling back to the stand-in scorer, so the platform
  never waits on the model. His tracer code still uses the old format (0-1000 units, level
  ids line/circle/maze), so the adapter converts: level 1/2/3 <-> line/circle/maze, x1000.
* camera: Primož's rule-based camera scorer (app.services.camera_model). There is no
  stand-in: a recording that cannot be scored (poor capture quality, no reference, the
  scorer raised) comes back with score None and is stored without a score, outside the
  trend.

current_model_version() reports the tracer scorer.
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
        try:  # bridge to Primož's trained model (backend/models/tracer)
            mod = importlib.import_module("app.services.tracer_model")
        except Exception as e:
            log.info("tracer model bridge unavailable (%s); trying models.tracer.score", e)
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


_camera: dict[str, Any] = {"mod": None, "tried": False}
CAMERA_UNAVAILABLE_VERSION = "camera-unavailable"


def _camera_model():
    """app.services.camera_model, imported lazily: a broken camera scorer must not take the
    platform (or tracing) down with it."""
    if not _camera["tried"]:
        _camera["tried"] = True
        try:
            _camera["mod"] = importlib.import_module("app.services.camera_model")
        except Exception as e:  # missing scipy, a broken module ...
            log.warning("camera scorer unavailable (%s)", e)
    return _camera["mod"]


def camera_duration_s(level: int) -> Optional[float]:
    """Fixed length of a camera exercise (Primož's exercises.py), None if unknown."""
    mod = _camera_model()
    ex = mod.EXERCISES.get(level) if mod is not None else None
    return float(ex["duration_s"]) if ex and ex.get("duration_s") is not None else None


def _finite(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def score_camera(level: int, hand: str, duration_ms: int, series: dict[str, list],
                 client_meta: dict) -> ScoreResult:
    """Camera exercise -> ScoreResult. score None (so: no trend) when the capture quality is
    poor, there is no reference, or scoring raised; whatever features were found are kept."""
    mod = _camera_model()
    if mod is None:
        return ScoreResult({}, None, None, CAMERA_UNAVAILABLE_VERSION)
    version = str(getattr(mod, "MODEL_VERSION", "camera"))
    try:
        out = mod.score_session("camera", level, hand, duration_ms, series, client_meta)
    except Exception as e:  # never fail a submission because of scoring
        log.warning("camera scoring failed (%s); stored without a score", e)
        return ScoreResult({}, None, None, version)
    features = {str(k): float(v) for k, v in dict(out.get("features") or {}).items() if _finite(v)}
    quality_ok = bool(out.get("quality_ok"))
    version = str(out.get("model_version") or version)
    score = out.get("score")
    if not quality_ok or not _finite(score):
        return ScoreResult(features, None, None, version, quality_ok=quality_ok)
    score = round(max(0.0, min(100.0, float(score))), 1)
    cls = out.get("impairment_class")
    if cls not in ("normal", "mild", "moderate", "severe"):
        cls = score_to_class(score)
    return ScoreResult(features, score, cls, version, quality_ok=True)


def score_session(game_type: str, level: int, hand: str, duration_ms: int,
                  series: dict[str, list], client_meta: dict) -> ScoreResult:
    if game_type == "camera":
        return score_camera(level, hand, duration_ms, series, client_meta)
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
        try:
            return _standin_trace(duration_ms, series)
        except Exception as e:  # e.g. null coordinates: stored, not scored
            log.warning("stand-in scorer failed (%s); stored without a score", e)
            return ScoreResult({}, None, None, STANDIN_VERSION)
    return ScoreResult({}, None, None, STANDIN_VERSION)
