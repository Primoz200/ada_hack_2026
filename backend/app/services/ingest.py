"""The single write path. The API, the seed and admin simulate all go through these
two functions, so charts, scores and alerts always agree.

Store + score, trend, alerts, patient feedback wording.
"""
from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models import Checkin, GameSession, Pathway, Patient, SessionRaw
from app.models.schemas import CheckinIn, SessionIn
from app.services import alerts, clock, scoring, trend
from app.services.types import Feedback, ScoreResult

BETTER_BAND = 5.0  # points above / below the level baseline that count as better / lower
RETRY_DROP = 10.0  # a single score this far below the level EWMA offers a repeat

THANKS = Feedback("thanks", "Hvala!", "Poslano vašemu zdravniku.")
NEUTRAL = Feedback("neutral", "Hvala za vnos",
                   "Rezultati so ta teden nekoliko drugačni. Vaš zdravnik jih vidi.")
CALL_112 = Feedback(
    "call_112", "Takoj pokličite 112",
    "Znak, ki ste ga označili, je lahko znak možganske kapi. Takoj pokličite 112 in povejte, "
    "da gre za sum na kap. Ne čakajte na odgovor ambulante.")
CALL_CLINIC = Feedback(
    "call_clinic", "Še danes pokličite ambulanto",
    "Zaradi znaka, ki ste ga označili, še danes pokličite ambulanto. Vaš zdravnik je obveščen. "
    "Če se počutite zelo slabo, pokličite 112.")

COMPARED_TEXT = {
    "first": "Vaši prvi rezultati nam pomagajo spoznati, kaj je za vas običajno.",
    "better": "Danes je šlo bolje kot običajno.",
    "similar": "Danes je šlo podobno kot običajno.",
    "lower": "Danes je šlo malo težje kot običajno.",
    "not_scored": "Prekinjena vaja se ne šteje. Jutri poskusite znova.",
}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _warning_feedback(db: Session, patient_id: str, signs: list[str]) -> Optional[Feedback]:
    """call_112 beats call_clinic; a sign unknown to the pathway is treated as call_clinic."""
    if not signs:
        return None
    patient = db.get(Patient, patient_id)
    pathway = db.get(Pathway, patient.pathway_code) if patient else None
    actions = {w["id"]: w["action"] for w in (pathway.warning_signs if pathway else [])}
    if any(actions.get(s) == "call_112" for s in signs):
        return CALL_112
    return CALL_CLINIC


def _alarming(alert) -> bool:
    return alert is not None and alert.severity in ("yellow", "red")


def ingest_session(db: Session, data: SessionIn, *, day: Optional[date] = None,
                   created_at: Optional[datetime] = None,
                   preset_score: Optional[ScoreResult] = None
                   ) -> tuple[GameSession, Feedback, dict]:
    """Store raw data, score, recompute trends, evaluate alerts.

    day / created_at: override "today" (seed replay). preset_score: the seed passes a
    score from its story curve instead of scoring the trace.
    Returns (session row, patient feedback, extras) where extras has
    compared_to_usual, offer_retry, personal_best.
    """
    day = day or clock.today()
    meta = data.client_meta.model_dump(by_alias=True)
    scored = data.completed
    result = None
    if scored:
        result = preset_score or scoring.score_session(
            data.game_type, data.level, data.hand, data.duration_ms, data.series, meta)
    # level history BEFORE this session: the baseline / EWMA / best it is compared with
    before = (trend.level_history(db, data.patient_id, data.game_type, data.level, day)
              if scored else [])
    prev = trend.assess_trend(before)
    row = GameSession(
        patient_id=data.patient_id, game_type=data.game_type, level=data.level, hand=data.hand,
        started_at=created_at or _aware(data.started_at), day=day,
        duration_ms=data.duration_ms, completed=data.completed, abort_reason=data.abort_reason,
        input_device=data.client_meta.input_device,
        score=result.score if result else None,
        impairment_class=result.impairment_class if result else None,
        model_version=result.model_version if result else None,
        features=result.features if result else {},
        counts_for_trend=scored,
    )
    db.add(row)
    db.flush()
    db.add(SessionRaw(session_id=row.id, series=data.series, client_meta=meta))
    db.flush()
    if scored:
        trend.recompute_trends(db, data.patient_id, data.game_type, day)
    # also for aborted sessions: any entry closes a grey "no data" alert
    open_alert = alerts.evaluate_alerts(db, data.patient_id, day)
    db.commit()
    db.refresh(row)

    compared, personal_best = "not_scored", False
    if scored:
        if prev.baseline is None:
            compared = "first"
        else:
            diff = result.score - prev.baseline
            compared = "better" if diff >= BETTER_BAND else "lower" if diff <= -BETTER_BAND else "similar"
            personal_best = result.score > max(h.score for h in before)
    offer_retry = bool(scored and prev.smoothed is not None
                       and result.score <= prev.smoothed - RETRY_DROP and not _alarming(open_alert))
    extras = {"compared_to_usual": compared, "offer_retry": offer_retry,
              "personal_best": personal_best}

    todays = db.exec(select(Checkin).where(Checkin.patient_id == data.patient_id,
                                           Checkin.day == day)).all()
    fb = _warning_feedback(db, data.patient_id, [s for c in todays for s in c.warning_signs])
    if fb is None and _alarming(open_alert):
        fb = NEUTRAL
    if fb is None:
        text = "Hvala, da ste vadili. " + COMPARED_TEXT[compared]
        if personal_best:
            text += " To je vaš najboljši dosežek doslej."
        if offer_retry:
            text += " Če želite, poskusite še enkrat."
        fb = Feedback("thanks", "Hvala!", text)
    return row, fb, extras


def ingest_checkin(db: Session, data: CheckinIn, *, day: Optional[date] = None,
                   created_at: Optional[datetime] = None) -> tuple[Checkin, Feedback]:
    """Store the check-in, check warning signs and symptom rules, evaluate alerts."""
    day = day or clock.today()
    row = Checkin(
        patient_id=data.patient_id, day=day, created_at=created_at or clock.now(),
        warning_signs=data.warning_signs, answers=data.answers, concern=data.concern,
        concern_text=data.concern_text, answered_by=data.answered_by,
    )
    db.add(row)
    db.flush()
    open_alert = alerts.evaluate_alerts(db, data.patient_id, day)
    db.commit()
    db.refresh(row)
    fb = _warning_feedback(db, data.patient_id, data.warning_signs)
    if fb is None and _alarming(open_alert):
        fb = NEUTRAL
    if fb is None:
        text = THANKS.text
        if data.concern == "call":
            text += " Zdravnik bo videl, da si želite klic."
        fb = Feedback("thanks", THANKS.title, text)
    return row, fb
