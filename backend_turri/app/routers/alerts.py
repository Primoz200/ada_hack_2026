"""Clinician alert listing and acknowledgement endpoints."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import column
from sqlmodel import Session, select

from app.db import get_session
from app.models.api import AlertAckIn, AlertOut
from app.models.tables import Alert, Clinician
from app.services.clock import now

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut], operation_id="listAlerts")
def list_alerts(
    session: Annotated[Session, Depends(get_session)],
    status: Literal["open", "closed", "all"] = "open",
) -> list[AlertOut]:
    """List open alerts, closed alerts, or all alerts by descending id."""
    statement = select(Alert)
    if status == "open":
        statement = statement.where(column("status").in_(["new", "acknowledged"]))
    elif status == "closed":
        statement = statement.where(column("status") == "closed")
    statement = statement.order_by(column("id").desc())
    return [AlertOut.model_validate(alert) for alert in session.exec(statement).all()]


@router.post("/{alert_id}/ack", response_model=AlertOut, operation_id="ackAlert")
def acknowledge_alert(
    alert_id: int,
    payload: AlertAckIn,
    session: Annotated[Session, Depends(get_session)],
) -> AlertOut:
    """Acknowledge or close an alert on behalf of its clinician."""
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Opozorilo ne obstaja")
    clinician = session.get(Clinician, payload.clinician_id)
    if clinician is None:
        raise HTTPException(status_code=404, detail="Zdravnik ne obstaja")
    if alert.status == "closed":
        raise HTTPException(status_code=422, detail="Opozorilo je že zaprto.")
    if payload.close and payload.outcome is None:
        raise HTTPException(
            status_code=422,
            detail="Opozorila ni mogoče zapreti brez izbranega izida.",
        )
    timestamp = now()
    alert.updated_at = timestamp
    if alert.acknowledged_at is None:
        alert.acknowledged_by = clinician.name
        alert.acknowledged_at = timestamp
    if payload.close:
        alert.status = "closed"
        alert.closed_by = clinician.name
        alert.closed_at = timestamp
        alert.outcome = payload.outcome
    else:
        alert.status = "acknowledged"
    if payload.note is not None:
        alert.note = payload.note
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return AlertOut.model_validate(alert)
