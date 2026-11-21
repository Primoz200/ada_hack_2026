"""Trend rules without a model (plan sections 5 and 8). Parameters are engineering
choices, not validated thresholds.

STUB (Phase 0): agent A implements the bodies. Signatures are fixed.
"""
from datetime import date
from typing import Optional

from app.services.types import ScoredSession, TrendResult

TREND_VERSION = "rules-0.1"
EWMA_ALPHA = 0.3
PRACTICE_SESSIONS = 1  # the first session is practice and is discarded
BASELINE_SESSIONS = 3  # baseline = median of sessions 2-4
STABLE_BAND = 5.0  # |delta| below this many points counts as "stable"


def assess_trend(history: list[ScoredSession]) -> TrendResult:
    """history: ALL past sessions of the same game AND level for one patient, ordered by time."""
    return TrendResult("insufficient_data", None, None, None, len(history), TREND_VERSION)


def combined_delta(level_deltas: dict[int, Optional[float]]) -> Optional[float]:
    """Combined trend of one day: mean of per-level deltas (EWMA - own baseline) over the
    levels that already have a baseline and were played that day. None if there are none."""
    vals = [v for v in level_deltas.values() if v is not None]
    return sum(vals) / len(vals) if vals else None


def recompute_trends(db, patient_id: str, game_type: str, day: date) -> None:
    """Recompute and upsert TrendSnapshot rows for `day`: one per level played that day
    (metric "<game>:<level>") and the combined one ("<game>:all")."""
    return None
