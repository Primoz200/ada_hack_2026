"""Read path for patients. Phase 0: minimal bodies; agent B completes them."""
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.deps import Db, require_patient
from app.models import Alert, Checkin, GameSession, Pathway, Patient, TrendSnapshot
from app.models.schemas import (
    CheckinOut, PatientDetail, PatientHomeOut, PatientListItem, PatientListOut, PatientSummary, ProgressOut,
    ProgressPoint, SelfcheckSummary, SessionSummary, SparkPoint, TimelineOut, TrendPoint, TriageCounters,
)
from app.services import alerts, clock, queries

router = APIRouter(prefix="/api/patients", tags=["patients"])


def _pathway_names(db) -> dict:
    return {pw.code: pw for pw in db.exec(select(Pathway)).all()}


@router.get("", response_model=PatientListOut, operation_id="listPatients")
def list_patients(db: Db):
    today = clock.today()
    alerts.sweep(db, today)
    pathways = _pathway_names(db)
    rows = []
    for p in db.exec(select(Patient).order_by(Patient.sort_order)).all():
        st = queries.patient_state(db, p, today)
        item = PatientListItem(
            id=p.id, name=p.name, pathway_code=p.pathway_code, pathway_name=pathways[p.pathway_code].name,
            side=p.side, days_since_discharge=(today - p.discharge_date).days, status=st.status,
            reason=st.reason, diverging=st.diverging,
            sparkline=[SparkPoint(day=d, value=v) for d, v in queries.sparkline(db, p.id, today)],
            checkins_7d=queries.days_with_checkin(db, p.id, today, 7),
            days_to_next_visit=(p.next_visit_date - today).days if p.next_visit_date else None,
            open_alert_id=st.alert.id if st.alert else None, is_demo=p.is_demo)
        rows.append(((queries.URGENCY[st.status], -(st.alert.id if st.alert else 0), p.sort_order), item))
    rows.sort(key=lambda r: r[0])
    items = [r[1] for r in rows]
    n = lambda *statuses: sum(1 for i in items if i.status in statuses)  # noqa: E731
    counters = TriageCounters(needs_attention=n("red", "yellow"), no_data=n("no_data"),
                              stable=n("stable", "insufficient_data"), total=len(items))
    return PatientListOut(today=today, counters=counters, patients=items)


@router.get("/{patient_id}", response_model=PatientDetail, operation_id="getPatient")
def get_patient(patient_id: str, db: Db):
    p = require_patient(db, patient_id)
    today = clock.today()
    st = queries.patient_state(db, p, today)
    return PatientDetail(
        id=p.id, name=p.name, birth_year=p.birth_year,
        pathway=queries.pathway_out(db.get(Pathway, p.pathway_code)), side=p.side,
        discharge_date=p.discharge_date, next_visit_date=p.next_visit_date,
        days_since_discharge=(today - p.discharge_date).days,
        days_to_next_visit=(p.next_visit_date - today).days if p.next_visit_date else None,
        status=st.status, reason=st.reason, diverging=st.diverging,
        open_alert=queries.alert_out(db, st.alert) if st.alert else None,
        summary=PatientSummary(
            n_sessions=st.n_sessions, n_checkins=st.n_checkins,
            last_session_day=st.last_session_day, last_checkin_day=st.last_checkin_day,
            combined_delta=st.combined_delta, combined_direction=st.combined_direction),
        is_demo=p.is_demo)


@router.get("/{patient_id}/timeline", response_model=TimelineOut, operation_id="getTimeline")
def get_timeline(patient_id: str, db: Db):
    p = require_patient(db, patient_id)
    sessions = db.exec(select(GameSession).where(GameSession.patient_id == p.id)
                       .order_by(GameSession.started_at)).all()
    checkins = db.exec(select(Checkin).where(Checkin.patient_id == p.id).order_by(Checkin.day)).all()
    trends = db.exec(select(TrendSnapshot).where(TrendSnapshot.patient_id == p.id)
                     .order_by(TrendSnapshot.day)).all()
    alerts = db.exec(select(Alert).where(Alert.patient_id == p.id).order_by(Alert.id)).all()
    messages = db.exec(select(Message).where(Message.patient_id == p.id).order_by(Message.created_at)).all()
    return TimelineOut(
        patient_id=p.id, today=clock.today(), discharge_date=p.discharge_date,
        next_visit_date=p.next_visit_date,
        sessions=[SessionSummary.model_validate(s) for s in sessions],
        checkins=[CheckinOut.model_validate(c) for c in checkins],
        trends=[TrendPoint.model_validate(t) for t in trends],
        alerts=[queries.alert_out(db, a) for a in alerts],
        messages=[MessageOut.model_validate(m) for m in messages])


@router.get("/{patient_id}/home", response_model=PatientHomeOut, operation_id="getPatientHome")
def get_home(patient_id: str, db: Db):
    """Patient landing page: name and today's self-check steps."""
    raise HTTPException(501, "Ni še implementirano")


@router.get("/{patient_id}/selfcheck/summary", response_model=SelfcheckSummary,
            operation_id="getSelfcheckSummary")
def get_selfcheck_summary(patient_id: str, db: Db):
    """How today's self-check went compared with previous days (shown at the end)."""
    raise HTTPException(501, "Ni še implementirano")


@router.get("/{patient_id}/progress", response_model=ProgressOut, operation_id="getProgress")
def get_progress(patient_id: str, db: Db):
    """"Moj napredek": a very simple dashboard."""
    raise HTTPException(501, "Ni še implementirano")
