"""Synthetic trace generation from the shared tracer level definitions."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

LEVELS_PATH = Path(__file__).with_name("tracer_levels.json")
_LEVEL_DATA = json.loads(LEVELS_PATH.read_text(encoding="utf-8"))
LEVEL_PATHS: dict[int, list[tuple[float, float]]] = {
    int(level["level"]): [(float(x) / 1000.0, float(y) / 1000.0) for x, y in level["path"]]
    for level in _LEVEL_DATA["levels"]
}
BASE_DURATION_MS = {1: 8000, 2: 12000, 3: 22000}
TIME_LIMIT_MS = {1: 20000, 2: 30000, 3: 60000}
N_POINTS = {1: 70, 2: 90, 3: 120}


def level_features(level: int, score: float, rng: random.Random) -> dict[str, float]:
    """Generate plausible features where a worse story score has greater impairment."""
    severity = max(0.0, min(1.0, (100.0 - score) / 100.0))
    duration_ms = BASE_DURATION_MS[level] * (1.0 + 1.1 * severity) * (1.0 + rng.gauss(0, 0.04))
    duration_ms = min(duration_ms, TIME_LIMIT_MS[level] * 0.95)
    return {
        "mean_dev": round(max(0.002, 0.004 + 0.11 * severity * severity + rng.gauss(0, 0.0015)), 4),
        "duration_s": round(duration_ms / 1000.0, 2),
        "pause_rate_hz": round(max(0.0, 0.05 + 1.2 * severity + rng.gauss(0, 0.05)), 3),
        "lifts": float(int(severity * 6 * (0.4 + rng.random()))),
    }


def _arc_points(
    path: list[tuple[float, float]], count: int
) -> list[tuple[float, float, float, float, float]]:
    lengths = [math.dist(path[index], path[index + 1]) for index in range(len(path) - 1)]
    total = sum(lengths)
    output: list[tuple[float, float, float, float, float]] = []
    segment, accumulated = 0, 0.0
    for index in range(count):
        distance = total * index / (count - 1)
        while segment < len(lengths) - 1 and accumulated + lengths[segment] < distance:
            accumulated += lengths[segment]
            segment += 1
        fraction = (
            0.0
            if lengths[segment] == 0
            else min(1.0, max(0.0, (distance - accumulated) / lengths[segment]))
        )
        (x0, y0), (x1, y1) = path[segment], path[segment + 1]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        output.append(
            (x0 + dx * fraction, y0 + dy * fraction, -dy / length, dx / length, distance / total)
        )
    return output


def synthetic_trace(
    level: int,
    wobble: float,
    duration_ms: float | None = None,
    lifts: int = 0,
    seed: int | str = 0,
) -> dict[str, list[float]]:
    """Create a trace whose lateral wobble and timing reflect the story features."""
    path = LEVEL_PATHS.get(level, LEVEL_PATHS[1])
    rng = random.Random(f"trace:{seed}")
    count = N_POINTS.get(level, 80)
    duration = float(duration_ms or BASE_DURATION_MS.get(level, 9000))
    frequency1, frequency2 = rng.uniform(1.5, 3.0), rng.uniform(4.0, 7.0)
    phase1, phase2 = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
    steps = [1.0 + wobble * 12 * rng.random() for _ in range(count - 1)]
    cumulative = [0.0]
    for step in steps:
        cumulative.append(cumulative[-1] + step)
    times = [round(value / cumulative[-1] * duration, 1) for value in cumulative]
    lift_at = set(rng.sample(range(5, count - 5), min(lifts, count - 10))) if lifts > 0 else set()
    xs: list[float] = []
    ys: list[float] = []
    strokes: list[float] = []
    stroke_id = 0
    for index, (px, py, nx, ny, fraction) in enumerate(_arc_points(path, count)):
        offset = wobble * (
            0.65 * math.sin(2 * math.pi * frequency1 * fraction + phase1)
            + 0.35 * math.sin(2 * math.pi * frequency2 * fraction + phase2)
        )
        offset += rng.gauss(0, wobble * 0.08)
        xs.append(round(min(1.0, max(0.0, px + nx * offset)), 4))
        ys.append(round(min(1.0, max(0.0, py + ny * offset)), 4))
        if index in lift_at:
            stroke_id += 1
        strokes.append(float(stroke_id))
    return {
        "targetX": [round(point[0], 4) for point in path],
        "targetY": [round(point[1], 4) for point in path],
        "t": times,
        "x": xs,
        "y": ys,
        "strokeId": strokes,
    }


def generate(
    level: int, score: float, seed: str
) -> tuple[dict[str, list[float]], int, dict[str, float]]:
    """Return raw trace, duration in ms, and the required story feature fields."""
    features = level_features(level, score, random.Random(f"{seed}:features"))
    duration_ms = int(round(features["duration_s"] * 1000))
    series = synthetic_trace(
        level,
        features["mean_dev"],
        duration_ms,
        int(features["lifts"]),
        seed,
    )
    stored_features = {
        "dev_mean": round(features["mean_dev"] / 0.06, 3),
        "duration_s": features["duration_s"],
        "n_pauses": float(round(features["pause_rate_hz"] * features["duration_s"] / 4)),
        "n_lifts": features["lifts"],
    }
    return series, duration_ms, stored_features
