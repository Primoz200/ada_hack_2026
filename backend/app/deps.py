from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models import Patient

Db = Annotated[Session, Depends(get_session)]


def require_patient(db: Session, patient_id: str) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(404, "Pacient ne obstaja")
    return patient
