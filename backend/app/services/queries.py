"""Read-side helpers: table rows -> response models. Phase 0 has minimal versions;
agent B completes status / reason / sparkline / streak logic.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.models import Alert, Checkin, GameSession, Pathway, Patient, TrendSnapshot
from app.models.schemas import AlertOut, PathwayOut
from app.seed.pathways import WARNING_PROMPTS
from app.services import alerts as alert_rules
from app.services import divergence


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
            scored = db.exec(select(GameSession.id).where(
                GameSession.patient_id == p.id, GameSession.completed == True,  # noqa: E712
                GameSession.counts_for_trend == True)).all()  # noqa: E712
            n = min(len(scored), BASELINE_NEEDED - 1)
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


def sparkline(db: Session, patient_id: str, today: date, days: int = 14) -> list[tuple[date, float]]:
    since = today - timedelta(days=days - 1)
    return [(s.day, s.delta) for s in combined_snapshots(db, patient_id) if since <= s.day <= today]


def days_with_entry(all_days: set, today: date, n: int) -> int:
    return sum(1 for d in all_days if today - timedelta(days=n - 1) <= d <= today)


def streak(all_days: set, today: date) -> int:
    """Consecutive days with any entry, counted back from today (or yesterday if today is empty)."""
    d = today if today in all_days else today - timedelta(days=1)
    n = 0
    while d in all_days:
        n += 1
        d -= timedelta(days=1)
    return n


def latest_review(db: Session, patient_id: str) -> Optional[datetime]:
    rows = db.exec(select(Alert.acknowledged_at).where(
        Alert.patient_id == patient_id, Alert.acknowledged_at != None)).all()  # noqa: E711
    return max(rows, default=None)


def days_with_checkin(db: Session, patient_id: str, today: date, n: int = 7) -> int:
    days = db.exec(select(Checkin.day).where(Checkin.patient_id == patient_id,
                                             Checkin.day > today - timedelta(days=n),
                                             Checkin.day <= today)).all()
    return len(set(days))
