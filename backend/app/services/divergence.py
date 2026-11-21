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
CONCERN_PENALTY = {"none": 0.0, "little": 0.15, "call": 0.30}


def wellbeing(pathway: Pathway, checkin: Checkin) -> Optional[float]:
    """0-1, higher = the patient reports feeling better. Mean of the answered questions,
    each normalised by its range, minus a penalty for a reported concern."""
    vals = []
    for q in pathway.questions:
        if q["id"] not in checkin.answers:
            continue
        span = (q["max"] - q["min"]) or 1
        v = (checkin.answers[q["id"]] - q["min"]) / span
        vals.append(1.0 - v if q.get("higherIsWorse", True) else v)
    if not vals:
        return None
    return max(0.0, sum(vals) / len(vals) - CONCERN_PENALTY.get(checkin.concern, 0.0))


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


def assess(db: Session, patient_id: str, day: date) -> tuple[bool, Optional[str]]:
    """(diverging, sentence in Slovenian or None)."""
    delta = latest_combined_delta(db, patient_id, day)
    change = subjective_change(db, patient_id, day)
    if delta is None or change is None:
        return False, None
    if delta <= -OBJECTIVE_DROP and change >= SUBJECTIVE_SAME:
        return True, "Rezultati igre padajo, pacient pa poroča enako ali boljše počutje."
    if abs(delta) < OBJECTIVE_OK and change <= SUBJECTIVE_WORSE:
        return True, "Rezultati igre so stabilni, pacient pa poroča slabše počutje."
    return False, None
