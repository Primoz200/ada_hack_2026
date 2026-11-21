"""Patient check-in endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models.api import CheckinIn, CheckinResult
from app.services.ingest import PatientNotFoundError, ingest_checkin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/checkins", tags=["checkins"])


@router.post("", response_model=CheckinResult, operation_id="createCheckin")
def create_checkin(
    payload: CheckinIn,
    session: Annotated[Session, Depends(get_session)],
) -> CheckinResult:
    """Store the patient's two daily ratings, replacing today's earlier check-in."""
    try:
        checkin = ingest_checkin(
            session,
            patient_id=payload.patient_id,
            wellbeing=payload.wellbeing,
            pain=payload.pain,
        )
    except PatientNotFoundError as error:
        logger.exception("Check-in ingestion rejected for unknown patient: %s", error)
        raise HTTPException(status_code=404, detail="Pacient ne obstaja") from error
    if checkin.id is None:
        raise RuntimeError("Check-in ingestion did not assign a database id")
    return CheckinResult(checkin_id=checkin.id)
