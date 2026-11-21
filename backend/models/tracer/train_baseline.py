"""Baseline: gradient boosting on the hand-made features (+ level one-hot) -> score 0-100."""
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance

from common import report
from dataset import DATA, load

ART = Path(__file__).resolve().parent / "artifacts"


def design(X, level):
    return np.column_stack([X, level == 1, level == 2, level == 3]).astype(np.float32)


def main():
    d = load()
    A = design(d["X"], d["level"])
    tr, va, te = (d["split"] == k for k in (0, 1, 2))
    model = HistGradientBoostingRegressor(loss="absolute_error", max_iter=600, learning_rate=0.05,
                                          max_leaf_nodes=31, min_samples_leaf=20, l2_regularization=1.0,
                                          early_stopping=True, validation_fraction=0.15, random_state=0)
    model.fit(A[tr], d["y"][tr])
    print(f"iterations: {model.n_iter_}")
    for name, m in (("GBM val", va), ("GBM test", te)):
        report(name, np.clip(model.predict(A[m]), 0, 100), d["y"][m], d["y_clean"][m], d["level"][m])

    names = list(d["feature_names"]) + ["level_1", "level_2", "level_3"]
    imp = permutation_importance(model, A[va], d["y"][va], n_repeats=5, random_state=0, scoring="neg_mean_absolute_error")
    print("\npermutation importance (MAE increase):")
    for i in np.argsort(-imp.importances_mean)[:12]:
        print(f"   {names[i]:14s} {imp.importances_mean[i]:.2f}")

    (DATA / "gbm_test_pred.json").write_text(json.dumps(np.clip(model.predict(A[te]), 0, 100).round(2).tolist()))
    ART.mkdir(exist_ok=True)
    joblib.dump({"model": model, "feature_names": names, "version": "tracer-gbm-0.1"}, ART / "tracer_gbm.joblib")
    print(f"saved {ART / 'tracer_gbm.joblib'}")


if __name__ == "__main__":
    main()
