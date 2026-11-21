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


def _snapshots(session: Session, patient_id: str, as_of: date) -> list[TrendSnapshot]:
    """Load scored trace combined deltas from oldest to newest through the given day."""
    return list(
        session.exec(
            select(TrendSnapshot)
            .where(
                column("patient_id") == patient_id,
                column("metric") == "trace:all",
                column("day") <= as_of,
                column("delta").is_not(None),
            )
            .order_by(column("day"), column("id"))
        ).all()
    )


def _has_open_game_alert(session: Session, patient_id: str) -> bool:
    alerts = session.exec(
        select(Alert).where(
            column("patient_id") == patient_id,
            column("status").in_(["new", "acknowledged"]),
            column("severity").in_(["yellow", "red"]),
        )
    ).all()
    return any(
        alert.rule in GAME_ALERT_RULES
        or any(
            isinstance(trigger, dict) and trigger.get("rule") in GAME_ALERT_RULES
            for trigger in alert.evidence.get("triggers", [])
        )
        for alert in alerts
    )


def patient_feedback(session: Session, patient_id: str, as_of: date) -> FeedbackOut:
    """Return text-only trend feedback as of a date, without exposing a score."""
    snapshots = _snapshots(session, patient_id, as_of)
    tone: Literal["first", "better", "similar", "lower"]
    trend: Literal["unknown", "stable", "improving", "declining"]
    if not snapshots:
        tone, trend = "first", "unknown"
    else:
        deltas = [float(row.delta) for row in snapshots if row.delta is not None]
        prior = deltas[-(PRIOR_TONE_WINDOW + 1) : -1]
        difference = deltas[-1] - (mean(prior) if prior else 0.0)
        if difference >= TONE_BETTER_THRESHOLD:
            tone = "better"
        elif difference <= TONE_LOWER_THRESHOLD:
            tone = "lower"
        else:
            tone = "similar"

        if _has_open_game_alert(session, patient_id):
            trend = "declining"
        else:
            comparison_index = max(0, len(deltas) - 1 - TREND_SESSION_DAY_LOOKBACK)
            comparison = deltas[comparison_index]
            change = deltas[-1] - comparison
            if deltas[-1] <= -TREND_DELTA_THRESHOLD and change <= -TREND_CHANGE_THRESHOLD:
                trend = "declining"
            elif deltas[-1] >= TREND_DELTA_THRESHOLD and change >= TREND_CHANGE_THRESHOLD:
                trend = "improving"
            else:
                trend = "stable"

    message_tone = "first" if tone == "first" or trend == "unknown" else tone
    message_trend = "unknown" if message_tone == "first" else trend
    title, text = FEEDBACK_MESSAGES[(message_tone, message_trend)]
    return FeedbackOut(tone=tone, trend=trend, title=title, text=text)


def feedback_points(
    session: Session, patient_id: str, as_of: date, *, since: date | None = None
) -> list[FeedbackPoint]:
    """Return numeric trend points for charts, rounded and labelled for the patient."""
    snapshots = _snapshots(session, patient_id, as_of)
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
