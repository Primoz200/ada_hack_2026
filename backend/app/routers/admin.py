"""Demo controls: reset the database and simulate the next N days."""
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app import seed
from app.seed import simulate
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
    try:
        return simulate.simulate(db, data.patient_id, data.days)
    except KeyError:
        raise HTTPException(404, "Pacient ne obstaja")
