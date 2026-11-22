"""Unit tests for divergence, alert rules, and alert merging."""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

import app.db as database
import app.services.alerts as alert_service
from app.models.tables import Alert, Checkin, GameSession, TrendSnapshot
from app.services.alerts import (
    BIG_DROP_REASON,
    BOTH_REASON,
    DIVERGENCE_FALLING_SENTENCE,
    SUBJECTIVE_CHANGE_THRESHOLD,
    divergence,
    evaluate_alerts,
    evaluate_triggers,
)


def _add_checkin(session: Session, day: date, wellbeing: int, pain: int) -> None:
    session.add(
        Checkin(
            patient_id="p3",
            day=day,
            created_at=datetime.combine(day, time(9), tzinfo=UTC),
            answers={"wellbeing": float(wellbeing), "pain": float(pain)},
        )
    )


def _add_snapshot(session: Session, day: date, delta: float, game_type: str = "trace") -> None:
    session.add(
        TrendSnapshot(
            patient_id="p3",
            metric=f"{game_type}:all",
            day=day,
            sessions=1,
            delta=delta,
            direction="declining" if delta < -5 else "stable",
        )
    )


def _add_scored_session(session: Session, day: date) -> None:
    session.add(
        GameSession(
            patient_id="p3",
            game_type="trace",
            level=1,
            hand="right",
            started_at=datetime.combine(day, time(10), tzinfo=UTC),
            day=day,
            duration_ms=10_000,
            completed=True,
            input_device="touch",
            score=50.0,
            impairment_class="moderate",
            model_version="standin-0.1",
            features={},
            counts_for_trend=True,
        )
    )


def test_divergence_compares_latest_delta_to_normalized_weekly_index(client: TestClient) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        for offset in range(13, 6, -1):
            _add_checkin(session, day - timedelta(days=offset), 7, 3)
        for offset in range(6, -1, -1):
            _add_checkin(session, day - timedelta(days=offset), 7, 3)
        _add_snapshot(session, day - timedelta(days=1), -12.0)
        session.commit()

        result, reason = divergence(session, "p3", day)
        assert result is True
        assert reason == DIVERGENCE_FALLING_SENTENCE


def test_divergence_uses_camera_and_reports_cross_game_sentence(client: TestClient) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        for offset in range(13, 6, -1):
            _add_checkin(session, day - timedelta(days=offset), 7, 3)
        for offset in range(6, -1, -1):
            _add_checkin(session, day - timedelta(days=offset), 7, 3)
        _add_snapshot(session, day, 0.0, "trace")
        _add_snapshot(session, day, -12.0, "camera")
        session.commit()

        assert divergence(session, "p3", day) == (
            True,
            "Rezultati meritev padajo, pacient pa poroča enako ali boljše počutje.",
        )


def test_divergence_stable_results_and_worse_wellbeing(client: TestClient) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        for offset in range(13, 6, -1):
            _add_checkin(session, day - timedelta(days=offset), 8, 2)
        for offset in range(6, -1, -1):
            _add_checkin(session, day - timedelta(days=offset), 5, 2)
        _add_snapshot(session, day, 0.0)
        session.commit()

        assert divergence(session, "p3", day) == (
            True,
            "Rezultati sledenja so stabilni, pacient pa poroča slabše počutje.",
        )
        assert divergence(session, "p3", day - timedelta(days=14)) == (False, None)


def test_alert_rules_include_exact_evidence_and_combined_rule(client: TestClient) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        for offset, delta in ((4, -6.0), (3, -7.0), (2, -2.0), (1, -11.0)):
            snapshot_day = day - timedelta(days=offset)
            _add_snapshot(session, snapshot_day, delta)
            _add_scored_session(session, snapshot_day)
        # Two check-ins in each week; subjective deterioration is two points on both scales.
        for offset in (13, 11):
            _add_checkin(session, day - timedelta(days=offset), 8, 2)
        for offset in (5, 2):
            _add_checkin(session, day - timedelta(days=offset), 6, 4)
        session.commit()

        triggers = evaluate_triggers(session, "p3", day)
        by_rule = {trigger["rule"]: trigger for trigger in triggers}
        assert {"trend_drop", "subjective_drop", "both"}.issubset(by_rule)
        assert by_rule["trend_drop"]["reason"] == (
            "Rezultati sledenja so že več dni pod pacientovim izhodiščem."
        )
        assert by_rule["trend_drop"]["evidence"]["delta"] == -11.0
        assert by_rule["trend_drop"]["evidence"]["previousDeltas"] == [-2.0, -7.0, -6.0]
        assert by_rule["trend_drop"]["evidence"]["sessionIds"]
        assert by_rule["subjective_drop"]["evidence"]["wellbeingChange"] == -2.0
        assert by_rule["subjective_drop"]["evidence"]["painChange"] == 2.0
        assert by_rule["both"]["reason"] == BOTH_REASON
        assert by_rule["both"]["source"] == "game"
        assert SUBJECTIVE_CHANGE_THRESHOLD == 2.0
        selected = evaluate_alerts(session, "p3", day)
        assert selected is not None
        assert selected.rule == "both"
        assert [trigger["rule"] for trigger in selected.evidence["triggers"]] == [
            "no_data",
            "both",
            "trend_drop",
            "subjective_drop",
        ]
        assert "divergence" not in selected.evidence


def test_game_alert_rules_and_evidence_keep_games_separate(client: TestClient) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        for game_type, deltas in (
            ("trace", (-6.0, -7.0, -6.0, -12.0)),
            ("camera", (-8.0, -9.0, -8.0, -25.0)),
        ):
            for offset, delta in zip((4, 3, 2, 1), deltas, strict=True):
                _add_snapshot(session, day - timedelta(days=offset), delta, game_type)
        for offset in (13, 11):
            _add_checkin(session, day - timedelta(days=offset), 8, 2)
        for offset in (5, 2):
            _add_checkin(session, day - timedelta(days=offset), 6, 4)
        session.commit()

        triggers = evaluate_triggers(session, "p3", day)
        assert [(item["rule"], item.get("game")) for item in triggers] == [
            ("both", "camera"),
            ("both", "trace"),
            ("big_drop", "camera"),
            ("trend_drop", "camera"),
            ("trend_drop", "trace"),
            ("subjective_drop", None),
        ]
        alert = evaluate_alerts(session, "p3", day)
        assert alert is not None
        assert alert.rule == "both"
        assert alert.reason == "Padajo rezultati meritev in počutje hkrati."
        assert alert.evidence["games"] == {
            "trace": {"delta": -12.0},
            "camera": {"delta": -25.0},
        }
        assert alert.evidence["delta"] == -25.0
        assert alert.evidence["previousDeltas"] == [-8.0, -9.0, -8.0]
        assert [(item["rule"], item.get("game")) for item in alert.evidence["triggers"][-6:]] == [
            ("both", "camera"),
            ("both", "trace"),
            ("big_drop", "camera"),
            ("trend_drop", "camera"),
            ("trend_drop", "trace"),
            ("subjective_drop", None),
        ]


def test_alert_trigger_append_order_and_noop_evaluation_preserves_updated_time(
    client: TestClient,
) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        for offset, delta in ((4, -6.0), (3, -7.0), (1, -25.0)):
            _add_snapshot(session, day - timedelta(days=offset), delta)
        for offset in (13, 11):
            _add_checkin(session, day - timedelta(days=offset), 8, 2)
        for offset in (5, 2):
            _add_checkin(session, day - timedelta(days=offset), 6, 4)
        session.commit()

        alert = evaluate_alerts(session, "p3", day)
        assert alert is not None
        assert [item["rule"] for item in alert.evidence["triggers"]] == [
            "no_data",
            "both",
            "big_drop",
            "trend_drop",
            "subjective_drop",
        ]
        assert alert.evidence["missedDays"] > 0
        previous_updated = alert.updated_at
        evaluate_alerts(session, "p3", day)
        session.refresh(alert)
        assert alert.updated_at == previous_updated


def test_existing_alert_refreshes_evidence_without_appending_a_trigger(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        for existing in session.exec(
            select(Alert).where(Alert.patient_id == "p3", Alert.status != "closed")
        ).all():
            existing.status = "closed"
            existing.closed_by = "system"
            existing.closed_at = datetime.combine(day, time(12), tzinfo=UTC)
            session.add(existing)
        session.add(
            Alert(
                patient_id="p3",
                patient_name="Ivan Zupan",
                source="game",
                rule="big_drop",
                severity="red",
                status="new",
                reason=BIG_DROP_REASON,
                evidence={
                    "triggers": [
                        {
                            "rule": "big_drop",
                            "severity": "red",
                            "source": "game",
                            "day": day.isoformat(),
                            "reason": BIG_DROP_REASON,
                        }
                    ],
                    "sessionIds": [1],
                    "checkinIds": [2],
                    "delta": -25.0,
                    "wellbeingChange": -3.0,
                    "missedDays": 8,
                    "divergence": "Prejšnji stavek odstopanja.",
                },
                diverging=False,
                opened_day=day,
                created_at=datetime.combine(day, time(12), tzinfo=UTC),
                updated_at=datetime.combine(day, time(12), tzinfo=UTC),
            )
        )
        session.commit()
        existing = session.exec(
            select(Alert).where(Alert.patient_id == "p3", Alert.rule == "big_drop")
        ).one()
        previous_updated_at = existing.updated_at

        live_trigger = {
            "rule": "big_drop",
            "severity": "red",
            "source": "game",
            "day": day,
            "reason": BIG_DROP_REASON,
            "evidence": {"sessionIds": [9], "delta": -21.0, "wellbeingChange": None},
        }
        monkeypatch.setattr(alert_service, "evaluate_triggers", lambda *_: [live_trigger])
        monkeypatch.setattr(alert_service, "divergence", lambda *_: (False, None))
        result = evaluate_alerts(session, "p3", day)

        assert result is not None
        assert len(result.evidence["triggers"]) == 1
        assert result.updated_at == previous_updated_at
        assert result.evidence["sessionIds"] == [1, 9]
        assert result.evidence["checkinIds"] == [2]
        assert result.evidence["delta"] == -21.0
        assert result.evidence["wellbeingChange"] == -3.0
        assert result.evidence["missedDays"] == 8
        assert result.evidence["divergence"] is None


def test_big_drop_merges_and_escalates_acknowledged_alert(client: TestClient) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        for offset in (13, 11):
            _add_checkin(session, day - timedelta(days=offset), 8, 2)
        for offset in (5, 2):
            _add_checkin(session, day - timedelta(days=offset), 5, 2)
        session.commit()
        alert = evaluate_alerts(session, "p3", day)
        assert alert is not None
        assert alert.rule == "subjective_drop"
        alert.status = "acknowledged"
        alert.acknowledged_by = "c1"
        alert.acknowledged_at = alert.updated_at
        session.add(alert)
        session.commit()

        _add_snapshot(session, day, -25.0)
        session.commit()
        escalated = evaluate_alerts(session, "p3", day)
        assert escalated is not None
        assert escalated.rule == "big_drop"
        assert escalated.severity == "red"
        assert escalated.reason == BIG_DROP_REASON
        assert escalated.status == "new"
        assert escalated.acknowledged_by is None
        assert {trigger["rule"] for trigger in escalated.evidence["triggers"]} == {
            "no_data",
            "subjective_drop",
            "big_drop",
        }
        assert (
            len(
                session.exec(
                    select(Alert).where(Alert.patient_id == "p3", Alert.status != "closed")
                ).all()
            )
            == 1
        )


def test_closed_alert_suppresses_matching_live_rule(client: TestClient) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        _add_snapshot(session, day, -25.0)
        session.commit()
    response = client.post(
        "/api/checkins",
        json={"patientId": "p3", "wellbeing": 7, "pain": 2},
    )
    assert response.status_code == 200
    listed = client.get("/api/alerts")
    patient_alert = next(item for item in listed.json() if item["patientId"] == "p3")
    alert_id = patient_alert["id"]
    closed = client.post(
        f"/api/alerts/{alert_id}/ack",
        json={"clinicianId": "c1", "close": True, "outcome": "called_reassured"},
    )
    assert closed.status_code == 200
    with Session(database.engine) as session:
        result = evaluate_alerts(session, "p3", day)
        assert result is None
