"""Read path for patients: triage list, detail, timeline and the patient's own screens."""
from datetime import timedelta

from fastapi import APIRouter
from sqlmodel import select

from app.deps import Db, require_patient
from app.models import Alert, Checkin, GameSession, Pathway, Patient, TrendSnapshot
from app.models.schemas import (
    CheckinOut, GameProgress, PatientDetail, PatientHomeOut, PatientListItem, PatientListOut, PatientSummary,
    ProgressOut, ProgressPoint, RatingPoint, SelfcheckStep, SelfcheckSummary, SessionSummary, SparkPoint,
    TimelineOut, TrendPoint, TriageCounters,
)
from app.seed.pathways import GAME_TITLES, LEVEL_TITLES
from app.services import alerts, clock, feedback, queries, scoring

RATINGS_TITLE = "Počutje in bolečina"
SUMMARY_DAYS = 14
POINT_BAND = 5.0  # combined trend beyond +-this many points is labelled better / lower
WEEK_GOAL = 5

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
            game_sparkline=[SparkPoint(day=d, value=v) for d, v in queries.game_sparkline(db, p.id, today)],
            camera_sparkline=[SparkPoint(day=d, value=v)
                              for d, v in queries.game_sparkline(db, p.id, today, game="camera")],
            wellbeing_sparkline=[SparkPoint(day=d, value=v)
                                 for d, v in queries.wellbeing_sparkline(db, p.id, today)],
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
    return TimelineOut(
        patient_id=p.id, today=clock.today(), discharge_date=p.discharge_date,
        next_visit_date=p.next_visit_date,
        sessions=[SessionSummary.model_validate(s) for s in sessions],
        checkins=[CheckinOut.model_validate(c) for c in checkins],
        trends=[TrendPoint.model_validate(t) for t in trends],
        alerts=[queries.alert_out(db, a) for a in alerts])


def _label(delta: float) -> str:
    return "lower" if delta <= -POINT_BAND else "better" if delta >= POINT_BAND else "usual"


def _points(snaps) -> list[ProgressPoint]:
    return [ProgressPoint(day=s.day, value=round(s.delta, 1), label=_label(s.delta)) for s in snaps]


def _games(db, p: Patient, today, since=None) -> list[GameProgress]:
    """Each game's own trend for the patient, tracing first; only games with trend points.
    since: first day of the points shown (the personal best is over the whole history)."""
    per_game = feedback.points_by_game(db, p.id, today)
    trends = feedback.game_trends(db, p.id, today, per_game)
    out = []
    for game, snaps in per_game.items():
        best = max(snaps, key=lambda s: (s.delta, s.day))
        shown = [s for s in snaps if since is None or s.day >= since]
        out.append(GameProgress(game_type=game, title=GAME_TITLES.get(game, game), trend=trends[game],
                                points=_points(shown), personal_best_day=best.day))
    return out


def _steps(db, p: Patient, today) -> list[SelfcheckStep]:
    pathway = db.get(Pathway, p.pathway_code)
    has_checkin = db.exec(select(Checkin.id).where(Checkin.patient_id == p.id,
                                                   Checkin.day == today)).first() is not None
    steps = [SelfcheckStep(id="ratings", kind="ratings", title=RATINGS_TITLE, done=has_checkin)]
    done = queries.completed_levels(db, p.id, today)
    for game_type, level, skippable in queries.pathway_levels(pathway):
        steps.append(SelfcheckStep(
            id=f"{game_type}:{level}", kind="game", game_type=game_type, level=level,
            title=LEVEL_TITLES.get((game_type, level), f"Stopnja {level}"),
            done=(game_type, level) in done, skippable=skippable,
            duration_s=scoring.camera_duration_s(level) if game_type == "camera" else None))
    return steps


def _selfcheck_done(steps: list[SelfcheckStep]) -> bool:
    """Ratings and every tracing level; camera steps never block completion (no camera, no
    permission and skipped exercises are all fine)."""
    return all(s.done for s in steps if s.game_type != "camera")


@router.get("/{patient_id}/home", response_model=PatientHomeOut, operation_id="getPatientHome")
def get_home(patient_id: str, db: Db):
    """Patient landing page: name and today's self-check steps."""
    p = require_patient(db, patient_id)
    today = clock.today()
    s_days, c_days, _, _ = queries.entry_days(db, p.id)
    days = {d for d in s_days | c_days if d <= today}
    steps = _steps(db, p, today)
    return PatientHomeOut(
        patient_id=p.id, name=p.name, pathway_code=p.pathway_code,
        pathway_name=db.get(Pathway, p.pathway_code).name, hand=p.side, today=today, steps=steps,
        selfcheck_done_today=_selfcheck_done(steps), last_selfcheck_day=max(days, default=None))


@router.get("/{patient_id}/selfcheck/summary", response_model=SelfcheckSummary,
            operation_id="getSelfcheckSummary")
def get_selfcheck_summary(patient_id: str, db: Db):
    """How today's self-check went compared with previous days (shown at the end)."""
    p = require_patient(db, patient_id)
    today = clock.today()
    fb = feedback.feedback_for(db, p.id, today)
    game_steps = [s for s in _steps(db, p, today) if s.kind == "game"]
    since = today - timedelta(days=SUMMARY_DAYS - 1)
    return SelfcheckSummary(
        tone=fb.tone, trend=fb.trend, title=fb.title, text=fb.text, patient_id=p.id, day=today,
        levels_done=sum(1 for s in game_steps if s.done), levels_total=len(game_steps),
        games=_games(db, p, today, since))


@router.get("/{patient_id}/progress", response_model=ProgressOut, operation_id="getProgress")
def get_progress(patient_id: str, db: Db):
    """"Moj napredek": a very simple dashboard."""
    p = require_patient(db, patient_id)
    today = clock.today()
    fb = feedback.feedback_for(db, p.id, today)
    s_days, c_days, _, _ = queries.entry_days(db, p.id)
    ratings = [RatingPoint(day=c.day, wellbeing=c.answers.get("wellbeing"), pain=c.answers.get("pain"))
               for c in queries.checkins_of(db, p.id, today)]
    return ProgressOut(
        tone=fb.tone, trend=fb.trend, title=fb.title, text=fb.text, patient_id=p.id,
        games=_games(db, p, today), ratings=ratings,
        week_done=queries.days_with_entry(s_days | c_days, today, 7), week_goal=WEEK_GOAL,
        clinician_reviewed_at=queries.latest_review(db, p.id))
