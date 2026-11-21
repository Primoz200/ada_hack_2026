"""Synthetic raw traces and score features for the seed (plan section 5 format).

Nothing here scores a trace: the seed passes the score from its story curve and this
module produces a trace and features that look consistent with it (worse score -> more
lateral wobble, longer duration, more pauses and lifts).
"""
import json
import math
import random
from pathlib import Path

_LEVELS_FILE = Path(__file__).resolve().parents[3] / "shared" / "tracer_levels.json"
_RAW = json.loads(_LEVELS_FILE.read_text())
_IDS = {"line": 1, "circle": 2, "maze": 3}
LEVEL_PATHS: dict[int, list[tuple[float, float]]] = {
    _IDS[lv["level_id"]]: [(p[0] / 1000.0, p[1] / 1000.0) for p in lv["path"]] for lv in _RAW["levels"]
}
N_POINTS = {1: 70, 2: 90, 3: 120}
BASE_DURATION_MS = {1: 8000, 2: 12000, 3: 22000}  # a good attempt at each level
TIME_LIMIT_MS = {1: 20000, 2: 30000, 3: 60000}


def level_features(level: int, score: float, rng: random.Random) -> dict[str, float]:
    """Plausible features for a score: worse score -> larger deviation, longer, more pauses."""
    sev = max(0.0, min(1.0, (100.0 - score) / 100.0))
    duration_ms = BASE_DURATION_MS[level] * (1.0 + 1.1 * sev) * (1.0 + rng.gauss(0, 0.04))
    duration_ms = min(duration_ms, TIME_LIMIT_MS[level] * 0.95)
    return {
        "mean_dev": round(max(0.002, 0.006 + 0.06 * sev + rng.gauss(0, 0.0015)), 4),
        "duration_s": round(duration_ms / 1000.0, 2),
        "pause_rate_hz": round(max(0.0, 0.05 + 1.2 * sev + rng.gauss(0, 0.05)), 3),
        "lifts": float(int(sev * 6 * (0.4 + rng.random()))),
    }


def _arc_points(path: list[tuple[float, float]], n: int):
    """n points evenly spread by arc length along the polyline, with the segment normal."""
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]
    total = sum(seg)
    out = []
    j, acc = 0, 0.0
    for i in range(n):
        s = total * i / (n - 1)
        while j < len(seg) - 1 and acc + seg[j] < s:
            acc += seg[j]
            j += 1
        f = 0.0 if seg[j] == 0 else min(1.0, max(0.0, (s - acc) / seg[j]))
        (x0, y0), (x1, y1) = path[j], path[j + 1]
        dx, dy = (x1 - x0), (y1 - y0)
        ln = math.hypot(dx, dy) or 1.0
        out.append((x0 + dx * f, y0 + dy * f, -dy / ln, dx / ln, s / total))
    return out


def synthetic_trace(level: int, wobble: float, duration_ms: float | None = None,
                    lifts: int = 0, seed: int | str = 0) -> dict[str, list[float]]:
    """A plan-section-5 trace (0-1 square canvas). target* is the real level path; x/y follow
    it with lateral wobble (amplitude `wobble`, in canvas units), over `duration_ms`."""
    path = LEVEL_PATHS.get(level, LEVEL_PATHS[1])
    rng = random.Random(f"trace:{seed}")
    n = N_POINTS.get(level, 80)
    duration_ms = float(duration_ms or BASE_DURATION_MS.get(level, 9000))
    f1, f2 = rng.uniform(1.5, 3.0), rng.uniform(4.0, 7.0)
    p1, p2 = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
    # pace: slow and uneven when wobbly
    steps = [1.0 + wobble * 12 * rng.random() for _ in range(n - 1)]
    cum = [0.0]
    for st in steps:
        cum.append(cum[-1] + st)
    ts = [round(c / cum[-1] * duration_ms, 1) for c in cum]
    lift_at = set(rng.sample(range(5, n - 5), min(lifts, n - 10))) if lifts > 0 else set()
    xs, ys, strokes, sid = [], [], [], 0
    for i, (px, py, nx, ny, u) in enumerate(_arc_points(path, n)):
        off = wobble * (0.65 * math.sin(2 * math.pi * f1 * u + p1) + 0.35 * math.sin(2 * math.pi * f2 * u + p2))
        off += rng.gauss(0, wobble * 0.25)
        xs.append(round(min(1.0, max(0.0, px + nx * off)), 4))
        ys.append(round(min(1.0, max(0.0, py + ny * off)), 4))
        if i in lift_at:
            sid += 1
        strokes.append(float(sid))
    return {
        "targetX": [round(p[0], 4) for p in path],
        "targetY": [round(p[1], 4) for p in path],
        "t": ts, "x": xs, "y": ys, "strokeId": strokes,
    }
