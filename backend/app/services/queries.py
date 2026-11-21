"""Read-side helpers: table rows -> response models, patient state for the triage list."""
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.models import Alert, Checkin, GameSession, Pathway, Patient, TrendSnapshot
from app.models.schemas import AlertOut, PathwayOut
from app.services import alerts as alert_rules
from app.services import divergence


def pathway_out(p: Pathway) -> PathwayOut:
    return PathwayOut.model_validate({
        "code": p.code, "name": p.name, "frequency": p.frequency, "games": p.games,
        "questions": p.questions,
    })


def alert_out(db: Session, a: Alert) -> AlertOut:
    patient = db.get(Patient, a.patient_id)
    return AlertOut.model_validate({**a.model_dump(), "patient_name": patient.name if patient else ""})


def open_alert(db: Session, patient_id: str) -> Optional[Alert]:
    return db.exec(select(Alert).where(Alert.patient_id == patient_id, Alert.status != "closed")
                   .order_by(Alert.id.desc())).first()


# ---------------------------------------------------------------- patient state

BASELINE_NEEDED = 4  # practice session + baseline sessions (see trend.py)
IMPROVING_REASON = "Rezultati so nad izhodiščem."
STABLE_REASON = "Brez posebnosti; rezultati so blizu izhodišča."
DECLINING_HANDLED_REASON = "Rezultati so pod izhodiščem; opozorila trenutno ni odprtega."
URGENCY = {"red": 0, "yellow": 1, "no_data": 2, "insufficient_data": 3, "stable": 4}


@dataclass
class PatientState:
    status: str
    reason: str
    diverging: bool
    alert: Optional[Alert]
    last_entry_day: Optional[date]
    last_session_day: Optional[date]
    last_checkin_day: Optional[date]
    n_sessions: int
    n_checkins: int
    entry_days: set
    combined_delta: Optional[float]
    combined_direction: str


def entry_days(db: Session, patient_id: str) -> tuple[set, set, int, int]:
    """(session days, check-in days, n sessions, n check-ins): one query per table."""
    s_rows = db.exec(select(GameSession.day).where(GameSession.patient_id == patient_id)).all()
    c_rows = db.exec(select(Checkin.day).where(Checkin.patient_id == patient_id)).all()
    return set(s_rows), set(c_rows), len(s_rows), len(c_rows)


def combined_snapshots(db: Session, patient_id: str) -> list[TrendSnapshot]:
    return list(db.exec(select(TrendSnapshot).where(
        TrendSnapshot.patient_id == patient_id, TrendSnapshot.metric == "trace:all",
        TrendSnapshot.delta != None).order_by(TrendSnapshot.day)).all())  # noqa: E711


def patient_state(db: Session, p: Patient, today: date) -> PatientState:
    alert = open_alert(db, p.id)
    s_days, c_days, n_s, n_c = entry_days(db, p.id)
    all_days = s_days | c_days
    last = max(all_days) if all_days else None
    snaps = combined_snapshots(db, p.id)
    latest = snaps[-1] if snaps else None
    delta = latest.delta if latest else None
    direction = latest.direction if latest else "insufficient_data"

    if alert is not None and alert.severity in ("red", "yellow", "grey"):
        status = "no_data" if alert.severity == "grey" else alert.severity
        reason = alert.reason
        if alert.severity == "grey":  # the stored sentence is frozen at opening; count up to today
            reason = f"Brez vnosa že {(today - (last or p.discharge_date)).days} dni."
        diverging = alert.diverging
    else:
        diverging = divergence.assess(db, p.id, today)[0]
        silent = (today - (last or p.discharge_date)).days
        if silent >= alert_rules.GREY_AFTER_MISSED_DAYS:
            status, reason = "no_data", f"Brez vnosa že {silent} dni."
        elif latest is None:
            scored = db.exec(select(GameSession.game_type, GameSession.level).where(
                GameSession.patient_id == p.id, GameSession.completed == True,  # noqa: E712
                GameSession.counts_for_trend == True)).all()  # noqa: E712
            per_level = Counter(tuple(r) for r in scored)  # the baseline is per level
            n = min(max(per_level.values(), default=0), BASELINE_NEEDED - 1)
            status = "insufficient_data"
            reason = f"Premalo sej za izhodišče ({n} od {BASELINE_NEEDED})."
        elif direction == "improving":
            status, reason = "stable", IMPROVING_REASON
        elif direction == "declining":
            # no open alert although the trend is below baseline: a clinician already handled it
            status, reason = "stable", DECLINING_HANDLED_REASON
        else:
            status, reason = "stable", STABLE_REASON
    return PatientState(status, reason, diverging, alert, last, max(s_days, default=None),
                        max(c_days, default=None), n_s, n_c, all_days, delta, direction)


SPARK_POINTS = 21  # the last N days that have a value


def game_sparkline(db: Session, patient_id: str, today: date, n: int = SPARK_POINTS) -> list[tuple[date, float]]:
    """Combined trend (trace:all delta) of the last n days that have one."""
    return [(s.day, s.delta) for s in combined_snapshots(db, patient_id) if s.day <= today][-n:]


def checkins_of(db: Session, patient_id: str, upto: Optional[date] = None) -> list[Checkin]:
    stmt = select(Checkin).where(Checkin.patient_id == patient_id)
    if upto is not None:
        stmt = stmt.where(Checkin.day <= upto)
    return list(db.exec(stmt.order_by(Checkin.day, Checkin.id)).all())


def wellbeing_sparkline(db: Session, patient_id: str, today: date,
                        n: int = SPARK_POINTS) -> list[tuple[date, Optional[float]]]:
    """The wellbeing rating of the last n days that have a check-in."""
    return [(c.day, c.answers.get("wellbeing")) for c in checkins_of(db, patient_id, today)][-n:]


def days_with_entry(all_days: set, today: date, n: int) -> int:
    return sum(1 for d in all_days if today - timedelta(days=n - 1) <= d <= today)


def latest_review(db: Session, patient_id: str) -> Optional[datetime]:
    rows = db.exec(select(Alert.acknowledged_at).where(
        Alert.patient_id == patient_id, Alert.acknowledged_at != None)).all()  # noqa: E711
    return max(rows, default=None)


def completed_levels(db: Session, patient_id: str, day: date) -> set[tuple[str, int]]:
    """(game_type, level) pairs with a COMPLETED session on `day`."""
    rows = db.exec(select(GameSession.game_type, GameSession.level).where(
        GameSession.patient_id == patient_id, GameSession.day == day,
        GameSession.completed == True)).all()  # noqa: E712
    return {(g, lv) for g, lv in rows}


def pathway_levels(pathway: Pathway) -> list[tuple[str, int]]:
    return [(g["gameType"], lv) for g in pathway.games for lv in g["levels"]]
