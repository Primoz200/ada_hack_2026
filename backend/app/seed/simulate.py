"""Demo control "simulate the next N days": every patient continues their story; the
selected one switches to a slow decline of the game score with calm check-ins."""
from sqlmodel import Session

from app.models import Patient
from app.models.schemas import SimulateOut
from app.seed import stories as st
from app.seed import write_day
from app.services import alerts, clock

# patient id -> (first simulated day index k0, level-2 base score the decline starts from)
_DECLINING: dict[str, tuple[int, float]] = {}


def clear() -> None:
    """Called by reset_database."""
    _DECLINING.clear()


def declining() -> dict[str, tuple[int, float]]:
    return dict(_DECLINING)


def simulate(db: Session, patient_id: str, days: int) -> SimulateOut:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise KeyError(patient_id)
    story = st.BY_ID.get(patient_id)
    n_checkins = n_sessions = 0
    for i in range(days):
        clock.advance(1)
        today = clock.today()
        if i == 0 and story is not None and patient_id not in _DECLINING \
                and not story.declining and not story.silent \
                and alerts.open_alert(db, patient_id) is None:
            k0 = (today - patient.discharge_date).days
            _DECLINING[patient_id] = (k0, story.curve(k0 - 1))
        for s in st.STORIES:
            p = db.get(Patient, s.id)
            if p is None:
                continue
            k = (today - p.discharge_date).days
            c, n = write_day(db, s, k, today, _DECLINING.get(s.id))
            if s.id == patient_id:
                n_checkins += c
                n_sessions += n
        alerts.sweep(db, today)
    return SimulateOut(patient_id=patient_id, days_added=days, sessions_added=n_sessions,
                       checkins_added=n_checkins, today=clock.today())
