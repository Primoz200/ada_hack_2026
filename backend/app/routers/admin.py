"""Meta and demo controls."""
from fastapi import APIRouter
from sqlmodel import select

from app import seed
from app.deps import Db
from app.models import Clinician
from app.models.schemas import ClinicianOut, MetaOut, ResetOut
from app.seed.pathways import DEFAULT_PATIENT_ID
from app.services import clock, scoring
from app.services.alerts import OUTCOME_LABELS

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/meta", response_model=MetaOut, operation_id="getMeta")
def get_meta(db: Db):
    return MetaOut(today=clock.today(),
                   clinicians=[ClinicianOut.model_validate(c) for c in db.exec(select(Clinician)).all()],
                   outcomes=OUTCOME_LABELS, model_version=scoring.current_model_version(),
                   default_patient_id=DEFAULT_PATIENT_ID)


@router.post("/admin/reset", response_model=ResetOut, operation_id="resetDemo")
def reset_demo():
    return ResetOut(ok=True, patients=seed.reset_database())
