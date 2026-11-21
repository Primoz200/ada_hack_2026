"""The single write path. The API and the seed both go through these two functions, so
charts, scores and alerts always agree.

Store + score, trend, alerts. v8: no per-submission patient feedback; the patient gets one
sentence at the end of the self-check (app.services.feedback).
"""
from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models import Checkin, GameSession, SessionRaw
from app.models.schemas import CheckinIn, SessionIn
from app.services import alerts, clock, scoring, trend
from app.services.types import ScoreResult


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def ingest_session(db: Session, data: SessionIn, *, day: Optional[date] = None,
                   created_at: Optional[datetime] = None,
                   preset_score: Optional[ScoreResult] = None) -> GameSession:
    """Store raw data, score, recompute trends, evaluate alerts. Returns the stored row
    (row.score is None for an aborted attempt, a camera recording of poor capture quality or
    one that could not be scored: stored with its raw series, not in the trend).

    day / created_at: override "today" (seed replay). preset_score: the seed passes a
    score from its story curve instead of scoring the recording (ScoreResult.quality_ok
    sets GameSession.quality_ok, e.g. True for seeded camera sessions). A repeated session
    of the same level on the same day is stored too and both count.
    """
    day = day or clock.today()
    # extra client keys (camera: videoW, videoH, fpsMeasured, detector ...) are kept: the camera
    # scorer reads them and they are stored with the raw series
    meta = data.client_meta.model_dump(by_alias=True)
    result = None
    if data.completed:
        result = preset_score or scoring.score_session(
            data.game_type, data.level, data.hand, data.duration_ms, data.series, meta)
    # aborted, poor capture quality (camera) or not scorable: stored, not in the trend
    scored = result is not None and result.score is not None and result.quality_ok is not False
    row = GameSession(
        patient_id=data.patient_id, game_type=data.game_type, level=data.level, hand=data.hand,
        started_at=created_at or _aware(data.started_at), day=day,
        duration_ms=data.duration_ms, completed=data.completed, abort_reason=data.abort_reason,
        input_device=data.client_meta.input_device,
        score=result.score if scored else None,
        impairment_class=result.impairment_class if scored else None,
        model_version=result.model_version if result else None,
        features=result.features if result else {},
        counts_for_trend=scored,
        quality_ok=result.quality_ok if result else None,
    )
    db.add(row)
    db.flush()
    db.add(SessionRaw(session_id=row.id, series=data.series, client_meta=meta))
    db.flush()
    if scored:
        trend.recompute_trends(db, data.patient_id, data.game_type, day)
    # also for aborted sessions: any entry closes a grey "no data" alert
    alerts.evaluate_alerts(db, data.patient_id, day)
    db.commit()
    db.refresh(row)
    return row


def ingest_checkin(db: Session, data: CheckinIn, *, day: Optional[date] = None,
                   created_at: Optional[datetime] = None) -> Checkin:
    """Store the two ratings and evaluate alerts. One check-in per patient per day: a
    second one on the same day replaces the first."""
    day = day or clock.today()
    answers = {"wellbeing": float(data.wellbeing), "pain": float(data.pain)}
    row = db.exec(select(Checkin).where(Checkin.patient_id == data.patient_id, Checkin.day == day)
                  .order_by(Checkin.id)).first()
    if row is None:
        row = Checkin(patient_id=data.patient_id, day=day, created_at=created_at or clock.now(),
                      answers=answers)
    else:
        row.answers, row.created_at = answers, created_at or clock.now()
    db.add(row)
    db.flush()
    alerts.evaluate_alerts(db, data.patient_id, day)
    db.commit()
    db.refresh(row)
    return row
