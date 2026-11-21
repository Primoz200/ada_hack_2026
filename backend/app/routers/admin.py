"""Demo controls. Phase 0: reset works; the Phase 2 agent implements simulate."""
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app import seed
from app.deps import Db
from app.models import Clinician
from app.models.schemas import ClinicianOut, MetaOut, ResetOut, SimulateIn, SimulateOut
from app.services import clock, scoring
from app.services.alerts import OUTCOME_LABELS

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/meta", response_model=MetaOut, operation_id="getMeta")
def get_meta(db: Db):
    return MetaOut(today=clock.today(),
                   clinicians=[ClinicianOut.model_validate(c) for c in db.exec(select(Clinician)).all()],
                   outcomes=OUTCOME_LABELS, model_version=scoring.current_model_version())


@router.post("/admin/reset", response_model=ResetOut, operation_id="resetDemo")
def reset_demo():
    return ResetOut(ok=True, patients=seed.reset_database())


@router.post("/admin/simulate", response_model=SimulateOut, operation_id="simulateDays")
def simulate_days(data: SimulateIn, db: Db):
    raise HTTPException(501, "Ni še implementirano")
