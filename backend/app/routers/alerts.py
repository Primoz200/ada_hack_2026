"""STUB bodies (Phase 0): agent A completes ack / close."""
from typing import Literal

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.deps import Db
from app.models import Alert
from app.models.schemas import AlertAckIn, AlertOut
from app.services import alerts as alert_service
from app.services import queries

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts", response_model=list[AlertOut], operation_id="listAlerts")
def list_alerts(db: Db, status: Literal["open", "closed", "all"] = "open"):
    stmt = select(Alert).order_by(Alert.id.desc())
    if status == "open":
        stmt = stmt.where(Alert.status != "closed")
    elif status == "closed":
        stmt = stmt.where(Alert.status == "closed")
    return [queries.alert_out(db, a) for a in db.exec(stmt).all()]


@router.post("/alerts/{alert_id}/ack", response_model=AlertOut, operation_id="ackAlert")
def ack_alert(alert_id: int, data: AlertAckIn, db: Db):
    if db.get(Alert, alert_id) is None:
        raise HTTPException(404, "Opozorilo ne obstaja")
    try:
        alert = alert_service.acknowledge(db, alert_id, data.clinician_id, data.close, data.outcome, data.note)
    except alert_service.AlertError as e:
        raise HTTPException(422, str(e))
    except NotImplementedError:
        raise HTTPException(501, "Ni še implementirano")
    return queries.alert_out(db, alert)
