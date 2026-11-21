"""Clinician -> patient message. Kept minimal (add-on in the plan)."""
from fastapi import APIRouter, HTTPException

from app.deps import Db, require_patient
from app.models import Clinician, Message
from app.models.schemas import MessageIn, MessageOut
from app.services import clock

router = APIRouter(prefix="/api", tags=["messages"])


@router.post("/messages", response_model=MessageOut, operation_id="createMessage")
def create_message(data: MessageIn, db: Db):
    require_patient(db, data.patient_id)
    clinician = db.get(Clinician, data.clinician_id)
    if clinician is None:
        raise HTTPException(404, "Zdravnik ne obstaja")
    row = Message(patient_id=data.patient_id, direction="to_patient",
                  author=clinician.name, text=data.text, created_at=clock.now())
    db.add(row)
    db.commit()
    db.refresh(row)
    return MessageOut.model_validate(row)
