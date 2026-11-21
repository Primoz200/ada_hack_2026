"""Alert rules and the human-in-the-loop state machine (plan section 8).

All thresholds are parameters here. Rules (all evaluated as of a `day`):

* red    warning_sign   a check-in of that day answered a warning sign "yes"
* red    double_yellow  a game yellow (trend_drop) and a check-in yellow (symptom_rise, or
                        concern_call in the last CONCURRENT_DAYS days) hold at the same time
* yellow trend_drop     combined trend (trace:all delta) <= -YELLOW_DROP_POINTS on at least
                        YELLOW_DAYS_HIT of the last YELLOW_DAYS_WINDOW days that have a session
* yellow symptom_rise   7-day mean of pain / tingling >= previous 7-day mean + threshold
                        (muted by the pathway's muted_patterns)
* yellow concern_call   the patient answered concern = "call"
* grey   no_data        no check-in and no session for GREY_AFTER_MISSED_DAYS days (sweep)

Anti-noise: exactly one open (status != closed) alert per patient. New triggers are appended
to evidence["triggers"]; severity / rule / reason escalate to the most severe trigger.

"Same episode" (no re-fire after the clinician closed an alert): a trigger is suppressed when
a clinician-closed alert of that patient contains the same rule, the trigger is not more
severe than that alert, and either the trigger concerns data up to the closing day or the
closing was less than SUPPRESS_DAYS_AFTER_CLOSE days ago. A warning_sign is only suppressed
for the day that was closed: a new check-in with a sign on a later day always alerts.
Acknowledged-but-open alerts simply keep collecting triggers (no new alert); if one is
escalated to a worse severity it returns to "new" so the clinician sees it again.
"""
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlmodel import Session, select

from app.models import Alert, Checkin, Clinician, GameSession, Pathway, Patient, TrendSnapshot
from app.services import clock, divergence

YELLOW_DROP_POINTS = 10.0  # combined trend at least this far below baseline ...
YELLOW_DAYS_HIT = 2  # ... on this many ...
YELLOW_DAYS_WINDOW = 3  # ... of the last N days that have a session
PAIN_RISE_POINTS = 2.0  # pain week-over-week
TINGLING_RISE_POINTS = 1.0  # tingling (0-4 scale) week-over-week
MIN_CHECKINS_PER_WEEK = 2  # both weeks need this many check-ins for a symptom comparison
REMINDER_AFTER_MISSED_DAYS = 2  # patient gets an automatic reminder
GREY_AFTER_MISSED_DAYS = 4  # clinician sees "brez podatkov"
CONCURRENT_DAYS = 3  # a concern_call this recent counts as a concurrent check-in yellow
SUPPRESS_DAYS_AFTER_CLOSE = 7  # same rule does not reopen within this many days of closing

SYMPTOM_RULES = {  # question id -> (Slovenian label, rise threshold)
    "pain": ("Bolečina", PAIN_RISE_POINTS),
    "tingling": ("Mravljinčenje", TINGLING_RISE_POINTS),
}

OUTCOME_LABELS = {
    "called_reassured": "Poklical, pomiril",
    "adjusted_exercises": "Prilagodil vaje",
    "visit_moved_earlier": "Pregled prestavljen naprej",
    "urgent_referral": "Nujna napotitev",
    "unreachable": "Nedosegljiv",
    "false_alarm": "Lažni alarm ali težava s podatki",
}

SEVERITY_RANK = {"grey": 0, "yellow": 1, "red": 2}
SYSTEM_ACK_TEXT = "Zdravnik je pregledal vaše rezultate."


# at equal severity the more urgent rule is the one shown (a sign beats the combined rule)
RULE_PRIORITY = {"warning_sign": 2, "double_yellow": 1}


def _priority(t: dict) -> tuple[int, int]:
    return SEVERITY_RANK[t["severity"]], RULE_PRIORITY.get(t["rule"], 0)


class AlertError(ValueError):
    """Invalid transition, e.g. closing without an outcome."""


# ------------------------------------------------------------------ helpers

def open_alert(db: Session, patient_id: str) -> Optional[Alert]:
    return db.exec(select(Alert).where(Alert.patient_id == patient_id, Alert.status != "closed")
                   .order_by(Alert.id.desc())).first()


def _stamp(day: date) -> datetime:
    """Time of an alert change: now for today, otherwise noon of the (replayed) day."""
    return clock.now() if day == clock.today() else clock.at(day, 12)


def _num(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def _trigger(rule: str, severity: str, source: str, day: date, reason: str, **extra: Any) -> dict:
    return {"rule": rule, "severity": severity, "source": source, "day": day, "reason": reason,
            "extra": extra}


# ------------------------------------------------------------------ rule evaluation

def _warning_trigger(db: Session, pathway: Pathway, patient_id: str, day: date) -> Optional[dict]:
    rows = db.exec(select(Checkin).where(Checkin.patient_id == patient_id, Checkin.day == day)).all()
    rows = [c for c in rows if c.warning_signs]
    if not rows:
        return None
    ids: list[str] = []
    for c in rows:
        ids += [s for s in c.warning_signs if s not in ids]
    texts = {w["id"]: w["text"] for w in pathway.warning_signs}
    names = ", ".join(texts.get(i, i)[:1].lower() + texts.get(i, i)[1:] for i in ids)
    return _trigger("warning_sign", "red", "checkin", day,
                    f"Pacient je v dnevnem vnosu pritrdil opozorilnemu znaku: {names}.",
                    warningSigns=ids, checkinIds=[c.id for c in rows])


def _trend_trigger(db: Session, patient_id: str, day: date) -> Optional[dict]:
    snaps = db.exec(select(TrendSnapshot).where(
        TrendSnapshot.patient_id == patient_id, TrendSnapshot.metric == "trace:all",
        TrendSnapshot.day <= day, TrendSnapshot.delta != None  # noqa: E711
    ).order_by(TrendSnapshot.day.desc()).limit(YELLOW_DAYS_WINDOW)).all()
    hits = [s for s in snaps if s.delta <= -YELLOW_DROP_POINTS]
    if len(hits) < YELLOW_DAYS_HIT:
        return None
    days = [s.day for s in snaps]
    sess = db.exec(select(GameSession.id).where(
        GameSession.patient_id == patient_id, GameSession.game_type == "trace",
        GameSession.day.in_(days), GameSession.counts_for_trend == True)).all()  # noqa: E712
    return _trigger(
        "trend_drop", "yellow", "game", snaps[0].day,
        f"Skupni trend je že {len(hits)} od zadnjih {len(snaps)} dni vsaj "
        f"{YELLOW_DROP_POINTS:.0f} točk pod izhodiščem.",
        delta=round(snaps[0].delta, 1), sessionIds=list(sess))


def _symptom_triggers(db: Session, pathway: Pathway, patient: Patient, day: date) -> list[dict]:
    rows = db.exec(select(Checkin).where(
        Checkin.patient_id == patient.id, Checkin.day <= day,
        Checkin.day > day - timedelta(days=14))).all()
    out = []
    for qid, (label, threshold) in SYMPTOM_RULES.items():
        recent = [c for c in rows if c.day > day - timedelta(days=7) and qid in c.answers]
        before = [c for c in rows if c.day <= day - timedelta(days=7) and qid in c.answers]
        if len(recent) < MIN_CHECKINS_PER_WEEK or len(before) < MIN_CHECKINS_PER_WEEK:
            continue
        m_recent = sum(c.answers[qid] for c in recent) / len(recent)
        m_before = sum(c.answers[qid] for c in before) / len(before)
        if m_recent < m_before + threshold:
            continue
        # pathway-muted expected pattern (e.g. ctr pain in the first weeks, below a ceiling)
        since = (day - patient.discharge_date).days
        if any(m.get("question") == qid and since <= m.get("untilDay", 0)
               and m_recent <= m.get("maxValue", 0) for m in pathway.muted_patterns):
            continue
        out.append(_trigger(
            "symptom_rise", "yellow", "checkin", day,
            f"{label} je v zadnjih 7 dneh v povprečju za {_num(m_recent - m_before)} točke višja kot teden prej.",
            question=qid, recentMean=round(m_recent, 2), previousMean=round(m_before, 2),
            checkinIds=[c.id for c in recent]))
    return out


def _concern_trigger(db: Session, patient_id: str, day: date, window: int = 1) -> Optional[dict]:
    rows = db.exec(select(Checkin).where(
        Checkin.patient_id == patient_id, Checkin.day <= day,
        Checkin.day > day - timedelta(days=window), Checkin.concern == "call"
    ).order_by(Checkin.day.desc(), Checkin.id.desc())).all()
    if not rows:
        return None
    last = rows[0]
    return _trigger("concern_call", "yellow", "checkin", last.day,
                    "Pacient si želi klic zdravnika.",
                    concernText=last.concern_text, checkinIds=[c.id for c in rows])


def _collect(db: Session, patient: Patient, day: date) -> list[dict]:
    pathway = db.get(Pathway, patient.pathway_code)
    out: list[dict] = []
    warn = _warning_trigger(db, pathway, patient.id, day)
    drop = _trend_trigger(db, patient.id, day)
    symptoms = _symptom_triggers(db, pathway, patient, day)
    concern = _concern_trigger(db, patient.id, day)
    if warn:
        out.append(warn)
    concern_recent = _concern_trigger(db, patient.id, day, CONCURRENT_DAYS)
    if drop and (symptoms or concern_recent):
        out.append(_trigger("double_yellow", "red", "game", day,
                            "Hkrati sta rumena znaka iz igre (trend) in iz dnevnega vnosa.",
                            delta=drop["extra"].get("delta")))
    if drop:
        out.append(drop)
    out += symptoms
    if concern:
        out.append(concern)
    return out


# ------------------------------------------------------------------ state handling

def _suppressed(db: Session, patient_id: str, t: dict, day: date) -> bool:
    closed = db.exec(select(Alert).where(
        Alert.patient_id == patient_id, Alert.status == "closed", Alert.closed_at != None  # noqa: E711
    )).all()
    for a in closed:
        if a.closed_by == "system":  # automatic closure of a grey alert is not a clinician decision
            continue
        rules = {a.rule} | {x.get("rule") for x in a.evidence.get("triggers", [])}
        if t["rule"] not in rules or SEVERITY_RANK[t["severity"]] > SEVERITY_RANK[a.severity]:
            continue
        closed_day = a.closed_at.date()
        if t["day"] <= closed_day:
            return True
        if t["rule"] != "warning_sign" and (day - closed_day).days < SUPPRESS_DAYS_AFTER_CLOSE:
            return True
    return False


def _autoclose_grey(db: Session, patient_id: str) -> None:
    """A grey (missing data) alert closes by itself, outcome None, once new data arrived."""
    a = open_alert(db, patient_id)
    if a is None or a.rule != "no_data" or a.severity != "grey":
        return
    new_c = db.exec(select(Checkin.id).where(Checkin.patient_id == patient_id,
                                             Checkin.day >= a.opened_day)).first()
    new_s = db.exec(select(GameSession.id).where(GameSession.patient_id == patient_id,
                                                 GameSession.day >= a.opened_day)).first()
    if new_c is None and new_s is None:
        return
    now = clock.now()
    a.status, a.closed_by, a.closed_at, a.updated_at = "closed", "system", now, now
    a.outcome = None
    db.add(a)
    db.flush()


def _merge(db: Session, patient_id: str, day: date, triggers: list[dict]) -> Optional[Alert]:
    triggers = [t for t in triggers if not _suppressed(db, patient_id, t, day)]
    alert = open_alert(db, patient_id)
    if alert is not None:
        seen = {(x.get("rule"), x.get("day")) for x in alert.evidence.get("triggers", [])}
        triggers = [t for t in triggers if (t["rule"], t["day"].isoformat()) not in seen]
    if triggers:
        top = max(triggers, key=_priority)  # first of the most severe
        entries = [{"rule": t["rule"], "severity": t["severity"], "source": t["source"],
                    "day": t["day"].isoformat(), "reason": t["reason"]} for t in triggers]
        extras: dict[str, Any] = {}
        for t in triggers:
            for k, v in t["extra"].items():
                if k in ("sessionIds", "checkinIds"):
                    extras[k] = sorted(set(extras.get(k, [])) | set(v))
                elif k == "warningSigns":
                    extras[k] = list(dict.fromkeys(extras.get(k, []) + v))
                elif k in ("delta", "concernText"):
                    extras[k] = v
        now = _stamp(day)
        if alert is None:
            alert = Alert(patient_id=patient_id, source=top["source"], rule=top["rule"],
                          severity=top["severity"], status="new", reason=top["reason"],
                          created_at=now, updated_at=now, opened_day=day, evidence={})
            ev: dict[str, Any] = {"triggers": []}
        else:
            ev = dict(alert.evidence)
            if _priority(top) > (SEVERITY_RANK[alert.severity], RULE_PRIORITY.get(alert.rule, 0)):
                worse = SEVERITY_RANK[top["severity"]] > SEVERITY_RANK[alert.severity]
                alert.source, alert.rule = top["source"], top["rule"]
                alert.severity, alert.reason = top["severity"], top["reason"]
                if worse and alert.status == "acknowledged":  # worse than what the clinician saw
                    alert.status = "new"
                    alert.acknowledged_by = alert.acknowledged_at = None
            alert.updated_at = now
        ev["triggers"] = list(ev.get("triggers", [])) + entries
        for k, v in extras.items():
            if k in ("sessionIds", "checkinIds"):
                v = sorted(set(ev.get(k, [])) | set(v))
            ev[k] = v
        alert.evidence = ev
        db.add(alert)
        db.flush()
    if alert is not None:
        diverging, sentence = divergence.assess(db, patient_id, day)
        if alert.diverging != diverging or alert.evidence.get("divergence") != sentence:
            alert.diverging = diverging
            alert.evidence = {**alert.evidence, "divergence": sentence}
            db.add(alert)
            db.flush()
    return alert


# ------------------------------------------------------------------ public API

def evaluate_alerts(db: Session, patient_id: str, day: date) -> Optional[Alert]:
    """Run all rules for the patient as of `day`; open an alert, attach a trigger to the
    open one, or escalate. Returns the patient's open alert (or None)."""
    patient = db.get(Patient, patient_id)
    if patient is None:
        return None
    triggers = _collect(db, patient, day)
    # a live yellow/red trigger escalates an open grey alert; otherwise new data closes it
    if not any(not _suppressed(db, patient_id, t, day) for t in triggers):
        _autoclose_grey(db, patient_id)
    return _merge(db, patient_id, day, triggers)


def _missing_trigger(db: Session, patient: Patient, day: date) -> Optional[dict]:
    if (day - patient.discharge_date).days < GREY_AFTER_MISSED_DAYS:
        return None
    last_c = db.exec(select(Checkin.day).where(Checkin.patient_id == patient.id, Checkin.day <= day)
                     .order_by(Checkin.day.desc())).first()
    last_s = db.exec(select(GameSession.day).where(GameSession.patient_id == patient.id,
                                                   GameSession.day <= day)
                     .order_by(GameSession.day.desc())).first()
    last = max([d for d in (last_c, last_s, patient.discharge_date) if d is not None])
    missed = (day - last).days
    if missed < GREY_AFTER_MISSED_DAYS:
        return None
    return _trigger("no_data", "grey", "missing", day,
                    f"Pacient že {missed} dni nima nobenega vnosa ali meritve.", missedDays=missed)


def sweep(db: Session, day: date) -> None:
    """Time-driven rules for ALL patients (missing entries -> grey). Called by the triage
    list endpoint and by the seed, because no submission triggers them."""
    for patient in db.exec(select(Patient)).all():
        _autoclose_grey(db, patient.id)
        if open_alert(db, patient.id) is not None:  # one open alert only; grey never piles on
            continue
        t = _missing_trigger(db, patient, day)
        if t:
            _merge(db, patient.id, day, [t])
    db.commit()


def acknowledge(db: Session, alert_id: int, clinician_id: str, close: bool,
                outcome: Optional[str], note: Optional[str]) -> Alert:
    """new -> acknowledged (who, when) -> closed with an outcome. Closing without an
    outcome raises AlertError."""
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise AlertError("Opozorilo ne obstaja.")
    clinician = db.get(Clinician, clinician_id)
    if clinician is None:
        raise AlertError("Zdravnik ne obstaja.")
    if alert.status == "closed":
        raise AlertError("Opozorilo je že zaprto.")
    if close and not outcome:
        raise AlertError("Opozorila ni mogoče zapreti brez izbranega izida.")
    if close and outcome not in OUTCOME_LABELS:
        raise AlertError("Neznan izid opozorila.")
    now = clock.now()
    if alert.acknowledged_at is None:
        alert.acknowledged_by, alert.acknowledged_at = clinician.name, now
        if alert.status == "new":
            alert.status = "acknowledged"
    if close:
        alert.status, alert.closed_by, alert.closed_at = "closed", clinician.name, now
        alert.outcome = outcome
    if note:
        alert.note = note
    alert.updated_at = now
    if not alert.evidence.get("ackMessageSent"):
        db.add(Message(patient_id=alert.patient_id, direction="system", author=None,
                       text=SYSTEM_ACK_TEXT, created_at=now))
        alert.evidence = {**alert.evidence, "ackMessageSent": True}
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
