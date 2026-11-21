"""Patient divergence, alert rule evaluation, and alert lifecycle merging."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from statistics import mean
from typing import Any, TypedDict

from sqlalchemy import column
from sqlmodel import Session, select

from app.models.tables import Alert, Checkin, GameSession, Patient, TrendSnapshot
from app.services import clock

DIVERGENCE_WEEK_DAYS = 7
SUBJECTIVE_WINDOW_DAYS = 14
SUBJECTIVE_MIN_CHECKINS_PER_WEEK = 2
DIVERGENCE_DECLINE_DELTA = -10.0
DIVERGENCE_STABLE_ABS_DELTA = 5.0
DIVERGENCE_FLAT_WELLBEING_CHANGE = -0.05
DIVERGENCE_WORSE_WELLBEING_CHANGE = -0.15
TREND_DROP_DELTA = -10.0
TREND_DROP_PREVIOUS_DELTA = -5.0
TREND_DROP_REQUIRED_PREVIOUS = 2
TREND_DROP_PREVIOUS_WINDOW = 3
BIG_DROP_DELTA = -20.0
SUBJECTIVE_CHANGE_THRESHOLD = 2.0
CLINICIAN_SUPPRESSION_DAYS = 7
NO_DATA_DAYS = 4
NO_DATA_REASON = "Pacient že več dni nima nobenega vnosa ali meritve."

DIVERGENCE_FALLING_SENTENCE = (
    "Rezultati sledenja padajo, pacient pa poroča enako ali boljše počutje."
)
DIVERGENCE_STABLE_SENTENCE = "Rezultati sledenja so stabilni, pacient pa poroča slabše počutje."
TREND_DROP_REASON = "Rezultati sledenja so že več dni pod pacientovim izhodiščem."
BIG_DROP_REASON = "Rezultati sledenja so močno padli pod pacientovo izhodišče."
BOTH_REASON = "Padajo rezultati sledenja in počutje hkrati."


class Trigger(TypedDict):
    rule: str
    severity: str
    source: str
    day: date
    reason: str
    evidence: dict[str, Any]


def _week_index(checkin: Checkin) -> float | None:
    values: list[float] = []
    for key, raw_value in checkin.answers.items():
        value = float(raw_value)
        if key == "wellbeing":
            values.append((value - 1.0) / 9.0)
        elif key == "pain":
            values.append((10.0 - value) / 9.0)
    return mean(values) if values else None


def _checkins(session: Session, patient_id: str, start: date, end: date) -> list[Checkin]:
    return list(
        session.exec(
            select(Checkin)
            .where(
                column("patient_id") == patient_id,
                column("day") >= start,
                column("day") <= end,
            )
            .order_by(column("day"), column("id"))
        ).all()
    )


def _latest_trace_delta(session: Session, patient_id: str, day: date) -> TrendSnapshot | None:
    return session.exec(
        select(TrendSnapshot)
        .where(
            column("patient_id") == patient_id,
            column("metric") == "trace:all",
            column("day") <= day,
            column("delta").is_not(None),
        )
        .order_by(column("day").desc(), column("id").desc())
    ).first()


def divergence(session: Session, patient_id: str, day: date) -> tuple[bool, str | None]:
    """Compare the latest trace trend delta with the change in wellbeing index."""
    snapshot = _latest_trace_delta(session, patient_id, day)
    if snapshot is None or snapshot.delta is None:
        return False, None
    recent_start = day - timedelta(days=DIVERGENCE_WEEK_DAYS - 1)
    previous_end = recent_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=DIVERGENCE_WEEK_DAYS - 1)
    recent_values = [
        index
        for checkin in _checkins(session, patient_id, recent_start, day)
        if (index := _week_index(checkin)) is not None
    ]
    previous_values = [
        index
        for checkin in _checkins(session, patient_id, previous_start, previous_end)
        if (index := _week_index(checkin)) is not None
    ]
    if not recent_values or not previous_values:
        return False, None
    change = mean(recent_values) - mean(previous_values)
    if snapshot.delta <= DIVERGENCE_DECLINE_DELTA and change >= DIVERGENCE_FLAT_WELLBEING_CHANGE:
        return True, DIVERGENCE_FALLING_SENTENCE
    if (
        abs(snapshot.delta) < DIVERGENCE_STABLE_ABS_DELTA
        and change <= DIVERGENCE_WORSE_WELLBEING_CHANGE
    ):
        return True, DIVERGENCE_STABLE_SENTENCE
    return False, None


def _session_ids_for_snapshot_days(
    session: Session, patient_id: str, days: Iterable[date]
) -> list[int]:
    selected_days = sorted(set(days))
    if not selected_days:
        return []
    rows = session.exec(
        select(GameSession).where(
            column("patient_id") == patient_id,
            column("game_type") == "trace",
            column("day").in_(selected_days),
            column("counts_for_trend").is_(True),
            column("score").is_not(None),
        )
    ).all()
    return sorted(row.id for row in rows if row.id is not None)


def _latest_patient_activity(session: Session, patient_id: str, patient: Patient) -> date:
    latest_checkin = session.exec(
        select(Checkin).where(column("patient_id") == patient_id).order_by(column("day").desc())
    ).first()
    latest_session = session.exec(
        select(GameSession).where(column("patient_id") == patient_id).order_by(column("day").desc())
    ).first()
    return max(
        patient.discharge_date,
        latest_checkin.day if latest_checkin is not None else patient.discharge_date,
        latest_session.day if latest_session is not None else patient.discharge_date,
    )


def evaluate_triggers(session: Session, patient_id: str, day: date) -> list[Trigger]:
    """Evaluate all specified alert rules for a patient as of a date."""
    triggers: list[Trigger] = []
    snapshots = list(
        session.exec(
            select(TrendSnapshot)
            .where(
                column("patient_id") == patient_id,
                column("metric") == "trace:all",
                column("day") <= day,
                column("delta").is_not(None),
            )
            .order_by(column("day").desc(), column("id").desc())
        ).all()
    )
    if snapshots:
        latest = snapshots[0]
        assert latest.delta is not None
        previous = [row for row in snapshots[1:] if row.delta is not None][
            :TREND_DROP_PREVIOUS_WINDOW
        ]
        previous_deltas = [float(row.delta) for row in previous if row.delta is not None]
        if (
            latest.delta <= TREND_DROP_DELTA
            and sum(value <= TREND_DROP_PREVIOUS_DELTA for value in previous_deltas)
            >= TREND_DROP_REQUIRED_PREVIOUS
        ):
            involved_days = [latest.day, *(row.day for row in previous)]
            triggers.append(
                {
                    "rule": "trend_drop",
                    "severity": "yellow",
                    "source": "game",
                    "day": latest.day,
                    "reason": TREND_DROP_REASON,
                    "evidence": {
                        "delta": round(float(latest.delta), 1),
                        "sessionIds": _session_ids_for_snapshot_days(
                            session, patient_id, involved_days
                        ),
                        "previousDeltas": [round(value, 1) for value in previous_deltas],
                    },
                }
            )
        if latest.delta <= BIG_DROP_DELTA:
            triggers.append(
                {
                    "rule": "big_drop",
                    "severity": "red",
                    "source": "game",
                    "day": latest.day,
                    "reason": BIG_DROP_REASON,
                    "evidence": {
                        "delta": round(float(latest.delta), 1),
                        "sessionIds": _session_ids_for_snapshot_days(
                            session, patient_id, [latest.day]
                        ),
                    },
                }
            )

    recent_week_start = day - timedelta(days=DIVERGENCE_WEEK_DAYS - 1)
    previous_week_end = recent_week_start - timedelta(days=1)
    previous_week_start = day - timedelta(days=SUBJECTIVE_WINDOW_DAYS - 1)
    recent = _checkins(session, patient_id, recent_week_start, day)
    previous_week = _checkins(session, patient_id, previous_week_start, previous_week_end)
    recent_values: dict[str, list[float]] = {"wellbeing": [], "pain": []}
    previous_values: dict[str, list[float]] = {"wellbeing": [], "pain": []}
    for checkin in recent:
        for key in recent_values:
            if key in checkin.answers:
                recent_values[key].append(float(checkin.answers[key]))
    for checkin in previous_week:
        for key in previous_values:
            if key in checkin.answers:
                previous_values[key].append(float(checkin.answers[key]))
    changes: dict[str, float | None] = {}
    for key in recent_values:
        if (
            len(recent) >= SUBJECTIVE_MIN_CHECKINS_PER_WEEK
            and len(previous_week) >= SUBJECTIVE_MIN_CHECKINS_PER_WEEK
            and recent_values[key]
            and previous_values[key]
        ):
            changes[key] = mean(recent_values[key]) - mean(previous_values[key])
        else:
            changes[key] = None
    wellbeing_drop = (
        changes["wellbeing"] is not None and changes["wellbeing"] <= -SUBJECTIVE_CHANGE_THRESHOLD
    )
    pain_rise = changes["pain"] is not None and changes["pain"] >= SUBJECTIVE_CHANGE_THRESHOLD
    if wellbeing_drop or pain_rise:
        if wellbeing_drop and pain_rise:
            reason = "Pacient poroča slabše počutje in močnejšo bolečino kot prejšnji teden."
        elif wellbeing_drop:
            reason = "Pacient poroča slabše počutje kot prejšnji teden."
        else:
            reason = "Pacient poroča močnejšo bolečino kot prejšnji teden."
        triggers.append(
            {
                "rule": "subjective_drop",
                "severity": "yellow",
                "source": "checkin",
                "day": recent[-1].day,
                "reason": reason,
                "evidence": {
                    "wellbeingChange": (
                        round(changes["wellbeing"], 2) if changes["wellbeing"] is not None else None
                    ),
                    "painChange": (
                        round(changes["pain"], 2) if changes["pain"] is not None else None
                    ),
                    "checkinIds": sorted(
                        checkin.id for checkin in recent if checkin.id is not None
                    ),
                },
            }
        )

    trend_trigger = next((item for item in triggers if item["rule"] == "trend_drop"), None)
    subjective_trigger = next(
        (item for item in triggers if item["rule"] == "subjective_drop"), None
    )
    if trend_trigger is not None and subjective_trigger is not None:
        trend_values = trend_trigger["evidence"]
        subjective_values = subjective_trigger["evidence"]
        trigger_day = max(trend_trigger["day"], subjective_trigger["day"])
        triggers.append(
            {
                "rule": "both",
                "severity": "red",
                "source": "game",
                "day": trigger_day,
                "reason": BOTH_REASON,
                "evidence": {
                    "delta": trend_values["delta"],
                    "wellbeingChange": subjective_values["wellbeingChange"],
                    "painChange": subjective_values["painChange"],
                },
            }
        )
    return triggers


def _severity_rank(severity: str) -> int:
    return {"grey": 0, "yellow": 1, "red": 2}[severity]


def _priority(rule: str) -> int:
    return {"both": 3, "big_drop": 2}.get(rule, 1)


TRIGGER_ORDER = {"both": 0, "big_drop": 1, "trend_drop": 2, "subjective_drop": 3}


def _preferred(triggers: list[Trigger]) -> Trigger:
    return max(
        triggers,
        key=lambda item: (_severity_rank(item["severity"]), _priority(item["rule"])),
    )


def _alert_time(day: date, override: datetime | None = None) -> datetime:
    if day == clock.today():
        return override or clock.now()
    return datetime.combine(day, time(hour=12), tzinfo=UTC)


def _closed_day(alert: Alert) -> date:
    closed = alert.closed_at
    if closed is None:
        return alert.opened_day
    return closed.date() if closed.tzinfo is not None else closed.date()


def _is_suppressed(session: Session, patient_id: str, trigger: Trigger, as_of: date) -> bool:
    closed_alerts = session.exec(
        select(Alert).where(Alert.patient_id == patient_id, Alert.status == "closed")
    ).all()
    for alert in closed_alerts:
        if alert.closed_by in {None, "system"}:
            continue
        prior_rules = {alert.rule}
        prior_rules.update(
            str(item.get("rule"))
            for item in alert.evidence.get("triggers", [])
            if isinstance(item, dict)
        )
        closing_day = _closed_day(alert)
        if (
            trigger["rule"] in prior_rules
            and _severity_rank(trigger["severity"]) <= _severity_rank(alert.severity)
            and (
                trigger["day"] <= closing_day
                or 0 <= (as_of - closing_day).days < CLINICIAN_SUPPRESSION_DAYS
            )
        ):
            return True
    return False


def _merge_evidence(
    existing: dict[str, Any], live: list[Trigger], divergence_sentence: str | None
) -> tuple[dict[str, Any], bool]:
    prior_triggers = [dict(item) for item in existing.get("triggers", []) if isinstance(item, dict)]
    seen = {(str(item.get("rule")), str(item.get("day"))) for item in prior_triggers}
    appended = False
    for trigger in live:
        seen_key = (trigger["rule"], trigger["day"].isoformat())
        if seen_key not in seen:
            appended = True
            prior_triggers.append(
                {
                    "rule": trigger["rule"],
                    "severity": trigger["severity"],
                    "source": trigger["source"],
                    "day": trigger["day"].isoformat(),
                    "reason": trigger["reason"],
                }
            )
            seen.add(seen_key)
    evidence: dict[str, Any] = dict(existing)
    evidence["triggers"] = prior_triggers
    for evidence_key in ("sessionIds", "checkinIds"):
        ids = {int(item) for item in existing.get(evidence_key, [])}
        ids.update(
            int(item) for trigger in live for item in trigger["evidence"].get(evidence_key, [])
        )
        if ids:
            evidence[evidence_key] = sorted(ids)
    for evidence_key in ("delta", "previousDeltas", "wellbeingChange", "painChange", "missedDays"):
        for trigger in reversed(live):
            value = trigger["evidence"].get(evidence_key)
            if value is not None:
                evidence[evidence_key] = value
                break
    if divergence_sentence != existing.get("divergence"):
        evidence["divergence"] = divergence_sentence
    elif "divergence" in existing:
        evidence["divergence"] = existing["divergence"]
    return evidence, appended


def evaluate_alerts(
    session: Session,
    patient_id: str,
    day: date,
    *,
    evaluated_at: datetime | None = None,
) -> Alert | None:
    """Merge currently firing rules into at most one open alert for the patient."""
    all_triggers = evaluate_triggers(session, patient_id, day)
    all_triggers.sort(key=lambda trigger: TRIGGER_ORDER.get(trigger["rule"], 4))
    live = [
        trigger for trigger in all_triggers if not _is_suppressed(session, patient_id, trigger, day)
    ]
    diverging, divergence_sentence = divergence(session, patient_id, day)
    open_alert = session.exec(
        select(Alert)
        .where(
            column("patient_id") == patient_id,
            column("status").in_(["new", "acknowledged"]),
        )
        .order_by(column("id"))
    ).first()
    patient = session.get(Patient, patient_id)
    if patient is None:
        raise LookupError(f"No patient with id {patient_id!r}")
    if open_alert is None and not live:
        latest_activity = _latest_patient_activity(session, patient_id, patient)
        missed_days = (day - latest_activity).days
        if (day - patient.discharge_date).days >= NO_DATA_DAYS and missed_days >= NO_DATA_DAYS:
            live = [
                {
                    "rule": "no_data",
                    "severity": "grey",
                    "source": "missing",
                    "day": day,
                    "reason": NO_DATA_REASON,
                    "evidence": {"missedDays": missed_days},
                }
            ]
    if open_alert is not None and open_alert.rule == "no_data":
        latest_activity = _latest_patient_activity(session, patient_id, patient)
        if latest_activity >= open_alert.opened_day:
            if not any(
                _severity_rank(trigger["severity"]) > _severity_rank("grey") for trigger in live
            ):
                timestamp = _alert_time(day, evaluated_at)
                open_alert.status = "closed"
                open_alert.closed_by = "system"
                open_alert.closed_at = timestamp
                open_alert.outcome = None
                session.add(open_alert)
                session.commit()
                session.refresh(open_alert)
                return open_alert
    if open_alert is None and not live:
        return None
    if open_alert is None:
        chosen = _preferred(live)
        timestamp = _alert_time(day, evaluated_at)
        open_alert = Alert(
            patient_id=patient_id,
            patient_name=patient.name,
            source=chosen["source"],
            rule=chosen["rule"],
            severity=chosen["severity"],
            status="new",
            reason=chosen["reason"],
            evidence=_merge_evidence({}, live, divergence_sentence)[0],
            diverging=diverging,
            opened_day=day,
            created_at=timestamp,
            updated_at=timestamp,
        )
        session.add(open_alert)
    else:
        if live:
            current_priority = (_severity_rank(open_alert.severity), _priority(open_alert.rule))
            chosen = _preferred(live)
            chosen_priority = (_severity_rank(chosen["severity"]), _priority(chosen["rule"]))
            if chosen_priority > current_priority:
                was_acknowledged = open_alert.status == "acknowledged"
                prior_severity = open_alert.severity
                open_alert.source = chosen["source"]
                open_alert.rule = chosen["rule"]
                open_alert.severity = chosen["severity"]
                open_alert.reason = chosen["reason"]
                if was_acknowledged and _severity_rank(chosen["severity"]) > _severity_rank(
                    prior_severity
                ):
                    open_alert.status = "new"
                    open_alert.acknowledged_by = None
                    open_alert.acknowledged_at = None
        open_alert.evidence, appended = _merge_evidence(
            open_alert.evidence, live, divergence_sentence
        )
        open_alert.diverging = diverging
        if appended:
            open_alert.updated_at = _alert_time(day, evaluated_at)
        session.add(open_alert)
    session.commit()
    session.refresh(open_alert)
    return open_alert


def sweep_missing_data_alerts(session: Session, day: date) -> list[Alert]:
    """Open or close only missing-data alerts for every patient as of a date."""
    patients = session.exec(select(Patient).order_by(column("id"))).all()
    results: list[Alert] = []
    for patient in patients:
        open_alert = session.exec(
            select(Alert)
            .where(
                column("patient_id") == patient.id,
                column("status").in_(["new", "acknowledged"]),
            )
            .order_by(column("id"))
        ).first()
        latest_activity = _latest_patient_activity(session, patient.id, patient)
        if (
            open_alert is not None
            and open_alert.severity == "grey"
            and open_alert.rule == "no_data"
            and latest_activity >= open_alert.opened_day
        ):
            open_alert.status = "closed"
            open_alert.closed_by = "system"
            open_alert.closed_at = _alert_time(day)
            open_alert.outcome = None
            session.add(open_alert)
            session.commit()
            session.refresh(open_alert)
            results.append(open_alert)
            continue
        if open_alert is not None:
            continue
        missed_days = (day - latest_activity).days
        if (day - patient.discharge_date).days < NO_DATA_DAYS or missed_days < NO_DATA_DAYS:
            continue

        timestamp = _alert_time(day)
        diverging, divergence_sentence = divergence(session, patient.id, day)
        trigger: Trigger = {
            "rule": "no_data",
            "severity": "grey",
            "source": "missing",
            "day": day,
            "reason": NO_DATA_REASON,
            "evidence": {"missedDays": missed_days},
        }
        alert = Alert(
            patient_id=patient.id,
            patient_name=patient.name,
            source="missing",
            rule="no_data",
            severity="grey",
            status="new",
            reason=NO_DATA_REASON,
            evidence=_merge_evidence({}, [trigger], divergence_sentence)[0],
            diverging=diverging,
            opened_day=day,
            created_at=timestamp,
            updated_at=timestamp,
        )
        session.add(alert)
        session.commit()
        session.refresh(alert)
        results.append(alert)
    return results
