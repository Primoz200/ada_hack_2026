"""Alert rules and the human-in-the-loop state machine (plan section 8).

STUB (Phase 0): agent A implements the bodies. Signatures are fixed.
All thresholds are parameters here.
"""
from datetime import date
from typing import Optional

from sqlmodel import Session

from app.models import Alert

YELLOW_DROP_POINTS = 10.0  # combined trend at least this far below baseline ...
YELLOW_DAYS_HIT = 2  # ... on this many ...
YELLOW_DAYS_WINDOW = 3  # ... of the last N days that have a session
PAIN_RISE_POINTS = 2.0  # pain week-over-week
REMINDER_AFTER_MISSED_DAYS = 2  # patient gets an automatic reminder
GREY_AFTER_MISSED_DAYS = 4  # clinician sees "brez podatkov"

OUTCOME_LABELS = {
    "called_reassured": "Poklical, pomiril",
    "adjusted_exercises": "Prilagodil vaje",
    "visit_moved_earlier": "Pregled prestavljen naprej",
    "urgent_referral": "Nujna napotitev",
    "unreachable": "Nedosegljiv",
    "false_alarm": "Lažni alarm ali težava s podatki",
}


class AlertError(ValueError):
    """Invalid transition, e.g. closing without an outcome."""


def evaluate_alerts(db: Session, patient_id: str, day: date) -> Optional[Alert]:
    """Run all rules for the patient as of `day`; open an alert, attach a trigger to the
    open one, or escalate. Returns the patient's open alert (or None)."""
    return None


def sweep(db: Session, day: date) -> None:
    """Time-driven rules for ALL patients (missing entries -> grey). Called by the triage
    list endpoint and by the seed, because no submission triggers them."""
    return None


def acknowledge(db: Session, alert_id: int, clinician_id: str, close: bool,
                outcome: Optional[str], note: Optional[str]) -> Alert:
    """new -> acknowledged (who, when) -> closed with an outcome. Closing without an
    outcome raises AlertError."""
    raise NotImplementedError
