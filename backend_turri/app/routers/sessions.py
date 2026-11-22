"""Game-session ingestion and raw-result endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models.api import SessionIn, SessionRawOut, SessionResult
from app.models.tables import GameSession, GameSessionRaw, Pathway, Patient
from app.services.ingest import PatientNotFoundError, ingest_game_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResult, operation_id="createSession")
def create_session(
    payload: SessionIn,
    session: Annotated[Session, Depends(get_session)],
) -> SessionResult:
    """Store a game result and score completed sessions."""
    patient = session.get(Patient, payload.patient_id)
    if patient is not None:
        pathway = session.get(Pathway, patient.pathway_code)
        game = (
            next(
                (item for item in pathway.games if item.get("gameType") == payload.game_type),
                None,
            )
            if pathway is not None
            else None
        )
        if game is None or payload.level not in game.get("levels", []):
            raise HTTPException(status_code=422, detail="Neznana stopnja igre")
    try:
        stored, scored = ingest_game_session(
            session,
            patient_id=payload.patient_id,
            game_type=payload.game_type,
            level=payload.level,
            hand=payload.hand,
            started_at=payload.started_at,
            duration_ms=payload.duration_ms,
            completed=payload.completed,
            abort_reason=payload.abort_reason,
            series=payload.series,
            client_meta=payload.client_meta.model_dump(by_alias=True),
        )
    except PatientNotFoundError as error:
        logger.exception("Game-session ingestion rejected for unknown patient: %s", error)
        raise HTTPException(status_code=404, detail="Pacient ne obstaja") from error
    if stored.id is None:
        raise RuntimeError("Game-session ingestion did not assign a database id")
    return SessionResult(session_id=stored.id, scored=scored)


@router.get("/{session_id}/raw", response_model=SessionRawOut, operation_id="getSessionRaw")
def get_session_raw(
    session_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> SessionRawOut:
    """Return the raw payload for one session without loading raw data in listings."""
    game_session = session.get(GameSession, session_id)
    if game_session is None:
        raise HTTPException(status_code=404, detail="Seja ne obstaja")
    raw = session.get(GameSessionRaw, session_id)
    if raw is None:
        raise RuntimeError(f"Raw payload missing for game session {session_id}")
    return SessionRawOut(
        session_id=session_id,
        patient_id=game_session.patient_id,
        game_type=game_session.game_type,
        level=game_session.level,
        day=game_session.day,
        score=game_session.score,
        series=raw.series,
        client_meta=raw.client_meta,
    )
