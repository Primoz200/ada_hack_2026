"""The single write path. The API, the seed and admin simulate all go through these
two functions, so charts, scores and alerts always agree.

Phase 0 has a minimal version (store + score). Agent A completes it: trend, alerts,
feedback wording.
"""
from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Session

from app.models import Checkin, GameSession, SessionRaw
from app.models.schemas import CheckinIn, SessionIn
from app.services import alerts, clock, scoring, trend
from app.services.types import Feedback, ScoreResult

def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


THANKS = Feedback("thanks", "Hvala!", "Poslano vašemu zdravniku.")


def ingest_session(db: Session, data: SessionIn, *, day: Optional[date] = None,
                   created_at: Optional[datetime] = None,
                   preset_score: Optional[ScoreResult] = None
                   ) -> tuple[GameSession, Feedback, dict]:
    """Store raw data, score, recompute trends, evaluate alerts.

    day / created_at: override "today" (seed replay). preset_score: the seed passes a
    score from its story curve instead of scoring the trace.
    Returns (session row, patient feedback, extras) where extras has
    compared_to_usual, offer_retry, personal_best.
    """
    day = day or clock.today()
    meta = data.client_meta.model_dump(by_alias=True)
    scored = data.completed
    result = None
    if scored:
        result = preset_score or scoring.score_session(
            data.game_type, data.level, data.hand, data.duration_ms, data.series, meta)
    row = GameSession(
        patient_id=data.patient_id, game_type=data.game_type, level=data.level, hand=data.hand,
        started_at=created_at or _aware(data.started_at), day=day,
        duration_ms=data.duration_ms, completed=data.completed, abort_reason=data.abort_reason,
        input_device=data.client_meta.input_device,
        score=result.score if result else None,
        impairment_class=result.impairment_class if result else None,
        model_version=result.model_version if result else None,
        features=result.features if result else {},
        counts_for_trend=scored,
    )
    db.add(row)
    db.flush()
    db.add(SessionRaw(session_id=row.id, series=data.series, client_meta=meta))
    db.flush()
    if scored:
        trend.recompute_trends(db, data.patient_id, data.game_type, day)
        alerts.evaluate_alerts(db, data.patient_id, day)
    db.commit()
    db.refresh(row)
    extras = {"compared_to_usual": "first" if scored else "not_scored",
              "offer_retry": False, "personal_best": False}
    return row, THANKS, extras


def ingest_checkin(db: Session, data: CheckinIn, *, day: Optional[date] = None,
                   created_at: Optional[datetime] = None) -> tuple[Checkin, Feedback]:
    """Store the check-in, check warning signs and symptom rules, evaluate alerts."""
    day = day or clock.today()
    row = Checkin(
        patient_id=data.patient_id, day=day, created_at=created_at or clock.now(),
        warning_signs=data.warning_signs, answers=data.answers, concern=data.concern,
        concern_text=data.concern_text, answered_by=data.answered_by,
    )
    db.add(row)
    db.flush()
    alerts.evaluate_alerts(db, data.patient_id, day)
    db.commit()
    db.refresh(row)
    return row, THANKS
