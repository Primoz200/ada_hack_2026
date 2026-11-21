"""Plot example synthetic attempts: one row per level, one column per class, plus speed profiles."""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import CLASSES
from levels import levels_by_number


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "tracer_synth.jsonl")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "tracer_samples.jpg")
    args = ap.parse_args()

    levels = {lv.id: lv for lv in levels_by_number().values()}
    num_to_id = {lv.number: lv.id for lv in levels.values()}
    picked = {}
    with args.data.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            key = (num_to_id[r["level"]], r["label"]["impairment_class"])
            picked.setdefault(key, r)

    rows = list(levels)
    fig, axes = plt.subplots(2 * len(rows), len(CLASSES), figsize=(4 * len(CLASSES), 7 * len(rows)),
                             gridspec_kw={"height_ratios": [3, 1] * len(rows)})
    for i, lid in enumerate(rows):
        lv = levels[lid]
        for j, cls in enumerate(CLASSES):
            ax, axv = axes[2 * i, j], axes[2 * i + 1, j]
            r = picked.get((lid, cls))
            ax.plot(lv.xy[:, 0], lv.xy[:, 1], color="#ddd", lw=lv.channel_width * 0.28, solid_capstyle="round")
            ax.plot(lv.xy[:, 0], lv.xy[:, 1], color="#999", lw=0.8, ls="--")
            if r:
                smp = r["series"]
                x, y, t, sid = (np.array(smp[k], dtype=float) for k in ("x", "y", "t", "strokeId"))
                x, y = x * 1000, y * 1000
                for k in np.unique(sid):  # one line per stroke, so lifts show as breaks
                    m = sid == k
                    ax.plot(x[m], y[m], lw=1.0, color="#1f5fbf")
                starts = np.nonzero(np.diff(sid) > 0)[0] + 1
                ax.scatter(x[starts], y[starts], s=10, color="#d62728", zorder=3, label="new stroke")
                dist, _ = lv.distance_to_path(np.column_stack([x, y]))
                ax.set_title(f"{lid} / {cls}  score={r['label']['score']}\n"
                             f"T={t[-1] / 1000:.1f}s  rmsdev={np.sqrt((dist ** 2).mean()):.1f}  "
                             f"done={r['completed']}", fontsize=9)
                sp = np.hypot(np.diff(x), np.diff(y)) / np.maximum(np.diff(t), 1) * 1000
                axv.plot(t[1:] / 1000, sp, lw=0.7, color="#444")
                axv.set_xlabel("t [s]", fontsize=8)
                axv.set_ylabel("speed [u/s]", fontsize=8)
                axv.set_ylim(0, 800)
            ax.set_xlim(0, 1000)
            ax.set_ylim(1000, 0)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(args.out, dpi=80)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
