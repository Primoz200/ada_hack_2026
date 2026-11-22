"""Shared ingestion operations for patient-generated data."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlmodel import Session, select

from app.models.tables import Checkin, GameSession, GameSessionRaw, Patient
from app.services import clock
from app.services.alerts import evaluate_alerts
from app.services.scoring import impairment_class, score_session
from app.services.trends import recompute_trend_snapshots


class PatientNotFoundError(LookupError):
    """Raised when ingest data references a patient outside the registry."""


def ingest_checkin(
    session: Session,
    patient_id: str,
    wellbeing: int,
    pain: int,
    *,
    day: date | None = None,
    created_at: datetime | None = None,
) -> Checkin:
    """Create or replace a patient's check-in for one day.

    The optional date and creation-time overrides support deterministic demo ingestion.
    """
    if session.get(Patient, patient_id) is None:
        raise PatientNotFoundError(f"No patient with id {patient_id!r}")

    checkin_day = day or clock.today()
    timestamp = created_at or clock.now()
    checkin = session.exec(
        select(Checkin).where(
            Checkin.patient_id == patient_id,
            Checkin.day == checkin_day,
        )
    ).first()
    answers: dict[str, float] = {"wellbeing": float(wellbeing), "pain": float(pain)}
    if checkin is None:
        checkin = Checkin(
            patient_id=patient_id,
            day=checkin_day,
            created_at=timestamp,
            answers=answers,
        )
        session.add(checkin)
    else:
        checkin.created_at = timestamp
        checkin.answers = answers
        session.add(checkin)

    session.commit()
    session.refresh(checkin)
    evaluate_alerts(
        session,
        patient_id,
        checkin_day,
        evaluated_at=timestamp if checkin_day == clock.today() else None,
    )
    session.refresh(checkin)
    return checkin


def ingest_game_session(
    session: Session,
    *,
    patient_id: str,
    game_type: str,
    level: int,
    hand: str,
    started_at: datetime,
    duration_ms: int,
    completed: bool,
    abort_reason: str | None,
    series: dict[str, list[float | None]],
    client_meta: dict[str, Any],
    day: date | None = None,
    preset_score: float | None = None,
    preset_features: dict[str, float] | None = None,
    preset_model_version: str = "standin-0.1",
    preset_quality_ok: bool | None = None,
) -> tuple[GameSession, bool]:
    """Store one game result and, when completed, its score and trend snapshots."""
    if session.get(Patient, patient_id) is None:
        raise PatientNotFoundError(f"No patient with id {patient_id!r}")

    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)
    else:
        started_at = started_at.astimezone(UTC)

    session_day = day or clock.today()
    score_result: dict[str, Any] | None = None
    if completed:
        if preset_score is not None:
            score_result = {
                "score": preset_score,
                "impairment_class": impairment_class(preset_score),
                "features": preset_features or {},
                "model_version": preset_model_version,
                "quality_ok": preset_quality_ok,
            }
        else:
            score_result = score_session(game_type, level, hand, duration_ms, series, client_meta)
    game_session = GameSession(
        patient_id=patient_id,
        game_type=game_type,
        level=level,
        hand=hand,
        started_at=started_at,
        day=session_day,
        duration_ms=duration_ms,
        completed=completed,
        abort_reason=abort_reason,
        input_device=str(client_meta["inputDevice"]),
        score=float(score_result["score"])
        if score_result is not None and score_result.get("score") is not None
        else None,
        impairment_class=(
            str(score_result["impairment_class"])
            if score_result is not None and score_result.get("impairment_class") is not None
            else None
        ),
        model_version=str(score_result["model_version"]) if score_result is not None else None,
        features=score_result["features"] if score_result is not None else {},
        counts_for_trend=bool(
            score_result is not None
            and score_result.get("score") is not None
            and score_result.get("quality_ok") is not False
        ),
        quality_ok=score_result.get("quality_ok") if score_result is not None else None,
    )
    session.add(game_session)
    session.flush()
    if game_session.id is None:
        raise RuntimeError("Game-session ingestion did not assign a database id")
    session.add(
        GameSessionRaw(
            session_id=game_session.id,
            series=series,
            client_meta=client_meta,
        )
    )
    if game_session.counts_for_trend:
        recompute_trend_snapshots(session, patient_id, game_type, game_session.day)
    else:
        session.commit()
    session.refresh(game_session)
    evaluate_alerts(session, patient_id, game_session.day)
    return game_session, game_session.counts_for_trend
