"""Divergence between the objective trend and the patient's own report (plan section 8).
This is the main innovation claim: either signal alone can look fine.

Shared by the write path (alert reason) and the read path (badge in the list). Shared
hot file: agents use it, they do not edit it.
"""
from datetime import date, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.models import Checkin, Pathway, Patient, TrendSnapshot

OBJECTIVE_DROP = 10.0  # combined trend this far below baseline = objectively worse
OBJECTIVE_OK = 5.0  # within this band = objectively stable
SUBJECTIVE_WORSE = -0.15  # change of the wellbeing index (0-1) that counts as worse
SUBJECTIVE_SAME = -0.05  # at or above this = same or better


def wellbeing(pathway: Pathway, checkin: Checkin) -> Optional[float]:
    """0-1, higher = the patient reports feeling better. Mean of the answered ratings
    (v8: wellbeing and pain), each normalised by its range."""
    vals = []
    for q in pathway.questions:
        if q["id"] not in checkin.answers:
            continue
        span = (q["max"] - q["min"]) or 1
        v = (checkin.answers[q["id"]] - q["min"]) / span
        vals.append(1.0 - v if q.get("higherIsWorse", True) else v)
    if not vals:
        return None
    return sum(vals) / len(vals)


def subjective_change(db: Session, patient_id: str, day: date) -> Optional[float]:
    """Mean wellbeing of the last 7 days minus the 7 days before. None if either week is empty."""
    patient = db.get(Patient, patient_id)
    pathway = db.get(Pathway, patient.pathway_code)
    rows = db.exec(select(Checkin).where(Checkin.patient_id == patient_id, Checkin.day <= day,
                                         Checkin.day > day - timedelta(days=14))).all()
    recent, before = [], []
    for c in rows:
        w = wellbeing(pathway, c)
        if w is not None:
            (recent if c.day > day - timedelta(days=7) else before).append(w)
    if not recent or not before:
        return None
    return sum(recent) / len(recent) - sum(before) / len(before)


def latest_combined_delta(db: Session, patient_id: str, day: date, game_type: str = "trace") -> Optional[float]:
    snap = db.exec(select(TrendSnapshot).where(
        TrendSnapshot.patient_id == patient_id, TrendSnapshot.metric == f"{game_type}:all",
        TrendSnapshot.day <= day).order_by(TrendSnapshot.day.desc())).first()
    return snap.delta if snap else None


GAMES = ("trace", "camera")  # same order as app.services.trend.GAMES (no import: hot file)
# "sledenja" when only tracing is concerned, otherwise the measurements in general
_DROP = {"trace": "Rezultati sledenja padajo, pacient pa poroča enako ali boljše počutje.",
         "any": "Rezultati meritev padajo, pacient pa poroča enako ali boljše počutje."}
_STABLE = {"trace": "Rezultati sledenja so stabilni, pacient pa poroča slabše počutje.",
           "any": "Rezultati meritev so stabilni, pacient pa poroča slabše počutje."}


def assess(db: Session, patient_id: str, day: date) -> tuple[bool, Optional[str]]:
    """(diverging, sentence in Slovenian or None).

    Objective side, over the games that have a combined trend (tracing, camera exercises):
    worse = ANY game at least OBJECTIVE_DROP below its baseline; stable = ALL of them within
    OBJECTIVE_OK. A patient without camera data is judged on tracing alone.
    """
    deltas = {g: latest_combined_delta(db, patient_id, day, g) for g in GAMES}
    deltas = {g: v for g, v in deltas.items() if v is not None}
    change = subjective_change(db, patient_id, day)
    if not deltas or change is None:
        return False, None
    dropping = [g for g, v in deltas.items() if v <= -OBJECTIVE_DROP]
    if dropping and change >= SUBJECTIVE_SAME:
        return True, _DROP["trace" if dropping == ["trace"] else "any"]
    if all(abs(v) < OBJECTIVE_OK for v in deltas.values()) and change <= SUBJECTIVE_WORSE:
        return True, _STABLE["trace" if list(deltas) == ["trace"] else "any"]
    return False, None
