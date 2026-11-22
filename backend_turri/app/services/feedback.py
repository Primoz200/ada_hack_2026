"""Patient-facing feedback derived from persisted trace trend snapshots."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from statistics import mean
from typing import Literal

from sqlalchemy import column
from sqlmodel import Session, select

from app.models.api import FeedbackOut, FeedbackPoint
from app.models.tables import Alert, TrendSnapshot

logger = logging.getLogger(__name__)

TONE_BETTER_THRESHOLD = 3.0
TONE_LOWER_THRESHOLD = -3.0
TREND_DELTA_THRESHOLD = 5.0
TREND_CHANGE_THRESHOLD = 3.0
PRIOR_TONE_WINDOW = 5
TREND_SESSION_DAY_LOOKBACK = 5
POINT_LOWER_THRESHOLD = -5.0
POINT_BETTER_THRESHOLD = 5.0
GAME_ALERT_RULES = {"trend_drop", "big_drop", "both"}


# The source markdown is deliberately kept as the sole copy of these patient messages.
_MESSAGES_PATH = Path(__file__).resolve().parents[2] / "resources" / "feedback_messages.md"


def _load_messages() -> dict[tuple[str, str], tuple[str, str]]:
    """Parse the feedback message table from its linked resource."""
    messages: dict[tuple[str, str], tuple[str, str]] = {}
    for line in _MESSAGES_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| tone"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4:
            tone, trend, title, text = cells
            messages[(tone, trend)] = (title, text)
    return messages


FEEDBACK_MESSAGES = _load_messages()


def _snapshots(
    session: Session, patient_id: str, as_of: date, game_type: str = "trace"
) -> list[TrendSnapshot]:
    """Load combined deltas for one game's history from oldest to newest."""
    return list(
        session.exec(
            select(TrendSnapshot)
            .where(
                column("patient_id") == patient_id,
                column("metric") == f"{game_type}:all",
                column("day") <= as_of,
                column("delta").is_not(None),
            )
            .order_by(column("day"), column("id"))
        ).all()
    )


def _has_open_game_alert(session: Session, patient_id: str, game_type: str = "trace") -> bool:
    alerts = session.exec(
        select(Alert).where(
            column("patient_id") == patient_id,
            column("status").in_(["new", "acknowledged"]),
            column("severity").in_(["yellow", "red"]),
        )
    ).all()
    for alert in alerts:
        triggers = [item for item in alert.evidence.get("triggers", []) if isinstance(item, dict)]
        if not triggers and alert.rule in GAME_ALERT_RULES and game_type == "trace":
            return True
        if any(
            trigger.get("rule") in GAME_ALERT_RULES and trigger.get("game", "trace") == game_type
            for trigger in triggers
        ):
            return True
    return False


def _single_game_trend(
    session: Session, patient_id: str, game_type: str, snapshots: list[TrendSnapshot]
) -> str:
    deltas = [float(row.delta) for row in snapshots if row.delta is not None]
    if _has_open_game_alert(session, patient_id, game_type):
        return "declining"
    comparison_index = max(0, len(deltas) - 1 - TREND_SESSION_DAY_LOOKBACK)
    change = deltas[-1] - deltas[comparison_index]
    if deltas[-1] <= -TREND_DELTA_THRESHOLD and change <= -TREND_CHANGE_THRESHOLD:
        return "declining"
    if deltas[-1] >= TREND_DELTA_THRESHOLD and change >= TREND_CHANGE_THRESHOLD:
        return "improving"
    return "stable"


def patient_feedback(
    session: Session, patient_id: str, as_of: date, game_type: str | None = None
) -> FeedbackOut:
    """Return text-only feedback; game-specific calls retain a separate trend."""
    if game_type is not None:
        histories = {game_type: _snapshots(session, patient_id, as_of, game_type)}
        histories = {game: rows for game, rows in histories.items() if rows}
    else:
        histories = {
            game: rows
            for game in ("trace", "camera")
            if (rows := _snapshots(session, patient_id, as_of, game))
        }
    tone: Literal["first", "better", "similar", "lower"]
    trend: Literal["unknown", "stable", "improving", "declining"]
    if not histories:
        tone, trend = "first", "unknown"
    else:
        if game_type is not None:
            deltas = [
                float(row.delta) for row in next(iter(histories.values())) if row.delta is not None
            ]
            differences = [
                deltas[-1]
                - (mean(deltas[-(PRIOR_TONE_WINDOW + 1) : -1]) if len(deltas) > 1 else 0.0)
            ]
            trend_values = [
                _single_game_trend(session, patient_id, game_type, next(iter(histories.values())))
            ]
        else:
            described_day = max(rows[-1].day for rows in histories.values())
            differences = []
            trend_values = []
            for game, rows in histories.items():
                deltas = [float(row.delta) for row in rows if row.delta is not None]
                if rows[-1].day == described_day:
                    prior = deltas[-(PRIOR_TONE_WINDOW + 1) : -1]
                    differences.append(deltas[-1] - (mean(prior) if prior else 0.0))
                trend_values.append(_single_game_trend(session, patient_id, game, rows))
        difference = mean(differences)
        tone = (
            "better"
            if difference >= TONE_BETTER_THRESHOLD
            else "lower"
            if difference <= TONE_LOWER_THRESHOLD
            else "similar"
        )
        trend = (
            "declining"
            if "declining" in trend_values
            else "improving"
            if "improving" in trend_values
            else "stable"
        )

    message_tone = "first" if tone == "first" or trend == "unknown" else tone
    message_trend = "unknown" if message_tone == "first" else trend
    title, text = FEEDBACK_MESSAGES[(message_tone, message_trend)]
    return FeedbackOut(tone=tone, trend=trend, title=title, text=text)


def feedback_points(
    session: Session,
    patient_id: str,
    as_of: date,
    *,
    since: date | None = None,
    game_type: str = "trace",
) -> list[FeedbackPoint]:
    """Return numeric trend points for charts, rounded and labelled for the patient."""
    snapshots = _snapshots(session, patient_id, as_of, game_type)
    points: list[FeedbackPoint] = []
    for row in snapshots:
        if since is not None and row.day < since:
            continue
        if row.delta is None:
            continue
        delta = round(float(row.delta), 1)
        label: Literal["lower", "better", "usual"]
        if delta <= POINT_LOWER_THRESHOLD:
            label = "lower"
        elif delta >= POINT_BETTER_THRESHOLD:
            label = "better"
        else:
            label = "usual"
        points.append(FeedbackPoint(day=row.day, value=delta, label=label))
    return points
