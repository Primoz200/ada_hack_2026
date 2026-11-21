"""Trend rules without a model (plan sections 5 and 8). Parameters are engineering
choices, not validated thresholds.

"""
from datetime import date
from statistics import median
from typing import Optional

from sqlmodel import Session, select

from app.models import GameSession, TrendSnapshot

from app.services.types import ScoredSession, TrendResult

TREND_VERSION = "rules-0.1"
EWMA_ALPHA = 0.3
PRACTICE_SESSIONS = 1  # the first session is practice and is discarded
BASELINE_SESSIONS = 3  # baseline = median of sessions 2-4
STABLE_BAND = 5.0  # |delta| below this many points counts as "stable"


def _direction(delta: Optional[float]) -> str:
    if delta is None:
        return "insufficient_data"
    if delta > STABLE_BAND:
        return "improving"
    if delta < -STABLE_BAND:
        return "declining"
    return "stable"


def _scores_after_practice(history: list[ScoredSession]) -> list[float]:
    return [h.score for h in history[PRACTICE_SESSIONS:]]


def baseline_of(history: list[ScoredSession]) -> Optional[float]:
    """Median of sessions 2-4 (the first one is practice); None until three exist."""
    scores = _scores_after_practice(history)
    if len(scores) < BASELINE_SESSIONS:
        return None
    return float(median(scores[:BASELINE_SESSIONS]))


def ewma_of(scores: list[float], alpha: float = EWMA_ALPHA) -> Optional[float]:
    """EWMA seeded with the first value. Sessions on the same day are simply consecutive."""
    if not scores:
        return None
    e = scores[0]
    for x in scores[1:]:
        e = alpha * x + (1 - alpha) * e
    return e


def assess_trend(history: list[ScoredSession]) -> TrendResult:
    """history: ALL past sessions of the same game AND level for one patient, ordered by time.

    Session 1 = practice (discarded); baseline = median of sessions 2-4; EWMA (alpha 0.3)
    over all sessions after the practice one; delta = EWMA - baseline.
    """
    n = len(history)
    baseline = baseline_of(history)
    if baseline is None:
        return TrendResult("insufficient_data", None, None, None, n, TREND_VERSION)
    smoothed = ewma_of(_scores_after_practice(history))
    delta = smoothed - baseline
    return TrendResult(_direction(delta), baseline, smoothed, delta, n, TREND_VERSION)


def combined_delta(level_deltas: dict[int, Optional[float]]) -> Optional[float]:
    """Combined trend of one day: mean of per-level deltas (EWMA - own baseline) over the
    levels that already have a baseline and were played that day. None if there are none."""
    vals = [v for v in level_deltas.values() if v is not None]
    return sum(vals) / len(vals) if vals else None


def _slope(scores: list[float], last: int = 7) -> Optional[float]:
    """Least-squares slope (points per session) of the last `last` post-practice scores."""
    ys = scores[-last:]
    if len(ys) < 3:
        return None
    n = len(ys)
    mx, my = (n - 1) / 2, sum(ys) / n
    den = sum((i - mx) ** 2 for i in range(n))
    return sum((i - mx) * (y - my) for i, y in enumerate(ys)) / den


def _upsert(db: Session, patient_id: str, metric: str, day: date, **values) -> None:
    row = db.exec(select(TrendSnapshot).where(
        TrendSnapshot.patient_id == patient_id, TrendSnapshot.metric == metric,
        TrendSnapshot.day == day)).first()
    if row is None:
        row = TrendSnapshot(patient_id=patient_id, metric=metric, day=day, n_sessions=0)
    for k, v in values.items():
        setattr(row, k, v)
    db.add(row)


def level_history(db: Session, patient_id: str, game_type: str, level: int,
                  upto: date) -> list[ScoredSession]:
    """Scored sessions counting for the trend of one level up to and including `upto`,
    in time order (day, start, id)."""
    rows = db.exec(select(GameSession).where(
        GameSession.patient_id == patient_id, GameSession.game_type == game_type,
        GameSession.level == level, GameSession.counts_for_trend == True,  # noqa: E712
        GameSession.score != None, GameSession.day <= upto  # noqa: E711
    ).order_by(GameSession.day, GameSession.started_at, GameSession.id)).all()
    return [ScoredSession(r.day, r.duration_ms, r.level, r.score, r.features) for r in rows]


def recompute_trends(db: Session, patient_id: str, game_type: str, day: date) -> None:
    """Recompute and upsert TrendSnapshot rows for `day`: one per level played that day
    (metric "<game>:<level>") and the combined one ("<game>:all").

    Combined row: baseline/ewma None, n_sessions = number of session-days so far, delta =
    mean of the per-level deltas of levels with a baseline that were played that day.
    """
    rows = db.exec(select(GameSession).where(
        GameSession.patient_id == patient_id, GameSession.game_type == game_type,
        GameSession.counts_for_trend == True, GameSession.score != None,  # noqa: E712,E711
        GameSession.day <= day)).all()
    levels_today = sorted({r.level for r in rows if r.day == day})
    if not levels_today:
        return
    deltas: dict[int, Optional[float]] = {}
    for level in levels_today:
        hist = level_history(db, patient_id, game_type, level, day)
        res = assess_trend(hist)
        deltas[level] = res.delta_vs_baseline
        pct = (res.delta_vs_baseline / res.baseline * 100.0
               if res.baseline else None)
        _upsert(db, patient_id, f"{game_type}:{level}", day, n_sessions=res.n_sessions,
                baseline=res.baseline, ewma=res.smoothed, delta=res.delta_vs_baseline,
                delta_pct=pct, slope=_slope(_scores_after_practice(hist)), direction=res.direction)
    delta = combined_delta(deltas)
    session_days = len({r.day for r in rows})
    _upsert(db, patient_id, f"{game_type}:all", day, n_sessions=session_days, baseline=None,
            ewma=None, delta=delta, delta_pct=None, slope=None, direction=_direction(delta))
    db.flush()
