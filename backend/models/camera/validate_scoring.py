"""Sanity check of the rule-based score using only healthy recordings.

We have no impaired recordings, so "patients" are made by geometrically degrading our real reference
recordings (landmarks are edited, everything else stays real: noise, tempo, camera, detection gaps):
  hand   open a:  each frame's hand pose blended towards the recording's fist (a=1 original, a>1 opens wider)
         close a: blended towards the recording's open hand (a<1 = fist does not close fully)
  arms   range a: upper arm + forearm rotated around the shoulder to a * original angle (a>1 = higher)
         lean:    whole upper body tilted sideways while the arm is up
  all    faster tempo (time x0.5), 30 % dropped frames, 2x landmark jitter
Also leave-one-out: each reference scored against a reference built from the other recordings.

    python validate_scoring.py      -> table + data/camera/plots/score_validation.jpg
"""
import copy
import json
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import build_reference
from exercises import EXERCISES, HAND_WRIST, POSE
from scoring import THRESHOLDS, load_reference, measure, score_camera
from signals import hand_openness_3d

RNG = np.random.default_rng(0)
FACTORS = [0.0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0, 1.15, 1.3]


def _get(s, i, pre="lm"):
    return np.stack([np.array(s[f"{pre}{i}_{a}"], dtype=float) for a in "xyz"], 1)


def _set(s, i, arr, pre="lm"):
    for k, a in enumerate("xyz"):
        s[f"{pre}{i}_{a}"] = [None if not np.isfinite(v) else float(v) for v in arr[:, k]]


def hand_blend(rec, a, towards):
    """Blend every frame's hand pose (relative to the wrist) towards the fist ("fist") or open ("open") frame."""
    r = copy.deepcopy(rec)
    s = r["series"]
    o = hand_openness_3d(s)
    j = int(np.nanargmin(o) if towards == "fist" else np.nanargmax(o))
    for pre in ("lm", "w"):
        wrist = _get(s, HAND_WRIST, pre)
        for i in range(21):
            if i == HAND_WRIST:
                continue
            rel = _get(s, i, pre) - wrist
            ref_rel = rel[j]
            _set(s, i, wrist + ref_rel + a * (rel - ref_rel), pre)
    return r


def arm_range(rec, a):
    """Rotate elbow + wrist of both arms around the shoulder: angle to the trunk axis scaled by a (max 180°)."""
    r = copy.deepcopy(rec)
    s = r["series"]
    w, h = r["clientMeta"]["videoW"], r["clientMeta"]["videoH"]
    px = np.array([w, h, 1.0])
    for side, other in (("left", "right"), ("right", "left")):
        sh = _get(s, POSE[f"{side}_shoulder"]) * px
        sh_o = _get(s, POSE[f"{other}_shoulder"]) * px
        line = sh_o - sh
        down = np.stack([-line[:, 1], line[:, 0]], 1)
        down *= np.where(down[:, 1:2] >= 0, 1.0, -1.0)
        base = np.arctan2(down[:, 1], down[:, 0])
        el = _get(s, POSE[f"{side}_elbow"]) * px
        ang = np.arctan2(el[:, 1] - sh[:, 1], el[:, 0] - sh[:, 0]) - base
        ang = (ang + np.pi) % (2 * np.pi) - np.pi
        new = np.sign(ang) * np.minimum(np.abs(ang) * a, np.pi)
        rot = new - ang
        c, sn = np.cos(rot), np.sin(rot)
        for j in ("elbow", "wrist"):
            p = _get(s, POSE[f"{side}_{j}"]) * px
            d = p - sh
            q = p.copy()
            q[:, 0] = sh[:, 0] + c * d[:, 0] - sn * d[:, 1]
            q[:, 1] = sh[:, 1] + sn * d[:, 0] + c * d[:, 1]
            _set(s, POSE[f"{side}_{j}"], q / px)
    return r


def arm_lean(rec, deg):
    """Tilt the whole upper body around the hip midpoint by deg * (how far the arm is raised)."""
    r = copy.deepcopy(rec)
    s = r["series"]
    w, h = r["clientMeta"]["videoW"], r["clientMeta"]["videoH"]
    px = np.array([w, h, 1.0])
    feats, det = measure(r["level"], r["hand"], s, r["clientMeta"])
    t = np.array(s["t"], float)
    u = np.interp(t, det["t"], np.nan_to_num((det["signal"] - det["rest"]) / (feats["top_level"] - det["rest"])))
    th = np.radians(deg) * np.clip(u, 0, 1)
    hip = 0.5 * (_get(s, POSE["left_hip"]) + _get(s, POSE["right_hip"])) * px
    c, sn = np.cos(th), np.sin(th)
    for i in range(33):
        p = _get(s, i) * px
        d = p - hip
        q = p.copy()
        q[:, 0] = hip[:, 0] + c * d[:, 0] - sn * d[:, 1]
        q[:, 1] = hip[:, 1] + sn * d[:, 0] + c * d[:, 1]
        _set(s, i, q / px)
    return r


def faster(rec, k=0.5):
    r = copy.deepcopy(rec)
    r["series"]["t"] = [v * k for v in r["series"]["t"]]
    r["series"]["cueT"] = [v * k for v in r["series"]["cueT"]]
    return r


def drop_frames(rec, frac=0.3):
    r = copy.deepcopy(rec)
    s = r["series"]
    m = RNG.random(len(s["t"])) < frac
    for k, v in s.items():
        if k.startswith(("lm", "w")) and len(v) == len(m):
            s[k] = [None if d else x for x, d in zip(v, m)]
    return r


def jitter(rec, sd=0.004):
    r = copy.deepcopy(rec)
    s = r["series"]
    for k, v in s.items():
        if k.startswith("lm") and k[-2:] in ("_x", "_y"):
            s[k] = [None if x is None else x + RNG.normal(0, sd) for x in v]
    return r


def score(rec, ref):
    res = score_camera("camera", rec["level"], rec["hand"], rec["durationMs"], rec["series"], rec["clientMeta"], ref)
    return res["score"], res["quality_ok"], res["breakdown"]


def main():
    recs = [json.loads(f.read_text()) for f in sorted(build_reference.RECORDINGS.glob("*.json"))]
    recs = [r for r in recs if r.get("label", {}).get("role") == "reference"]
    ref = load_reference()

    print("== leave-one-out (reference built from the other recordings of the same exercise) ==")
    by_level = defaultdict(list)
    for r in recs:
        by_level[r["level"]].append(r)
    for lv, rs in sorted(by_level.items()):
        for i, r in enumerate(rs):
            others = [x for j, x in enumerate(rs) if j != i]
            if not others:
                print(f"  level {lv}: only 1 recording, LOO not possible")
                continue
            feats = [measure(x["level"], x["hand"], x["series"], x["clientMeta"])[0] for x in others]
            names = feats[0].keys()
            arr = {k: np.array([np.nan if f[k] is None else f[k] for f in feats]) for k in names}
            loo = {str(lv): {"any": {"n": len(others),
                                     "mean": {k: float(np.nanmean(v)) for k, v in arr.items()},
                                     "sd": {k: float(np.nanstd(v)) for k, v in arr.items()}}}}
            print(f"  level {lv} {r['id'][:19]} {r['hand']:5s}: {score(r, loo)[0]:5.1f}")

    print("\n== robustness (score: original -> modified) ==")
    for r in recs:
        base = score(r, ref)[0]
        rows = [("faster x2", faster(r)), ("30% frames dropped", drop_frames(r)), ("2x landmark jitter", jitter(r))]
        if EXERCISES[r["level"]]["detector"] == "pose":
            rows += [(f"lean {d}°", arm_lean(r, d)) for d in (10, 20, 30)]
        out = []
        for name, m in rows:
            sc, q, _ = score(m, ref)
            out.append(f"{name}: {sc:.0f}{'' if q else ' (bad quality)'}")
        print(f"  {r['id'][20:54]:34s} {base:5.1f} | " + " | ".join(out))

    # degradation curves
    panels = [(1, "open", "hand opens only partly (a<1) / wider (a>1)"),
              (1, "close", "fist closes only partly (a<1)"),
              (2, "range", "arms out to the side: angle x a"),
              (3, "range", "arms up: angle x a\n(a < 0.5 = test artifact: arm foreshortened at rest)")]
    fig, axes = plt.subplots(1, len(panels), figsize=(5 * len(panels), 4.2))
    print("\n== degradation curves (mean score over references) ==")
    for ax, (lv, kind, title) in zip(axes, panels):
        rs = by_level.get(lv, [])
        curves = []
        for r in rs:
            ys = []
            for a in FACTORS:
                if kind == "open":
                    m = hand_blend(r, a, "fist")
                elif kind == "close":
                    m = hand_blend(r, min(a, 1.0), "open") if a <= 1 else hand_blend(r, a, "open")
                else:
                    m = arm_range(r, a)
                ys.append(score(m, ref)[0])
            curves.append(ys)
            ax.plot(FACTORS, ys, "o-", lw=1, ms=3, alpha=0.6, label=f"{r['hand']} {r['id'][9:15]}")
        if curves:
            mean = np.mean(curves, 0)
            ax.plot(FACTORS, mean, "k-", lw=2.5, label="mean")
            print(f"  level {lv} {kind:6s}: " + "  ".join(f"a={a:.2f}:{m:3.0f}" for a, m in zip(FACTORS, mean)))
        for th in THRESHOLDS:
            ax.axhline(th, color="#bbb", lw=0.8)
        ax.axvline(1.0, color="#2ca02c", lw=0.8)
        ax.set_ylim(-3, 103)
        ax.set_xlabel("a  (1 = healthy recording as recorded)")
        ax.set_ylabel("score")
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=7, loc="lower right")
        ax.grid(alpha=0.3)
    fig.suptitle("Rule-based camera score on geometrically degraded healthy recordings "
                 "(grey = class thresholds 85 / 65 / 40)", fontsize=11)
    fig.tight_layout()
    out = build_reference.RECORDINGS.parent / "plots" / "score_validation.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=80)
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
