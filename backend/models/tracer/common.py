"""Shared constants: score -> class thresholds (design assumption, see RESEARCH.md) and evaluation metrics."""
import numpy as np

CLASSES = ["normal", "mild", "moderate", "severe"]
THRESHOLDS = (85, 65, 40)  # normal >= 85, mild 65-84, moderate 40-64, severe < 40


def score_to_class(score: float) -> str:
    if score >= THRESHOLDS[0]:
        return "normal"
    if score >= THRESHOLDS[1]:
        return "mild"
    if score >= THRESHOLDS[2]:
        return "moderate"
    return "severe"


def class_index(scores) -> np.ndarray:
    s = np.asarray(scores)
    return (s < THRESHOLDS[0]).astype(int) + (s < THRESHOLDS[1]) + (s < THRESHOLDS[2])


def report(name: str, pred, y_noisy, y_clean, level) -> dict:
    """MAE against the noisy training label and the latent truth, class accuracy, per level."""
    pred, y_noisy, y_clean, level = map(np.asarray, (pred, y_noisy, y_clean, level))
    pc, tc = class_index(pred), class_index(y_clean)
    out = {
        "mae_noisy": float(np.abs(pred - y_noisy).mean()),
        "mae_clean": float(np.abs(pred - y_clean).mean()),
        "class_acc": float((pc == tc).mean()),
        "class_within1": float((np.abs(pc - tc) <= 1).mean()),
        "spearman": float(np.corrcoef(np.argsort(np.argsort(pred)), np.argsort(np.argsort(y_clean)))[0, 1]),
    }
    print(f"\n== {name} ==  MAE(clean) {out['mae_clean']:.2f}  MAE(noisy label) {out['mae_noisy']:.2f}  "
          f"class acc {out['class_acc']:.3f}  (±1 class {out['class_within1']:.3f})  spearman {out['spearman']:.3f}")
    for lv in np.unique(level):
        m = level == lv
        print(f"   level {lv}: MAE(clean) {np.abs(pred[m] - y_clean[m]).mean():.2f}  class acc {(pc[m] == tc[m]).mean():.3f}")
    cm = np.zeros((4, 4), int)
    np.add.at(cm, (tc, pc), 1)
    print("   confusion (rows = true, cols = predicted):", " ".join(c[:4] for c in CLASSES))
    for c, row in zip(CLASSES, cm):
        print(f"   {c:9s}", " ".join(f"{v:5d}" for v in row))
    return out
