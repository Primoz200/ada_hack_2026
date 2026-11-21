"""Alert rules and the human-in-the-loop state machine (plan section 8, v8).

v8: alerts are the clinician's business only; the patient never sees them and is never
prompted to call anyone. All thresholds are parameters here. Rules (evaluated as of a `day`):

* yellow trend_drop       PER GAME (tracing "trace", camera exercises "camera"): the latest
                          combined trend of that game (<game>:all delta) <= -TREND_DROP_POINTS
                          AND on at least PREVIOUS_DAYS_HIT of the previous PREVIOUS_DAYS_WINDOW
                          session-days of that game the delta was <= -BELOW_BAND_POINTS
                          (outside the baseline band). One bad day of a stable patient opens
                          nothing; a patient who has been drifting below baseline tips over.
* yellow subjective_drop  7-day mean of `wellbeing` >= WELLBEING_DROP_POINTS lower than the
                          7 days before, OR 7-day mean of `pain` >= PAIN_RISE_POINTS higher.
                          Each week needs MIN_CHECKINS_PER_WEEK check-ins.
* red    both             a trend_drop of ANY game and subjective_drop hold at the same time
                          (one trigger per dropping game)
* red    big_drop         PER GAME: the latest combined delta <= -BIG_DROP_POINTS
* grey   no_data          no check-in and no session for GREY_AFTER_MISSED_DAYS days (sweep);
                          closes by itself once data arrives

Several measurements are followed: every game-trend trigger carries `game`, and a patient
without camera data is simply followed on tracing only.

Anti-noise: exactly one open (status != closed) alert per patient. New triggers are appended
to evidence["triggers"]; severity / rule / reason escalate to the most severe trigger. The
reason of a game alert names the measurements of the episode (every game that had a
trend trigger in this alert): tracing, camera exercises or both. evidence["games"] holds
{game: {"delta"}} for the games whose trend rule holds at the latest evaluation that had any,
evidence["delta"] the worst of them.

"Same episode" (no re-fire after the clinician closed an alert): a trigger is suppressed when
a clinician-closed alert of that patient contains the same rule FOR THE SAME GAME, the
trigger is not more severe than that alert, and either the trigger concerns data up to the
closing day or the closing was less than SUPPRESS_DAYS_AFTER_CLOSE days ago. So closing a
tracing alert does not silence a later camera drop. Acknowledged-but-open alerts simply keep
collecting triggers (no new alert); if one is escalated to a worse severity it returns to
"new" so the clinician sees it again.

Reasons are one short Slovenian sentence without numbers; the numbers are in `evidence`.
"""
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlmodel import Session, select

from app.models import Alert, Checkin, Clinician, GameSession, Patient, TrendSnapshot
from app.services import clock, divergence
from app.services.trend import GAMES

TREND_DROP_POINTS = 10.0  # latest combined trend at least this far below baseline ...
BELOW_BAND_POINTS = 5.0  # ... and outside the baseline band (<= -5) ...
PREVIOUS_DAYS_HIT = 2  # ... on at least this many ...
PREVIOUS_DAYS_WINDOW = 3  # ... of the previous N session-days
BIG_DROP_POINTS = 20.0  # latest combined trend this far below baseline: red on its own
WELLBEING_DROP_POINTS = 2.0  # wellbeing (1-10, higher = better) week over week
PAIN_RISE_POINTS = 2.0  # pain (1-10, higher = worse) week over week
WEEK_DAYS = 7
MIN_CHECKINS_PER_WEEK = 2  # both weeks need this many check-ins for a comparison
GREY_AFTER_MISSED_DAYS = 4  # clinician sees "brez podatkov"
SUPPRESS_DAYS_AFTER_CLOSE = 7  # same rule does not reopen within this many days of closing

REASONS = {
    "trend_drop": "Rezultati sledenja so že več dni pod pacientovim izhodiščem.",
    "big_drop": "Rezultati sledenja so močno padli pod pacientovo izhodišče.",
    "both": "Padajo rezultati sledenja in počutje hkrati.",
    "wellbeing": "Pacient poroča slabše počutje kot prejšnji teden.",
    "pain": "Pacient poroča močnejšo bolečino kot prejšnji teden.",
    "wellbeing_pain": "Pacient poroča slabše počutje in močnejšo bolečino kot prejšnji teden.",
    "no_data": "Pacient že več dni nima nobenega vnosa ali meritve.",
}

# game-trend sentences by (rule, the games concerned in GAMES order)
GAME_REASONS = {
    ("trend_drop", ("trace",)): REASONS["trend_drop"],
    ("trend_drop", ("camera",)): "Rezultati vaj s kamero so že več dni pod pacientovim izhodiščem.",
    ("trend_drop", ("trace", "camera")): "Padajo rezultati sledenja in vaj s kamero.",
    ("big_drop", ("trace",)): REASONS["big_drop"],
    ("big_drop", ("camera",)): "Rezultati vaj s kamero so močno padli pod pacientovo izhodišče.",
    ("big_drop", ("trace", "camera")): "Rezultati sledenja in vaj s kamero so močno padli pod pacientovo izhodišče.",
    ("both", ("trace",)): REASONS["both"],
    ("both", ("camera",)): "Padajo rezultati meritev in počutje hkrati.",
    ("both", ("trace", "camera")): "Padajo rezultati meritev in počutje hkrati.",
}


def game_reason(rule: str, games) -> str:
    key = tuple(g for g in GAMES if g in set(games)) or ("trace",)
    return GAME_REASONS[(rule, key)]

OUTCOME_LABELS = {
    "called_reassured": "Poklical, pomiril",
    "adjusted_exercises": "Prilagodil vaje",
    "visit_moved_earlier": "Pregled prestavljen naprej",
    "urgent_referral": "Nujna napotitev",
    "unreachable": "Nedosegljiv",
    "false_alarm": "Lažni alarm ali težava s podatki",
}

SEVERITY_RANK = {"grey": 0, "yellow": 1, "red": 2}
# at equal severity the rule shown is the more telling one (both signals beat one big drop)
RULE_PRIORITY = {"both": 2, "big_drop": 1}
GAME_RULES = ("trend_drop", "big_drop", "both")


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


def _trigger(rule: str, severity: str, source: str, day: date, reason: str,
             game: Optional[str] = None, **extra: Any) -> dict:
    return {"rule": rule, "severity": severity, "source": source, "day": day, "reason": reason,
            "game": game, "extra": extra}


def _trigger_key(x: dict) -> tuple:
    """(rule, game) of a trigger or a stored trigger entry; stored game-rule entries from
    before camera exercises existed have no game and are tracing."""
    rule, game = x.get("rule"), x.get("game")
    if rule in GAME_RULES and not game:
        game = "trace"
    return rule, game


# ------------------------------------------------------------------ rule evaluation

def _combined(db: Session, patient_id: str, day: date, n: int, game: str = "trace") -> list[TrendSnapshot]:
    """The last n <game>:all snapshots with a delta up to `day`, newest first."""
    return list(db.exec(select(TrendSnapshot).where(
        TrendSnapshot.patient_id == patient_id, TrendSnapshot.metric == f"{game}:all",
        TrendSnapshot.day <= day, TrendSnapshot.delta != None  # noqa: E711
    ).order_by(TrendSnapshot.day.desc()).limit(n)).all())


def _session_ids(db: Session, patient_id: str, days: list[date], game: str = "trace") -> list[int]:
    return list(db.exec(select(GameSession.id).where(
        GameSession.patient_id == patient_id, GameSession.game_type == game,
        GameSession.day.in_(days), GameSession.counts_for_trend == True)).all())  # noqa: E712


def _game_triggers(db: Session, patient_id: str, day: date,
                   game: str = "trace") -> tuple[Optional[dict], Optional[dict]]:
    """(trend_drop, big_drop) triggers of one game, each None when the rule does not hold."""
    snaps = _combined(db, patient_id, day, PREVIOUS_DAYS_WINDOW + 1, game)
    if not snaps:
        return None, None
    latest, previous = snaps[0], snaps[1:]
    ids = _session_ids(db, patient_id, [s.day for s in snaps], game)
    delta = round(latest.delta, 1)
    drop = big = None
    hits = sum(1 for s in previous if s.delta <= -BELOW_BAND_POINTS)
    if latest.delta <= -TREND_DROP_POINTS and hits >= PREVIOUS_DAYS_HIT:
        drop = _trigger("trend_drop", "yellow", "game", latest.day, game_reason("trend_drop", [game]),
                        game=game, delta=delta, sessionIds=ids,
                        previousDeltas=[round(s.delta, 1) for s in previous])
    if latest.delta <= -BIG_DROP_POINTS:
        big = _trigger("big_drop", "red", "game", latest.day, game_reason("big_drop", [game]),
                       game=game, delta=delta, sessionIds=ids)
    return drop, big


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def _subjective_trigger(db: Session, patient_id: str, day: date) -> Optional[dict]:
    rows = db.exec(select(Checkin).where(
        Checkin.patient_id == patient_id, Checkin.day <= day,
        Checkin.day > day - timedelta(days=2 * WEEK_DAYS)).order_by(Checkin.day)).all()
    recent = [c for c in rows if c.day > day - timedelta(days=WEEK_DAYS)]
    before = [c for c in rows if c.day <= day - timedelta(days=WEEK_DAYS)]

    def change(key: str) -> Optional[float]:
        r = [c.answers[key] for c in recent if key in c.answers]
        b = [c.answers[key] for c in before if key in c.answers]
        if len(r) < MIN_CHECKINS_PER_WEEK or len(b) < MIN_CHECKINS_PER_WEEK:
            return None
        return _mean(r) - _mean(b)

    wb, pain = change("wellbeing"), change("pain")
    worse_wb = wb is not None and wb <= -WELLBEING_DROP_POINTS
    worse_pain = pain is not None and pain >= PAIN_RISE_POINTS
    if not (worse_wb or worse_pain):
        return None
    key = "wellbeing_pain" if worse_wb and worse_pain else "wellbeing" if worse_wb else "pain"
    return _trigger("subjective_drop", "yellow", "checkin", recent[-1].day, REASONS[key],
                    wellbeingChange=None if wb is None else round(wb, 2),
                    painChange=None if pain is None else round(pain, 2),
                    checkinIds=[c.id for c in recent])


def _collect(db: Session, patient: Patient, day: date) -> list[dict]:
    """All triggers that hold as of `day`. Game triggers of the worst game come first, so at
    equal severity the alert follows the game that dropped most."""
    drops, bigs = [], []
    for game in GAMES:
        drop, big = _game_triggers(db, patient.id, day, game)
        drops += [drop] if drop else []
        bigs += [big] if big else []
    drops.sort(key=lambda t: t["extra"]["delta"])
    bigs.sort(key=lambda t: t["extra"]["delta"])
    subjective = _subjective_trigger(db, patient.id, day)
    out: list[dict] = []
    if subjective:
        for drop in drops:
            out.append(_trigger("both", "red", "game", max(drop["day"], subjective["day"]),
                                game_reason("both", [drop["game"]]), game=drop["game"],
                                delta=drop["extra"]["delta"],
                                wellbeingChange=subjective["extra"]["wellbeingChange"],
                                painChange=subjective["extra"]["painChange"]))
    out += bigs + drops + ([subjective] if subjective else [])
    return out


# ------------------------------------------------------------------ state handling

def _suppressed(db: Session, patient_id: str, t: dict, day: date) -> bool:
    closed = db.exec(select(Alert).where(
        Alert.patient_id == patient_id, Alert.status == "closed", Alert.closed_at != None  # noqa: E711
    )).all()
    for a in closed:
        if a.closed_by == "system":  # automatic closure of a grey alert is not a clinician decision
            continue
        # same rule for the same game: closing a tracing alert does not silence a camera drop
        keys = {_trigger_key(x) for x in a.evidence.get("triggers", [])} or {_trigger_key({"rule": a.rule})}
        if _trigger_key(t) not in keys or SEVERITY_RANK[t["severity"]] > SEVERITY_RANK[a.severity]:
            continue
        closed_day = a.closed_at.date()
        if t["day"] <= closed_day or (day - closed_day).days < SUPPRESS_DAYS_AFTER_CLOSE:
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


_LATEST_KEYS = ("wellbeingChange", "painChange", "missedDays")


def _game_evidence(live: list[dict]) -> dict[str, Any]:
    """games / delta / previousDeltas from the live game-trend triggers (rebuilt on every
    evaluation that has any, so a game that recovered drops out of `games`)."""
    games: dict[str, dict] = {}
    previous: dict[str, list] = {}
    for t in live:
        if t["rule"] in GAME_RULES and t["game"]:
            games[t["game"]] = {"delta": t["extra"]["delta"]}
            if "previousDeltas" in t["extra"]:
                previous[t["game"]] = t["extra"]["previousDeltas"]
    if not games:
        return {}
    worst = min(games, key=lambda g: games[g]["delta"])
    out: dict[str, Any] = {"games": {g: games[g] for g in GAMES if g in games}, "delta": games[worst]["delta"]}
    if worst in previous:
        out["previousDeltas"] = previous[worst]
    return out


def _entry(t: dict) -> dict:
    e = {"rule": t["rule"], "severity": t["severity"], "source": t["source"],
         "day": t["day"].isoformat(), "reason": t["reason"]}
    if t["game"]:
        e["game"] = t["game"]
    return e


def _merge(db: Session, patient_id: str, day: date, triggers: list[dict]) -> Optional[Alert]:
    live = [t for t in triggers if not _suppressed(db, patient_id, t, day)]
    alert = open_alert(db, patient_id)
    triggers = live
    if alert is not None:
        seen = {(*_trigger_key(x), x.get("day")) for x in alert.evidence.get("triggers", [])}
        triggers = [t for t in live if (*_trigger_key(t), t["day"].isoformat()) not in seen]
    # numbers and ids come from every live trigger, so the evidence follows the latest data of
    # the day (e.g. all three sessions of a self-check), while trigger entries are appended once
    extras: dict[str, Any] = _game_evidence(live)
    for t in live:
        for k, v in t["extra"].items():
            if k in ("sessionIds", "checkinIds"):
                extras[k] = sorted(set(extras.get(k, [])) | set(v))
            elif k in _LATEST_KEYS and (v is not None or k not in extras):
                extras[k] = v
    entries = [_entry(t) for t in triggers]
    if triggers:
        top = max(triggers, key=_priority)  # first of the most severe
        now = _stamp(day)
        if alert is None:
            alert = Alert(patient_id=patient_id, source=top["source"], rule=top["rule"],
                          severity=top["severity"], status="new", reason=top["reason"],
                          created_at=now, updated_at=now, opened_day=day, evidence={"triggers": []})
        elif _priority(top) > (SEVERITY_RANK[alert.severity], RULE_PRIORITY.get(alert.rule, 0)):
            worse = SEVERITY_RANK[top["severity"]] > SEVERITY_RANK[alert.severity]
            alert.source, alert.rule = top["source"], top["rule"]
            alert.severity, alert.reason = top["severity"], top["reason"]
            if worse and alert.status == "acknowledged":  # worse than what the clinician saw
                alert.status = "new"
                alert.acknowledged_by = alert.acknowledged_at = None
        alert.updated_at = now
    if alert is not None and (entries or extras):
        ev = dict(alert.evidence)
        ev["triggers"] = list(ev.get("triggers", [])) + entries
        for k, v in extras.items():
            if k in ("sessionIds", "checkinIds"):
                v = sorted(set(ev.get(k, [])) | set(v))
            ev[k] = v
        if ev != alert.evidence:
            alert.evidence = ev
            db.add(alert)
            db.flush()
    if alert is not None and alert.rule in GAME_RULES:
        # the sentence names every measurement of this episode (tracing, camera or both)
        games = {_trigger_key(x)[1] for x in alert.evidence.get("triggers", []) if x.get("rule") in GAME_RULES}
        reason = game_reason(alert.rule, games)
        if reason != alert.reason:
            alert.reason = reason
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


def has_open_game_alert(db: Session, patient_id: str) -> bool:
    """An open yellow / red alert that comes from the game trend (used by patient feedback)."""
    a = open_alert(db, patient_id)
    if a is None or a.severity not in ("yellow", "red"):
        return False
    rules = {a.rule} | {x.get("rule") for x in a.evidence.get("triggers", [])}
    return bool(rules & set(GAME_RULES))


def open_alert_games(db: Session, patient_id: str) -> set[str]:
    """Games with a trend trigger in the open yellow / red alert (patient feedback per game)."""
    a = open_alert(db, patient_id)
    if a is None or a.severity not in ("yellow", "red"):
        return set()
    return {_trigger_key(x)[1] for x in a.evidence.get("triggers", []) if x.get("rule") in GAME_RULES}


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
    return _trigger("no_data", "grey", "missing", day, REASONS["no_data"], missedDays=missed)


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
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
