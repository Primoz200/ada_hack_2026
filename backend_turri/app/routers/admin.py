"""Metadata and demo administration endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.api import ClinicianOut, MetaOut, ResetOut
from app.models.tables import Clinician
from app.seed.demo import reset_demo
from app.services.clock import today
from app.services.scoring import active_model_version

router = APIRouter(tags=["admin"])

OUTCOMES: dict[str, str] = {
    "called_reassured": "Poklical, pomiril",
    "adjusted_exercises": "Prilagodil vaje",
    "visit_moved_earlier": "Pregled prestavljen naprej",
    "urgent_referral": "Nujna napotitev",
    "unreachable": "Nedosegljiv",
    "false_alarm": "Lažni alarm ali težava s podatki",
}


@router.get("/api/meta", response_model=MetaOut, operation_id="getMeta")
def get_meta(session: Annotated[Session, Depends(get_session)]) -> MetaOut:
    """Return application date and frontend configuration metadata."""
    clinicians = list(session.exec(select(Clinician).order_by(Clinician.id)).all())
    return MetaOut(
        today=today(),
        synthetic_data=True,
        clinicians=[ClinicianOut.model_validate(clinician) for clinician in clinicians],
        outcomes=OUTCOMES,
        model_version=active_model_version(),
        default_patient_id="p3",
    )


@router.post("/api/admin/reset", response_model=ResetOut, operation_id="resetDemo")
def reset_demo_route(session: Annotated[Session, Depends(get_session)]) -> ResetOut:
    """Recreate the seeded synthetic demo database."""
    return ResetOut(ok=True, patients=reset_demo(session))
