"""Bridge to Primož's camera exercises (backend/models/camera): rule-based scoring, no ML.

His code is used read-only: `exercises.py` (cue timelines), `scoring.py` (`score_camera`, a
recording scored 0-100 as a share of the healthy reference in `artifacts/camera_reference.json`).
His modules import each other by bare name, so their folder goes on sys.path.

score_session() returns the same dict shape as the tracer bridge plus `quality_ok`; `score` is
None when there is no reference for that exercise. Any exception here must be handled by the
caller (app.services.scoring): the platform never fails a submission because of scoring.
"""
import sys
from pathlib import Path

CAMERA_DIR = Path(__file__).resolve().parents[2] / "models" / "camera"

if str(CAMERA_DIR) not in sys.path:
    sys.path.append(str(CAMERA_DIR))

import exercises as _exercises  # noqa: E402  (Primož's module)
import scoring as _scoring  # noqa: E402  (Primož's module; not app.services.scoring)

MODEL_VERSION: str = _scoring.MODEL_VERSION
EXERCISES: dict[int, dict] = _exercises.EXERCISES
_reference = _scoring.load_reference()


def exercise(level: int) -> dict:
    return EXERCISES[level]


def score_session(game_type: str, level: int, hand: str, duration_ms: int,
                  series: dict[str, list], client_meta: dict) -> dict:
    """{"score": float | None, "impairment_class", "features", "model_version", "quality_ok", "breakdown"}"""
    out = _scoring.score_camera("camera", level, hand, duration_ms, series, client_meta, reference=_reference)
    features = {k: float(v) for k, v in out["features"].items() if isinstance(v, (int, float)) and v == v}
    for k, v in (out.get("breakdown") or {}).items():  # position / repetition / penalty parts of the score
        if isinstance(v, (int, float)) and v == v:
            features[f"part_{k}"] = float(v)
    return {"score": out.get("score"), "impairment_class": out.get("impairment_class"),
            "features": features, "model_version": out["model_version"],
            "quality_ok": bool(out["quality_ok"]), "breakdown": out.get("breakdown") or {}}
