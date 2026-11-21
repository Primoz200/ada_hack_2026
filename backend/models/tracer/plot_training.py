"""Training graphs: learning curves of all CNN runs, test error per model, predicted vs. true score.

Reads data/cnn_history_*.json (train_cnn.py --tag ...) and data/gbm_test_pred.json (train_baseline.py).
Saves data/tracer_training.jpg.
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import THRESHOLDS
from dataset import DATA, load

COLORS = ["#1f5fbf", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b"]


def main():
    runs = []
    for f in sorted(DATA.glob("cnn_history_*.json")):
        h = json.loads(f.read_text())
        h["name"] = f.stem.replace("cnn_history_", "")
        runs.append(h)
    runs.sort(key=lambda h: -h["params"])
    d = load()
    te = d["split"] == 2
    y_clean = d["y_clean"][te]
    gbm = np.array(json.loads((DATA / "gbm_test_pred.json").read_text()))
    gbm_mae = np.abs(gbm - y_clean).mean()

    fig, ax = plt.subplots(2, 2, figsize=(14, 11))

    # 1) learning curves
    a = ax[0, 0]
    for c, h in zip(COLORS, runs):
        ep = [r["epoch"] for r in h["history"]]
        a.plot(ep, [r["train_mae"] for r in h["history"]], "--", color=c, lw=1.2)
        a.plot(ep, [r["val_mae"] for r in h["history"]], "-", color=c, lw=2,
               label=f"{h['name']} ({h['params'] / 1000:.0f}k params)")
    a.axhline(gbm_mae, color="#555", ls=":", lw=1.5, label=f"GBM test {gbm_mae:.2f}")
    a.set_ylim(0, 15)
    a.set_xlabel("epoch")
    a.set_ylabel("MAE [score points]")
    a.set_title("Learning curves: solid = validation (vs. truth), dashed = train (vs. noisy label)\n"
                "dashed far below solid = overfitting")
    a.legend(fontsize=9)
    a.grid(alpha=0.3)

    # 2) test MAE per model
    a = ax[0, 1]
    names = ["GBM"] + [h["name"] for h in runs]
    maes = [gbm_mae] + [h["results"]["test"]["mae_clean"] for h in runs]
    accs = [None] + [h["results"]["test"]["class_acc"] for h in runs]
    bars = a.bar(names, maes, color=["#555"] + COLORS[:len(runs)])
    for b, m, acc in zip(bars, maes, accs):
        a.text(b.get_x() + b.get_width() / 2, m + 0.1, f"{m:.2f}" + (f"\n{acc:.0%} class" if acc else ""),
               ha="center", fontsize=9)
    a.set_ylabel("test MAE vs. true score")
    a.set_title("Test error per model (lower = better)")
    a.set_ylim(0, max(maes) * 1.3)

    # 3/4) predicted vs. true for GBM and the best CNN
    best = min(runs, key=lambda h: h["results"]["val"]["mae_clean"])
    for a, pred, title in ((ax[1, 0], gbm, f"GBM  (MAE {gbm_mae:.2f})"),
                           (ax[1, 1], np.array(best["test_pred"]),
                            f"CNN {best['name']}  (MAE {best['results']['test']['mae_clean']:.2f})")):
        lv = d["level"][te]
        for k, (c, nm) in enumerate(zip(COLORS, ["line", "circle", "maze"]), 1):
            m = lv == k
            a.scatter(y_clean[m], pred[m], s=6, alpha=0.45, color=c, label=nm)
        a.plot([0, 100], [0, 100], color="#333", lw=1)
        for th in THRESHOLDS:
            a.axvline(th, color="#bbb", lw=0.8)
            a.axhline(th, color="#bbb", lw=0.8)
        a.set_xlim(0, 100)
        a.set_ylim(0, 100)
        a.set_aspect("equal")
        a.set_xlabel("true score (latent)")
        a.set_ylabel("predicted score")
        a.set_title(f"Test set: {title}\ngrey lines = class thresholds 85 / 65 / 40")
        a.legend(fontsize=8, loc="upper left")

    fig.tight_layout()
    out = DATA / "tracer_training.jpg"
    fig.savefig(out, dpi=80)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
