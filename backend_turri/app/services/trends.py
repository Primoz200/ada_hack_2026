"""Trend calculations and daily snapshot persistence."""

from __future__ import annotations

from datetime import date
from statistics import median
from typing import TypedDict

from sqlalchemy import column
from sqlmodel import Session, select

from app.models.tables import GameSession, TrendSnapshot

EWMA_ALPHA = 0.3
TREND_BAND_POINTS = 5.0
BASELINE_SESSION_COUNT = 3
SLOPE_WINDOW_SESSIONS = 7


class TrendValues(TypedDict):
    sessions: int
    baseline: float | None
    ewma: float | None
    slope: float | None
    delta: float | None
    delta_percent: float | None
    direction: str


def _direction(delta: float | None) -> str:
    if delta is None:
        return "insufficient_data"
    if delta > TREND_BAND_POINTS:
        return "improving"
    if delta < -TREND_BAND_POINTS:
        return "declining"
    return "stable"


def _least_squares_slope(scores: list[float]) -> float | None:
    if len(scores) < 3:
        return None
    recent = scores[-SLOPE_WINDOW_SESSIONS:]
    mean_x = (len(recent) - 1) / 2
    mean_y = sum(recent) / len(recent)
    numerator = sum((index - mean_x) * (score - mean_y) for index, score in enumerate(recent))
    denominator = sum((index - mean_x) ** 2 for index in range(len(recent)))
    return numerator / denominator


def _level_trend(rows: list[GameSession]) -> TrendValues:
    scores = [row.score for row in rows if row.score is not None]
    practice_and_later = scores[1:]
    baseline = (
        median(practice_and_later[:BASELINE_SESSION_COUNT])
        if len(practice_and_later) >= BASELINE_SESSION_COUNT
        else None
    )
    ewma = practice_and_later[0] if baseline is not None and practice_and_later else None
    if baseline is not None:
        for score in practice_and_later[1:]:
            assert ewma is not None
            ewma = EWMA_ALPHA * score + (1 - EWMA_ALPHA) * ewma
    delta = ewma - baseline if ewma is not None and baseline is not None else None
    delta_percent = delta / baseline * 100 if delta is not None and baseline else None
    slope = _least_squares_slope(practice_and_later) if baseline is not None else None
    return {
        "sessions": len(scores),
        "baseline": baseline,
        "ewma": ewma,
        "slope": slope,
        "delta": delta,
        "delta_percent": delta_percent,
        "direction": _direction(delta),
    }


def _upsert_snapshot(
    session: Session,
    *,
    patient_id: str,
    metric: str,
    day: date,
    values: TrendValues,
) -> None:
    snapshot = session.exec(
        select(TrendSnapshot).where(
            TrendSnapshot.patient_id == patient_id,
            TrendSnapshot.metric == metric,
            TrendSnapshot.day == day,
        )
    ).first()
    if snapshot is None:
        snapshot = TrendSnapshot(
            patient_id=patient_id,
            metric=metric,
            day=day,
            sessions=int(values["sessions"] or 0),
            baseline=values["baseline"],
            ewma=values["ewma"],
            slope=values["slope"],
            delta=values["delta"],
            delta_percent=values["delta_percent"],
            direction=str(values["direction"]),
        )
    else:
        snapshot.sessions = int(values["sessions"] or 0)
        snapshot.baseline = values["baseline"]
        snapshot.ewma = values["ewma"]
        snapshot.slope = values["slope"]
        snapshot.delta = values["delta"]
        snapshot.delta_percent = values["delta_percent"]
        snapshot.direction = str(values["direction"])
    session.add(snapshot)


def recompute_trend_snapshots(session: Session, patient_id: str, game_type: str, day: date) -> None:
    """Recompute today's level trends and combined trend after a scored session."""
    rows = list(
        session.exec(
            select(GameSession)
            .where(
                column("patient_id") == patient_id,
                column("game_type") == game_type,
                column("day") <= day,
                column("counts_for_trend").is_(True),
                column("score").is_not(None),
            )
            .order_by(column("day"), column("started_at"), column("id"))
        ).all()
    )
    today_rows = [row for row in rows if row.day == day]
    played_today = sorted({row.level for row in today_rows})
    level_latest: dict[int, TrendValues] = {}
    for level in played_today:
        level_rows = [row for row in rows if row.level == level]
        result = _level_trend(level_rows)
        level_latest[level] = result
        _upsert_snapshot(
            session,
            patient_id=patient_id,
            metric=f"{game_type}:{level}",
            day=day,
            values=result,
        )

    # Retain the most recent usable level delta even if that level was not played today.
    all_levels = sorted({row.level for row in rows})
    deltas: list[float] = []
    for level in all_levels:
        trend = level_latest.get(level)
        if trend is None:
            trend = _level_trend([row for row in rows if row.level == level])
        if trend["delta"] is not None:
            deltas.append(float(trend["delta"]))
    combined_delta = sum(deltas) / len(deltas) if deltas else None
    distinct_days = len({row.day for row in rows})
    combined: TrendValues = {
        "sessions": distinct_days,
        "baseline": None,
        "ewma": None,
        "slope": None,
        "delta": combined_delta,
        "delta_percent": None,
        "direction": _direction(combined_delta),
    }
    _upsert_snapshot(
        session,
        patient_id=patient_id,
        metric=f"{game_type}:all",
        day=day,
        values=combined,
    )
    session.commit()
