"""Patient registry, triage, detail, and timeline endpoints."""

from datetime import UTC, date, timedelta
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import column
from sqlmodel import Session, select

from app.db import get_session
from app.models.api import (
    AlertOut,
    CheckinOut,
    PathwayOut,
    PatientDetail,
    PatientHomeOut,
    PatientHomeStep,
    PatientListItem,
    PatientListOut,
    PatientProgressOut,
    PatientRatingPoint,
    PatientSummary,
    SelfcheckSummaryOut,
    SessionSummary,
    SparkPoint,
    TimelineOut,
    TrendPoint,
    TriageCounters,
)
from app.models.tables import Alert, Checkin, GameSession, Pathway, Patient, TrendSnapshot
from app.services.alerts import divergence, sweep_missing_data_alerts
from app.services.clock import today
from app.services.feedback import feedback_points, patient_feedback

router = APIRouter(prefix="/api/patients", tags=["patients"])
NO_DATA_DAYS = 4
TRIAGE_ORDER = {"red": 0, "yellow": 1, "no_data": 2, "insufficient_data": 3, "stable": 4}
WEEK_GOAL = 5
RECENT_PROGRESS_DAYS = 7
SELF_CHECK_POINTS_DAYS = 14
TRACE_LEVEL_TITLES = {1: "Ravna črta", 2: "Krog", 3: "Labirint"}


def _open_alert(session: Session, patient_id: str) -> Alert | None:
    return session.exec(
        select(Alert)
        .where(
            column("patient_id") == patient_id,
            column("status").in_(["new", "acknowledged"]),
        )
        .order_by(column("updated_at").desc(), column("id").desc())
    ).first()


def _last_activity_day(session: Session, patient: Patient) -> date:
    last_checkin = session.exec(
        select(Checkin)
        .where(column("patient_id") == patient.id)
        .order_by(column("day").desc(), column("id").desc())
    ).first()
    last_session = session.exec(
        select(GameSession)
        .where(column("patient_id") == patient.id)
        .order_by(column("day").desc(), column("id").desc())
    ).first()
    return max(
        patient.discharge_date,
        last_checkin.day if last_checkin is not None else patient.discharge_date,
        last_session.day if last_session is not None else patient.discharge_date,
    )


def _latest_trace_snapshot(session: Session, patient_id: str) -> TrendSnapshot | None:
    return session.exec(
        select(TrendSnapshot)
        .where(
            column("patient_id") == patient_id,
            column("metric") == "trace:all",
        )
        .order_by(column("day").desc(), column("id").desc())
    ).first()


def _insufficient_sessions(session: Session, patient_id: str) -> int:
    rows = session.exec(
        select(GameSession).where(
            column("patient_id") == patient_id,
            column("game_type") == "trace",
            column("completed").is_(True),
            column("counts_for_trend").is_(True),
            column("score").is_not(None),
        )
    ).all()
    by_level: dict[int, int] = {}
    for row in rows:
        by_level[row.level] = by_level.get(row.level, 0) + 1
    return min(3, max(by_level.values(), default=0))


def _triage(
    session: Session, patient: Patient, as_of: date
) -> tuple[str, str, bool, Alert | None, TrendSnapshot | None]:
    alert = _open_alert(session, patient.id)
    latest = _latest_trace_snapshot(session, patient.id)
    diverging_now, _ = divergence(session, patient.id, as_of)
    if alert is not None:
        if alert.severity == "grey":
            missed_days = max(0, (as_of - _last_activity_day(session, patient)).days)
            return (
                "no_data",
                f"Brez vnosa že {missed_days} dni.",
                alert.diverging,
                alert,
                latest,
            )
        return alert.severity, alert.reason, alert.diverging, alert, latest

    missed_days = max(0, (as_of - _last_activity_day(session, patient)).days)
    if missed_days >= NO_DATA_DAYS:
        return "no_data", f"Brez vnosa že {missed_days} dni.", diverging_now, None, latest
    if latest is None or latest.delta is None:
        count = _insufficient_sessions(session, patient.id)
        return (
            "insufficient_data",
            f"Premalo sej za izhodišče ({count} od 4).",
            diverging_now,
            None,
            latest,
        )
    if latest.direction == "improving":
        reason = "Rezultati so nad izhodiščem."
    elif latest.direction == "declining":
        reason = "Rezultati so nekoliko pod izhodiščem."
    else:
        reason = "Brez posebnosti; rezultati so blizu izhodišča."
    return "stable", reason, diverging_now, None, latest


def _sparkline_data(session: Session, patient_id: str) -> tuple[list[SparkPoint], list[SparkPoint]]:
    game_rows = session.exec(
        select(TrendSnapshot)
        .where(
            column("patient_id") == patient_id,
            column("metric") == "trace:all",
            column("delta").is_not(None),
        )
        .order_by(column("day").desc(), column("id").desc())
        .limit(21)
    ).all()
    checkins = session.exec(
        select(Checkin)
        .where(column("patient_id") == patient_id)
        .order_by(column("day").desc(), column("id").desc())
        .limit(21)
    ).all()
    game = [SparkPoint(day=row.day, value=row.delta) for row in reversed(game_rows)]
    wellbeing = [
        SparkPoint(day=row.day, value=row.answers.get("wellbeing")) for row in reversed(checkins)
    ]
    return game, wellbeing


def _patient_list_item(
    session: Session, patient: Patient, pathway_name: str, as_of: date
) -> PatientListItem:
    status, reason, diverging_now, alert, _ = _triage(session, patient, as_of)
    game_sparkline, wellbeing_sparkline = _sparkline_data(session, patient.id)
    return PatientListItem(
        id=patient.id,
        name=patient.name,
        pathway_code=patient.pathway_code,
        pathway_name=pathway_name,
        side=cast(Literal["left", "right"], patient.side),
        days_since_discharge=(as_of - patient.discharge_date).days,
        status=cast(Literal["red", "yellow", "no_data", "stable", "insufficient_data"], status),
        reason=reason,
        diverging=diverging_now,
        game_sparkline=game_sparkline,
        wellbeing_sparkline=wellbeing_sparkline,
        days_to_next_visit=(patient.next_visit_date - as_of).days
        if patient.next_visit_date is not None
        else None,
        open_alert_id=alert.id if alert is not None else None,
        is_demo=patient.is_demo,
    )


def _alert_sort_key(alert: Alert | None) -> tuple[int, float]:
    if alert is None:
        return 1, 0.0
    updated = alert.updated_at
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=UTC)
    return 0, -updated.timestamp()


@router.get("", response_model=PatientListOut, operation_id="listPatients")
def list_patients(session: Annotated[Session, Depends(get_session)]) -> PatientListOut:
    """Run the missing-data sweep and return the urgency-sorted patient registry."""
    as_of = today()
    sweep_missing_data_alerts(session, as_of)
    patients = session.exec(select(Patient).order_by(column("sort_order"), column("id"))).all()
    pathways = {row.code: row for row in session.exec(select(Pathway)).all()}
    entries: list[tuple[PatientListItem, Alert | None, int]] = []
    for patient in patients:
        pathway = pathways.get(patient.pathway_code)
        item = _patient_list_item(
            session, patient, pathway.name if pathway is not None else patient.pathway_code, as_of
        )
        entries.append((item, _open_alert(session, patient.id), patient.sort_order))
    entries.sort(
        key=lambda entry: (
            TRIAGE_ORDER[entry[0].status],
            *_alert_sort_key(entry[1]),
            entry[2],
            entry[0].id,
        )
    )
    items = [entry[0] for entry in entries]
    return PatientListOut(
        today=as_of,
        counters=TriageCounters(
            needs_attention=sum(item.status in {"red", "yellow"} for item in items),
            no_data=sum(item.status == "no_data" for item in items),
            stable=sum(item.status in {"stable", "insufficient_data"} for item in items),
            total=len(items),
        ),
        patients=items,
    )


def _require_patient(session: Session, patient_id: str) -> Patient:
    patient = session.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Pacient ne obstaja")
    return patient


def _patient_game_steps(
    session: Session, patient_id: str, pathway: Pathway, as_of: date
) -> list[PatientHomeStep]:
    completed = session.exec(
        select(GameSession.game_type, GameSession.level).where(
            column("patient_id") == patient_id,
            column("day") == as_of,
            column("completed").is_(True),
        )
    ).all()
    completed_pairs = set(completed)
    steps: list[PatientHomeStep] = []
    for game in pathway.games:
        game_type = str(game.get("gameType", ""))
        for raw_level in game.get("levels", []):
            level = int(raw_level)
            steps.append(
                PatientHomeStep(
                    id=f"{game_type}:{level}",
                    kind="game",
                    title=TRACE_LEVEL_TITLES.get(level, f"Stopnja {level}")
                    if game_type == "trace"
                    else f"Stopnja {level}",
                    game_type=game_type,
                    level=level,
                    done=(game_type, level) in completed_pairs,
                )
            )
    return steps


def _home_steps(
    session: Session, patient: Patient, pathway: Pathway, as_of: date
) -> list[PatientHomeStep]:
    checkin_today = (
        session.exec(
            select(Checkin.id).where(
                column("patient_id") == patient.id,
                column("day") == as_of,
            )
        ).first()
        is not None
    )
    return [
        PatientHomeStep(
            id="ratings",
            kind="ratings",
            title="Počutje in bolečina",
            game_type=None,
            level=None,
            done=checkin_today,
        ),
        *_patient_game_steps(session, patient.id, pathway, as_of),
    ]


def _last_entry_day(session: Session, patient_id: str, as_of: date) -> date | None:
    checkin = session.exec(
        select(Checkin)
        .where(column("patient_id") == patient_id, column("day") <= as_of)
        .order_by(column("day").desc())
    ).first()
    game = session.exec(
        select(GameSession)
        .where(column("patient_id") == patient_id, column("day") <= as_of)
        .order_by(column("day").desc())
    ).first()
    activity_days = [row.day for row in (checkin, game) if row is not None]
    return max(activity_days) if activity_days else None


@router.get("/{patient_id}/home", response_model=PatientHomeOut, operation_id="getPatientHome")
def get_patient_home(
    patient_id: str, session: Annotated[Session, Depends(get_session)]
) -> PatientHomeOut:
    """Return the patient-facing daily checklist."""
    patient = _require_patient(session, patient_id)
    pathway = session.get(Pathway, patient.pathway_code)
    if pathway is None:
        raise RuntimeError(f"Pathway {patient.pathway_code!r} missing for patient {patient_id!r}")
    as_of = today()
    steps = _home_steps(session, patient, pathway, as_of)
    return PatientHomeOut(
        patient_id=patient.id,
        name=patient.name,
        pathway_code=pathway.code,
        pathway_name=pathway.name,
        hand=cast(Literal["left", "right"], patient.side),
        today=as_of,
        steps=steps,
        selfcheck_done_today=all(step.done for step in steps),
        last_selfcheck_day=_last_entry_day(session, patient.id, as_of),
    )


def _selfcheck_summary(
    session: Session, patient_id: str, as_of: date, pathway: Pathway
) -> SelfcheckSummaryOut:
    steps = _patient_game_steps(session, patient_id, pathway, as_of)
    done_today = sum(step.done for step in steps)
    total_steps = sum(len(game.get("levels", [])) for game in pathway.games)
    feedback = patient_feedback(session, patient_id, as_of)
    return SelfcheckSummaryOut(
        tone=feedback.tone,
        trend=feedback.trend,
        title=feedback.title,
        text=feedback.text,
        patient_id=patient_id,
        day=as_of,
        levels_done=done_today,
        levels_total=total_steps,
        points=feedback_points(session, patient_id, as_of, since=as_of - timedelta(days=13)),
    )


@router.get(
    "/{patient_id}/selfcheck/summary",
    response_model=SelfcheckSummaryOut,
    operation_id="getSelfcheckSummary",
)
def get_selfcheck_summary(
    patient_id: str, session: Annotated[Session, Depends(get_session)]
) -> SelfcheckSummaryOut:
    """Return today's feedback and self-check completion summary."""
    patient = _require_patient(session, patient_id)
    pathway = session.get(Pathway, patient.pathway_code)
    if pathway is None:
        raise RuntimeError(f"Pathway {patient.pathway_code!r} missing for patient {patient_id!r}")
    return _selfcheck_summary(session, patient_id, today(), pathway)


@router.get(
    "/{patient_id}/progress", response_model=PatientProgressOut, operation_id="getPatientProgress"
)
def get_patient_progress(
    patient_id: str, session: Annotated[Session, Depends(get_session)]
) -> PatientProgressOut:
    """Return the patient's all-time game and rating progress."""
    _require_patient(session, patient_id)
    as_of = today()
    snapshots = feedback_points(session, patient_id, as_of)
    ratings = session.exec(
        select(Checkin)
        .where(column("patient_id") == patient_id, column("day") <= as_of)
        .order_by(column("day"), column("id"))
    ).all()
    recent_start = as_of - timedelta(days=RECENT_PROGRESS_DAYS - 1)
    checkin_days = session.exec(
        select(Checkin).where(
            column("patient_id") == patient_id,
            column("day") >= recent_start,
            column("day") <= as_of,
        )
    ).all()
    session_days = session.exec(
        select(GameSession).where(
            column("patient_id") == patient_id,
            column("day") >= recent_start,
            column("day") <= as_of,
        )
    ).all()
    acknowledged = session.exec(
        select(Alert)
        .where(column("patient_id") == patient_id, column("acknowledged_at").is_not(None))
        .order_by(column("acknowledged_at").desc())
    ).first()
    best_snapshot = session.exec(
        select(TrendSnapshot)
        .where(
            column("patient_id") == patient_id,
            column("metric") == "trace:all",
            column("day") <= as_of,
            column("delta").is_not(None),
        )
        .order_by(column("delta").desc(), column("day").desc(), column("id").desc())
    ).first()
    feedback = patient_feedback(session, patient_id, as_of)
    return PatientProgressOut(
        tone=feedback.tone,
        trend=feedback.trend,
        title=feedback.title,
        text=feedback.text,
        patient_id=patient_id,
        points=snapshots,
        ratings=[
            PatientRatingPoint(
                day=row.day,
                wellbeing=row.answers.get("wellbeing"),
                pain=row.answers.get("pain"),
            )
            for row in ratings
        ],
        personal_best_day=best_snapshot.day if best_snapshot is not None else None,
        week_done=len({row.day for row in checkin_days} | {row.day for row in session_days}),
        week_goal=WEEK_GOAL,
        clinician_reviewed_at=acknowledged.acknowledged_at if acknowledged is not None else None,
    )


@router.get("/{patient_id}", response_model=PatientDetail, operation_id="getPatient")
def get_patient(
    patient_id: str, session: Annotated[Session, Depends(get_session)]
) -> PatientDetail:
    """Return patient demographics, triage state, and activity summary."""
    patient = _require_patient(session, patient_id)
    as_of = today()
    sweep_missing_data_alerts(session, as_of)
    status, reason, diverging_now, alert, snapshot = _triage(session, patient, as_of)
    pathway = session.get(Pathway, patient.pathway_code)
    if pathway is None:
        raise RuntimeError(f"Pathway {patient.pathway_code!r} missing for patient {patient_id!r}")
    sessions = session.exec(select(GameSession).where(column("patient_id") == patient_id)).all()
    checkins = session.exec(select(Checkin).where(column("patient_id") == patient_id)).all()
    latest_session_day = max((row.day for row in sessions), default=None)
    latest_checkin_day = max((row.day for row in checkins), default=None)
    return PatientDetail(
        id=patient.id,
        name=patient.name,
        birth_year=patient.birth_year,
        pathway=PathwayOut.model_validate(pathway),
        side=cast(Literal["left", "right"], patient.side),
        discharge_date=patient.discharge_date,
        next_visit_date=patient.next_visit_date,
        days_since_discharge=(as_of - patient.discharge_date).days,
        days_to_next_visit=(patient.next_visit_date - as_of).days
        if patient.next_visit_date is not None
        else None,
        status=cast(Literal["red", "yellow", "no_data", "stable", "insufficient_data"], status),
        reason=reason,
        diverging=diverging_now,
        open_alert=AlertOut.model_validate(alert) if alert is not None else None,
        summary=PatientSummary(
            n_sessions=len(sessions),
            n_checkins=len(checkins),
            last_session_day=latest_session_day,
            last_checkin_day=latest_checkin_day,
            combined_delta=snapshot.delta if snapshot is not None else None,
            combined_direction=(
                cast(
                    Literal["improving", "stable", "declining", "insufficient_data"],
                    snapshot.direction,
                )
                if snapshot is not None
                else "insufficient_data"
            ),
        ),
        is_demo=patient.is_demo,
    )


@router.get("/{patient_id}/timeline", response_model=TimelineOut, operation_id="getTimeline")
def get_timeline(patient_id: str, session: Annotated[Session, Depends(get_session)]) -> TimelineOut:
    """Return all non-raw activity and alerts for a patient's timeline."""
    patient = _require_patient(session, patient_id)
    sessions = session.exec(
        select(GameSession)
        .where(column("patient_id") == patient_id)
        .order_by(column("started_at"), column("id"))
    ).all()
    checkins = session.exec(
        select(Checkin)
        .where(column("patient_id") == patient_id)
        .order_by(column("day"), column("id"))
    ).all()
    trends = session.exec(
        select(TrendSnapshot)
        .where(column("patient_id") == patient_id)
        .order_by(column("day"), column("id"))
    ).all()
    alerts = session.exec(
        select(Alert).where(column("patient_id") == patient_id).order_by(column("id"))
    ).all()
    return TimelineOut(
        patient_id=patient_id,
        today=today(),
        discharge_date=patient.discharge_date,
        next_visit_date=patient.next_visit_date,
        sessions=[SessionSummary.model_validate(row) for row in sessions],
        checkins=[CheckinOut.model_validate(row) for row in checkins],
        trends=[
            TrendPoint(
                metric=row.metric,
                day=row.day,
                n_sessions=row.sessions,
                baseline=row.baseline,
                ewma=row.ewma,
                delta=row.delta,
                delta_pct=row.delta_percent,
                direction=row.direction,
            )
            for row in trends
        ],
        alerts=[AlertOut.model_validate(row) for row in alerts],
    )
