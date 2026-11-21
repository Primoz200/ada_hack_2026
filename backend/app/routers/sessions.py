from fastapi import APIRouter, HTTPException

from app.deps import Db, require_patient
from app.models import GameSession, SessionRaw
from app.models.schemas import SessionIn, SessionRawOut, SessionResult
from app.services import ingest

router = APIRouter(prefix="/api", tags=["sessions"])


@router.post("/sessions", response_model=SessionResult, operation_id="createSession")
def create_session(data: SessionIn, db: Db):
    require_patient(db, data.patient_id)
    if data.game_type == "trace" and data.level not in (1, 2, 3):
        raise HTTPException(422, "Neznana stopnja igre")
    row = ingest.ingest_session(db, data)
    return SessionResult(session_id=row.id, scored=row.score is not None)


@router.get("/sessions/{session_id}/raw", response_model=SessionRawOut, operation_id="getSessionRaw")
def get_session_raw(session_id: int, db: Db):
    row = db.get(GameSession, session_id)
    raw = db.get(SessionRaw, session_id)
    if row is None or raw is None:
        raise HTTPException(404, "Seja ne obstaja")
    return SessionRawOut(session_id=row.id, patient_id=row.patient_id, game_type=row.game_type,
                         level=row.level, day=row.day, score=row.score, series=raw.series,
                         client_meta=raw.client_meta)
