"""Bridge to Primož's tracer model (backend/models/tracer): features + gradient boosting.

His code is used read-only: `features.py` (preprocess, extract_features), `levels.py` and the
trained artifact `artifacts/tracer_gbm.joblib`. His modules import each other by bare name
(`from levels import ...`), so their folder goes on sys.path.

Called through the hook in app.services.scoring, which passes the hook format:
level id "line" / "circle" / "maze" and coordinates in 0-1000 units. Any exception here makes
scoring fall back to the stand-in scorer.
"""
import sys
from pathlib import Path

import numpy as np

TRACER_DIR = Path(__file__).resolve().parents[2] / "models" / "tracer"
ARTIFACT = TRACER_DIR / "artifacts" / "tracer_gbm.joblib"

if str(TRACER_DIR) not in sys.path:
    sys.path.insert(0, str(TRACER_DIR))

import joblib  # noqa: E402
from common import score_to_class  # noqa: E402  (Primož's module)
from features import FEATURE_NAMES, extract_features, preprocess  # noqa: E402
from levels import CANVAS_UNITS, load_levels  # noqa: E402

_bundle = joblib.load(ARTIFACT)
_model = _bundle["model"]
MODEL_VERSION = str(_bundle.get("version", "tracer-gbm"))
_levels = load_levels()

# the few features shown to the clinician first; all 20 are stored
_COORD_KEYS = ("x", "y", "targetX", "targetY")


def score_session(game_type: str, level_id: str, hand: str, duration_ms: int,
                  series: dict[str, list[float]], client_meta: dict) -> dict:
    level = _levels[level_id]
    if len(series.get("t", [])) < 2:
        raise ValueError("trace too short to score")
    # features.py expects GameResult coordinates (0-1)
    norm = {k: ([v / CANVAS_UNITS for v in vals] if k in _COORD_KEYS else vals) for k, vals in series.items()}
    feats = extract_features(preprocess(norm, level, duration_ms), level, True)
    x = np.array([[feats[n] for n in FEATURE_NAMES]
                  + [level.number == 1, level.number == 2, level.number == 3]], dtype=np.float32)
    score = float(np.clip(_model.predict(x)[0], 0.0, 100.0))
    return {
        "score": score,
        "impairment_class": score_to_class(score),
        "features": {n: round(float(feats[n]), 4) for n in FEATURE_NAMES},
        "model_version": MODEL_VERSION,
    }
