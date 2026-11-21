"""Test helpers: build histories through the real write path."""
from datetime import date, timedelta

from sqlmodel import select

from app.models import Alert, Patient
from app.models.schemas import CheckinIn, ClientMeta, SessionIn
from app.services import clock, ingest
from app.services.scoring import STANDIN_VERSION, score_to_class
from app.services.types import ScoreResult

D0 = date(2026, 9, 1)
META = ClientMeta(input_device="touch", canvasW=360, canvasH=360, device_pixel_ratio=2, user_agent="t")


def d(n: int) -> date:
    return D0 + timedelta(days=n)


def add_patient(db, pid="p", pathway="stroke", discharge=None):
    db.add(Patient(id=pid, name="Test Pacient", birth_year=1950, pathway_code=pathway, side="right",
                   discharge_date=discharge or d(-60)))
    db.commit()


def play(db, pid, day, score, level=1, completed=True, hour=9):
    """One session through ingest_session (preset score). Returns the stored row."""
    data = SessionIn(patient_id=pid, game_type="trace", level=level, hand="right",
                     started_at=clock.at(day, hour, level), duration_ms=9000, completed=completed,
                     series={"targetX": [0.1, 0.9], "targetY": [0.5, 0.5], "t": [0, 1], "x": [0.1, 0.9],
                             "y": [0.5, 0.5], "strokeId": [0, 0]}, client_meta=META)
    preset = ScoreResult({}, float(score), score_to_class(score), STANDIN_VERSION)
    return ingest.ingest_session(db, data, day=day, created_at=clock.at(day, hour, level),
                                 preset_score=preset)


def play_round(db, pid, day, score):
    """All three levels on one day (level offsets keep each level's own baseline apart)."""
    return [play(db, pid, day, score + off, level=lv) for lv, off in ((1, 5), (2, 0), (3, -5))]


def checkin(db, pid, day, wellbeing=7, pain=2):
    data = CheckinIn(patient_id=pid, wellbeing=wellbeing, pain=pain)
    return ingest.ingest_checkin(db, data, day=day, created_at=clock.at(day, 8))


def all_alerts(db, pid="p"):
    return db.exec(select(Alert).where(Alert.patient_id == pid).order_by(Alert.id)).all()


def open_alerts(db, pid="p"):
    return [a for a in all_alerts(db, pid) if a.status != "closed"]


def baseline_days(db, pid="p", score=70, start=0):
    """Practice + 3 baseline sessions (days start .. start+3), level 1 only. Returns next day index."""
    for i in range(4):
        play(db, pid, d(start + i), score)
    return start + 4
