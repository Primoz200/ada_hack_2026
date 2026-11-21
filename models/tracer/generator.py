"""Rule-based synthetic data generator for the tracer game.

Produces attempts in exactly the format of docs/tracer_data_spec.md, plus a `label` field.

Model of an attempt
-------------------
A latent impairment severity `sev` in [0, 1] (0 = healthy) drives several mechanisms, each with
its own random weight, so impairment shows up differently in different "patients":

- slowness            lower base speed (research: patients are slower, lower Fitts throughput)
- jerkiness           speed fluctuations (sub-movements) and pauses (more velocity peaks, lower SPARC)
- inaccuracy          low-frequency lateral deviation from the path + overshoot at corners
                      (main signal: accuracy)
- tremor              optional 4-8 Hz oscillation (pathological tremor band)
- lifts / giving up   button released mid-path, or attempt abandoned

Motion is built in the arc-length domain: a speed profile v(s) along the path gives time t(s);
pauses/lifts are inserted as time jumps at fixed s. The cursor is then the path point at s(t)
plus lateral deviation and tremor, sampled at ~60 Hz with frame jitter and dropped frames.

Label: score = round(100 * (1 - sev)); class from the score thresholds below
(thresholds are a design assumption, see RESEARCH.md).
"""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import lfilter

from levels import Level, load_levels

CLASSES = ["normal", "mild", "moderate", "severe"]
# severity ranges per class -> score = 100 * (1 - sev): normal >= 85, mild 65-84, moderate 40-64, severe < 40
SEV_RANGES = {"normal": (0.0, 0.15), "mild": (0.15, 0.35), "moderate": (0.35, 0.60), "severe": (0.60, 1.0)}

FRAME_MS = 1000.0 / 60.0
GRID_HZ = 200.0  # internal time grid for noise processes


def score_to_class(score: float) -> str:
    if score >= 85:
        return "normal"
    if score >= 65:
        return "mild"
    if score >= 40:
        return "moderate"
    return "severe"


def smooth_noise(rng, n, sigma_samples):
    """Zero-mean, unit-std low-pass Gaussian noise of length n."""
    sigma_samples = max(sigma_samples, 0.5)
    pad = int(4 * sigma_samples) + 1
    x = gaussian_filter1d(rng.standard_normal(n + 2 * pad), sigma_samples)[pad:-pad]
    return (x - x.mean()) / (x.std() + 1e-9)


def ou_noise(rng, n, corr_samples):
    """Zero-mean, unit-std Ornstein-Uhlenbeck noise (mean-reverting random walk): jagged like a stock chart."""
    a = np.exp(-1.0 / max(corr_samples, 1.0))
    e = rng.standard_normal(n) * np.sqrt(1.0 - a * a)
    e[0] = rng.standard_normal()
    x = lfilter([1.0], [1.0, -a], e)  # x[i] = a * x[i-1] + e[i]
    x = gaussian_filter1d(x, 0.02 * GRID_HZ)  # hand inertia: no instant jumps (~20 ms)
    return (x - x.mean()) / (x.std() + 1e-9)


def sample_params(sev: float, rng: np.random.Generator) -> dict:
    """Map latent severity to concrete generator parameters (with per-person variation)."""
    def comp():  # each mechanism scales with sev, with individual variation
        return float(np.clip(sev * rng.uniform(0.6, 1.4), 0.0, 1.0))

    a_slow, a_jerk, a_acc = comp(), comp(), comp()
    has_tremor = rng.random() < 0.10 + 0.5 * sev
    a_trem = comp() if has_tremor else 0.0

    skill = rng.normal(0.0, 1.0)  # healthy people differ too
    return {
        "severity": sev,
        # careful mouse tracing ~250 units/s for a healthy person
        "base_speed": float(250.0 * np.exp(0.2 * skill) * (1.0 - 0.65 * a_slow)),
        "corner_slowdown": float(50.0 * (1.0 + sev)),
        "speed_fluct": float(0.08 + 0.55 * a_jerk),
        "speed_fluct_corr_s": float(rng.uniform(0.15, 0.4)),
        "pause_rate_hz": float(0.01 + 0.25 * a_jerk ** 1.5),
        "pause_max_s": float(0.3 + 1.2 * sev),
        "lateral_sd_frac": float(0.05 * np.exp(0.15 * rng.normal()) + 0.30 * a_acc),  # of channel width
        "lateral_corr_s": float(rng.uniform(0.3, 0.8)),
        # jagged "stock chart" component: fast mean-reverting noise perpendicular to the path
        "jitter_sd_frac": float(0.012 + 0.18 * a_acc ** 1.2),  # of channel width
        "jitter_corr_s": float(rng.uniform(0.06, 0.15)),
        "overshoot_frac": float(0.05 + 0.6 * a_acc),  # of channel width, at corners
        "tremor_hz": float(rng.uniform(4.0, 8.0)) if has_tremor else 0.0,
        "tremor_amp": float(1.0 + 10.0 * a_trem) if has_tremor else 0.0,  # units (mouse damps tremor)
        "lift_rate": float(3.0 * sev ** 2),  # expected lifts per attempt
        "give_up_prob": float(0.15 * max(0.0, sev - 0.5)),
    }


def simulate_attempt(level: Level, p: dict, rng: np.random.Generator) -> dict:
    cw = level.channel_width
    s = level.s
    ds = np.diff(s)

    # --- speed profile along the path ---------------------------------------------------
    corr_units = p["speed_fluct_corr_s"] * p["base_speed"]
    fluct = smooth_noise(rng, len(s), corr_units / (s[1] - s[0]))
    v = p["base_speed"] * np.clip(1.0 + p["speed_fluct"] * fluct, 0.08, None)
    v /= 1.0 + p["corner_slowdown"] * np.abs(level.curvature)
    ramp = 40.0  # minimum-jerk-like acceleration at start / deceleration at end
    v *= np.clip(np.sqrt(np.minimum(s, level.length - s) / ramp), 0.15, 1.0)

    t_of_s = np.concatenate([[0.0], np.cumsum(ds / (0.5 * (v[1:] + v[:-1])))])

    # --- pauses (still holding) and lifts (button released) -------------------------------
    base_T = t_of_s[-1]
    n_pause = rng.poisson(p["pause_rate_hz"] * base_T)
    n_lift = rng.poisson(p["lift_rate"])
    events = [(rng.uniform(0.05, 0.95) * level.length, rng.uniform(0.12, p["pause_max_s"]), 1) for _ in range(n_pause)]
    events += [(rng.uniform(0.05, 0.95) * level.length, rng.uniform(0.2, 1.0), 0) for _ in range(n_lift)]
    events.sort()

    knots_s, knots_t = list(s), list(t_of_s)
    down_intervals = []  # (t_start, t_end) where button is up
    shift = 0.0
    for es, dur, held in events:
        te = float(np.interp(es, s, t_of_s)) + shift
        if not held:
            down_intervals.append((te, te + dur))
        shift += dur
        knots_t = [kt + dur if ks > es else kt for ks, kt in zip(knots_s, knots_t)]
        knots_s.append(es)
        knots_t.append(te)
        knots_s.append(es)
        knots_t.append(te + dur)
    order = np.lexsort((knots_t, knots_s))
    knots_s = np.asarray(knots_s)[order]
    knots_t = np.asarray(knots_t)[order]
    total_T = knots_t[-1]

    # --- end conditions -----------------------------------------------------------------
    completed = True
    end_T = total_T
    if rng.random() < p["give_up_prob"]:
        end_T = rng.uniform(0.3, 0.9) * total_T
        completed = False
    if end_T > level.time_limit_s:
        end_T = level.time_limit_s
        completed = False

    # --- sample times: ~60 Hz with jitter and occasional dropped frames -------------------
    n_max = int(end_T * 1000 / FRAME_MS * 1.2) + 10
    dt = FRAME_MS * (1.0 + 0.04 * rng.standard_normal(n_max))
    dt[rng.random(n_max) < 0.01] *= 2.0
    t_ms = np.concatenate([[0.0], np.cumsum(np.clip(dt, 5.0, None))])
    t_ms = t_ms[t_ms <= end_T * 1000.0]
    t_s = t_ms / 1000.0

    # arc position at each sample (knots_t is non-decreasing; pauses are flat segments)
    s_t = np.interp(t_s, knots_t, knots_s)
    base_xy, normal = level.point_at(s_t)

    # --- lateral deviation: low-pass noise in time + overshoot after corners ------------
    n_grid = int(end_T * GRID_HZ) + 2
    grid_t = np.arange(n_grid) / GRID_HZ
    lat = smooth_noise(rng, n_grid, p["lateral_corr_s"] * GRID_HZ) * p["lateral_sd_frac"] * cw
    lat += ou_noise(rng, n_grid, p["jitter_corr_s"] * GRID_HZ) * p["jitter_sd_frac"] * cw
    lateral = np.interp(t_s, grid_t, lat)
    # overshoot: outward of the turn, lagging slightly behind the corner
    lag = 15.0
    curv_lag = level.curvature_at(s_t - lag)
    max_curv = np.abs(level.curvature).max()
    if max_curv > 0.01:  # only real corners (maze), not the gentle circle
        lateral += -np.sign(curv_lag) * (np.abs(curv_lag) / max_curv) * p["overshoot_frac"] * cw

    # --- tremor: oscillation perpendicular to the path (up/down, no loops) ------------------
    if p["tremor_amp"] > 0:
        f = p["tremor_hz"] * (1.0 + 0.05 * smooth_noise(rng, n_grid, GRID_HZ))
        phase = 2 * np.pi * np.cumsum(f) / GRID_HZ
        amp = p["tremor_amp"] * np.clip(1.0 + 0.3 * smooth_noise(rng, n_grid, 0.5 * GRID_HZ), 0.2, None)
        lateral += np.interp(t_s, grid_t, amp * np.sin(phase))

    xy = base_xy + normal * lateral[:, None]

    # small sensor/quantization noise
    xy += rng.normal(0.0, 0.3, xy.shape)

    down = np.ones(len(t_s), dtype=int)
    for a, b in down_intervals:
        down[(t_s >= a) & (t_s < b)] = 0

    return {
        "completed": completed,
        "samples": {
            "t": np.round(t_ms).astype(int).tolist(),
            "x": np.round(xy[:, 0], 1).tolist(),
            "y": np.round(xy[:, 1], 1).tolist(),
            "down": down.tolist(),
        },
    }


def generate(levels: dict, n_per_level: int, seed: int):
    rng = np.random.default_rng(seed)
    t0 = datetime(2026, 11, 1, tzinfo=timezone.utc)
    for level_id, level in levels.items():
        for i in range(n_per_level):
            cls = CLASSES[i % len(CLASSES)]  # balanced classes
            sev = float(rng.uniform(*SEV_RANGES[cls]))
            params = sample_params(sev, rng)
            attempt = simulate_attempt(level, params, rng)
            score = int(round(100 * (1 - sev)))
            yield {
                "patient_id": f"synth_{level_id}_{i:05d}",
                "level_id": level_id,
                "started_at": (t0 + timedelta(seconds=int(rng.integers(0, 30 * 86400)))).isoformat().replace("+00:00", "Z"),
                **attempt,
                "device": {"pointer_type": "mouse"},
                "label": {
                    "severity": score_to_class(score),
                    "score": score,
                    "generator": {k: round(v, 4) if isinstance(v, float) else v for k, v in params.items()},
                },
            }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--n", type=int, default=1000, help="attempts per level")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--levels", nargs="*", default=None, help="subset of level ids")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "tracer_synth.jsonl")
    args = ap.parse_args()

    levels = load_levels()
    if args.levels:
        levels = {k: levels[k] for k in args.levels}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for n, rec in enumerate(generate(levels, args.n, args.seed), 1):
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")
    print(f"wrote {n} attempts to {args.out}")


if __name__ == "__main__":
    main()
