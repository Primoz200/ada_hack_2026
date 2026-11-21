"""Read path for patients. Phase 0: minimal bodies; agent B completes them."""
from fastapi import APIRouter
from sqlmodel import select

from app.deps import Db, require_patient
from app.models import Checkin, GameSession, Message, Pathway, Patient, TrendSnapshot, Alert
from app.models.schemas import (
    CheckinOut, MessageOut, PatientDetail, PatientListItem, PatientListOut, PatientSummary,
    ProgressOut, SessionSummary, TimelineOut, TodayOut, TodayTask, TrendPoint, TriageCounters,
)
from app.services import clock, queries

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=PatientListOut, operation_id="listPatients")
def list_patients(db: Db):
    today = clock.today()
    items = []
    for p in db.exec(select(Patient).order_by(Patient.sort_order)).all():
        pathway = db.get(Pathway, p.pathway_code)
        alert = queries.open_alert(db, p.id)
        items.append(PatientListItem(
            id=p.id, name=p.name, pathway_code=p.pathway_code, pathway_name=pathway.name, side=p.side,
            days_since_discharge=(today - p.discharge_date).days, status="stable",
            reason="Brez posebnosti.", diverging=False, sparkline=[], checkins_7d=0,
            days_to_next_visit=(p.next_visit_date - today).days if p.next_visit_date else None,
            open_alert_id=alert.id if alert else None, is_demo=p.is_demo))
    counters = TriageCounters(needs_attention=0, no_data=0, stable=len(items), total=len(items))
    return PatientListOut(today=today, counters=counters, patients=items)


@router.get("/{patient_id}", response_model=PatientDetail, operation_id="getPatient")
def get_patient(patient_id: str, db: Db):
    p = require_patient(db, patient_id)
    today = clock.today()
    alert = queries.open_alert(db, p.id)
    sessions = db.exec(select(GameSession).where(GameSession.patient_id == p.id)).all()
    checkins = db.exec(select(Checkin).where(Checkin.patient_id == p.id)).all()
    return PatientDetail(
        id=p.id, name=p.name, birth_year=p.birth_year,
        pathway=queries.pathway_out(db.get(Pathway, p.pathway_code)), side=p.side,
        discharge_date=p.discharge_date, next_visit_date=p.next_visit_date,
        days_since_discharge=(today - p.discharge_date).days,
        days_to_next_visit=(p.next_visit_date - today).days if p.next_visit_date else None,
        status="stable", reason="Brez posebnosti.", diverging=False,
        open_alert=queries.alert_out(db, alert) if alert else None,
        summary=PatientSummary(
            n_sessions=len(sessions), n_checkins=len(checkins),
            last_session_day=max((s.day for s in sessions), default=None),
            last_checkin_day=max((c.day for c in checkins), default=None),
            combined_delta=None, combined_direction="insufficient_data"),
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


@router.get("/{patient_id}/today", response_model=TodayOut, operation_id="getToday")
def get_today(patient_id: str, db: Db):
    p = require_patient(db, patient_id)
    today = clock.today()
    pathway = db.get(Pathway, p.pathway_code)
    done_levels = {(s.game_type, s.level) for s in db.exec(
        select(GameSession).where(GameSession.patient_id == p.id, GameSession.day == today)).all()}
    checkin_done = db.exec(select(Checkin).where(Checkin.patient_id == p.id, Checkin.day == today)).first()
    tasks = [TodayTask(id="checkin", kind="checkin", title="Kako ste danes?", done=checkin_done is not None)]
    for game in pathway.games:
        for level in game["levels"]:
            tasks.append(TodayTask(
                id=f"{game['gameType']}:{level}", kind="game", title=game["title"],
                game_type=game["gameType"], level=level,
                done=(game["gameType"], level) in done_levels))
    return TodayOut(patient_id=p.id, name=p.name, pathway_code=p.pathway_code, hand=p.side, today=today,
                    tasks=tasks, streak_days=0, week_done=0, last_message=None, reminder=None,
                    clinician_reviewed_at=None)


@router.get("/{patient_id}/progress", response_model=ProgressOut, operation_id="getProgress")
def get_progress(patient_id: str, db: Db):
    p = require_patient(db, patient_id)
    return ProgressOut(patient_id=p.id, points=[], personal_best_day=None, week_done=0, week_goal=5,
                       clinician_reviewed_at=None)
