"""Scoring adapter (plan section 5).

score_session() is the only entry point the platform calls. It tries Primož's model
first and falls back to the stand-in scorer, so the platform never waits on the model.
Primož's code is consumed read-only; it still uses the old format (0-1000 units,
level ids line/circle/maze), so the adapter converts: level 1/2/3 <-> line/circle/maze,
coordinates x1000.
"""
import math

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


def current_model_version() -> str:
    return STANDIN_VERSION


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
    # TODO(agent A): try Primož's model here (try/except), fall back to the stand-in.
    if game_type == "trace":
        return _standin_trace(duration_ms, series)
    return ScoreResult({}, 50.0, "moderate", STANDIN_VERSION)
