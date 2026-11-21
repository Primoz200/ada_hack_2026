"""Plot one or more recordings: main signal with detected peaks and beeps, compensation signals, score.

    python plot_recording.py                      # newest recording
    python plot_recording.py <file.json> [...]    # specific recordings (overlaid per exercise row)
Saves data/camera/plots/<id>.jpg (or compare.jpg for several).
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from build_reference import RECORDINGS
from exercises import EXERCISES
from scoring import load_reference, measure, score_camera

LABELS = {"hand": "hand openness 3D (fingertips–wrist / palm)", "shoulder_abduction": "shoulder abduction [deg]",
          "arm_raise": "wrist height above shoulder [shoulder widths]"}


def plot(files):
    ref = load_reference()
    recs = [json.loads(Path(f).read_text()) for f in files]
    fig, axes = plt.subplots(len(recs), 1, figsize=(12, 3.6 * len(recs)), squeeze=False)
    for ax, r in zip(axes[:, 0], recs):
        ex = EXERCISES[int(r["level"])]
        feats, tr = measure(r["level"], r["hand"], r["series"], r["clientMeta"])
        res = score_camera("camera", r["level"], r["hand"], r["durationMs"], r["series"], r["clientMeta"], ref)
        ts = tr["t"] / 1000
        ax.plot(ts, tr["signal"], color="#1f5fbf", lw=1.6, label=f"{r['hand']} (tested)")
        if "signal_other" in tr:
            ax.plot(ts, tr["signal_other"], color="#9aa", lw=1, label="other side")
        ax.plot(ts[tr["peaks"]], tr["signal"][tr["peaks"]], "o", color="#d62728", ms=5, label="detected peaks")
        if "troughs" in tr:
            ax.plot(ts[tr["troughs"]], tr["signal"][tr["troughs"]], "v", color="#9467bd", ms=5, label="detected fists")
        r_ref = (ref.get(str(r["level"]), {}).get("any") or {}).get("mean", {})
        for key, c in (("open_level", "#2ca02c"), ("fist_level", "#9467bd"), ("top_level", "#2ca02c"),
                       ("rest_level", "#999")):
            if key in r_ref:
                ax.axhline(r_ref[key], color=c, ls="--", lw=1, alpha=0.7)
        for c in tr["cues"]:
            ax.axvline(c / 1000, color="#2ca02c", lw=0.8, alpha=0.6)
        if "tilt" in tr:
            ax2 = ax.twinx()
            ax2.plot(ts, tr["tilt"], color="#ff7f0e", lw=0.8, alpha=0.7)
            ax2.set_ylabel("shoulder tilt [deg]", color="#ff7f0e")
        score = "–" if res["score"] is None else f"{res['score']:.0f} ({res['impairment_class']})"
        main = {k: v for k, v in feats.items() if v is not None and k in (
            "open_level", "fist_level", "n_reps", "timing_lag_ms", "top_level", "rest_level", "lean_deg", "hike",
            "top_visibility", "fps")}
        if res.get("breakdown"):
            main.update({f"[{k}]": v for k, v in res["breakdown"].items()})
        ax.set_title(f"{r['id']}  |  role {r.get('label', {}).get('role')}  |  score {score}\n"
                     + "  ".join(f"{k}={v:.2f}" for k, v in main.items()), fontsize=9)
        ax.set_ylabel(LABELS["hand" if ex["detector"] == "hand" else ex["key"]], fontsize=9)
        ax.set_xlabel("time [s]   (green lines = beeps, dashed = healthy reference levels)")
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    out_dir = RECORDINGS.parent / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (f"{recs[0]['id']}.jpg" if len(recs) == 1 else "compare.jpg")
    fig.savefig(out, dpi=80)
    print(f"saved {out}")


if __name__ == "__main__":
    files = sys.argv[1:] or [max(RECORDINGS.glob("*.json"), key=lambda p: p.stat().st_mtime)]
    plot(files)
