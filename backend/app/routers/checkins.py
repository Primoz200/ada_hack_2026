from fastapi import APIRouter

from app.deps import Db, require_patient
from app.models.schemas import CheckinIn, CheckinResult
from app.services import ingest

router = APIRouter(prefix="/api", tags=["checkins"])


@router.post("/checkins", response_model=CheckinResult, operation_id="createCheckin")
def create_checkin(data: CheckinIn, db: Db):
    require_patient(db, data.patient_id)
    row, fb = ingest.ingest_checkin(db, data)
    return CheckinResult(checkin_id=row.id, message_level=fb.level, message_title=fb.title,
                         message_text=fb.text)
