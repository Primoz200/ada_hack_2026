"""Read-side helpers: table rows -> response models. Phase 0 has minimal versions;
agent B completes status / reason / sparkline / streak logic.
"""
from typing import Optional

from sqlmodel import Session, select

from app.models import Alert, Pathway, Patient
from app.models.schemas import AlertOut, PathwayOut
from app.seed.pathways import WARNING_PROMPTS


def pathway_out(p: Pathway) -> PathwayOut:
    return PathwayOut.model_validate({
        "code": p.code, "name": p.name, "frequency": p.frequency, "games": p.games,
        "questions": p.questions, "warningSigns": p.warning_signs,
        "warningSignsPrompt": WARNING_PROMPTS.get(p.code, "Ali opažate kaj od naštetega?"),
    })


def alert_out(db: Session, a: Alert) -> AlertOut:
    patient = db.get(Patient, a.patient_id)
    return AlertOut.model_validate({**a.model_dump(), "patient_name": patient.name if patient else ""})


def open_alert(db: Session, patient_id: str) -> Optional[Alert]:
    return db.exec(select(Alert).where(Alert.patient_id == patient_id, Alert.status != "closed")
                   .order_by(Alert.id.desc())).first()
