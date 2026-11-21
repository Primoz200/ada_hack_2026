"""Tests for missing-data alert sweeps and the clinician alert API."""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import column
from sqlmodel import Session, select

import app.db as database
import app.services.alerts as alert_service
from app.models.tables import Alert, Checkin, Patient
from app.services.alerts import sweep_missing_data_alerts


def test_missing_data_alert_requires_four_days_and_records_missed_days(
    client: TestClient,
) -> None:
    today = date(2026, 11, 21)
    with Session(database.engine) as session:
        patient = session.get(Patient, "p9")
        assert patient is not None
        patient.discharge_date = today - timedelta(days=3)
        session.add(patient)
        session.commit()
        sweep_missing_data_alerts(session, today)
        assert (
            session.exec(
                select(Alert).where(Alert.patient_id == "p9", Alert.status != "closed")
            ).first()
            is None
        )

        patient.discharge_date = today - timedelta(days=4)
        session.add(patient)
        session.commit()
        sweep_missing_data_alerts(session, today)
        alert = session.exec(
            select(Alert).where(Alert.patient_id == "p9", Alert.status != "closed")
        ).first()
        assert alert is not None
        assert alert.rule == "no_data"
        assert alert.source == "missing"
        assert alert.severity == "grey"
        assert alert.reason == "Pacient že več dni nima nobenega vnosa ali meritve."
        assert alert.evidence["missedDays"] == 4


def test_missing_sweep_only_opens_or_closes_missing_alerts(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    today = date(2026, 11, 21)
    with Session(database.engine) as session:
        grey_alert = session.exec(
            select(Alert).where(Alert.patient_id == "p3", Alert.rule == "no_data")
        ).first()
        assert grey_alert is not None
        grey_evidence = dict(grey_alert.evidence)
        grey_updated_at = grey_alert.updated_at
        session.add(
            Checkin(
                patient_id="p3",
                day=today,
                created_at=datetime.combine(today, time(9), tzinfo=UTC),
                answers={"wellbeing": 7.0, "pain": 2.0},
            )
        )

        patient = session.get(Patient, "p8")
        assert patient is not None
        patient.discharge_date = today - timedelta(days=10)
        session.add(patient)
        open_no_data = session.exec(
            select(Alert).where(Alert.patient_id == "p8", Alert.rule == "no_data")
        ).first()
        assert open_no_data is not None
        open_no_data.status = "closed"
        open_no_data.closed_by = "system"
        open_no_data.closed_at = datetime.combine(today, time(12), tzinfo=UTC)
        session.add(
            Alert(
                patient_id="p8",
                patient_name=patient.name,
                source="game",
                rule="big_drop",
                severity="red",
                status="new",
                reason="Ohranjeno opozorilo.",
                evidence={"triggers": [], "custom": "unchanged"},
                opened_day=today,
                created_at=datetime.combine(today, time(12), tzinfo=UTC),
                updated_at=datetime.combine(today, time(12), tzinfo=UTC),
            )
        )
        session.commit()
        existing = session.exec(
            select(Alert).where(Alert.patient_id == "p8", Alert.rule == "big_drop")
        ).one()
        existing_evidence = dict(existing.evidence)

        monkeypatch.setattr(
            alert_service,
            "evaluate_triggers",
            lambda *_: pytest.fail("missing-data sweep evaluated alert rules"),
        )
        sweep_missing_data_alerts(session, today)

        session.refresh(grey_alert)
        assert grey_alert.status == "closed"
        assert grey_alert.closed_by == "system"
        assert grey_alert.evidence == grey_evidence
        assert grey_alert.updated_at == grey_updated_at
        session.refresh(existing)
        assert existing.status == "new"
        assert existing.evidence == existing_evidence


def test_patient_list_runs_missing_alert_sweep(client: TestClient) -> None:
    response = client.get("/api/patients")

    assert response.status_code == 200
    result = response.json()
    assert result["today"] == "2026-11-21"
    patient = next(item for item in result["patients"] if item["id"] == "p1")
    assert patient["status"] == "no_data"
    assert patient["openAlertId"] is not None
    assert result["counters"]["noData"] > 0


def test_missing_alert_closes_automatically_after_new_checkin(client: TestClient) -> None:
    with Session(database.engine) as session:
        alert = session.exec(
            select(Alert).where(Alert.patient_id == "p3", Alert.rule == "no_data")
        ).first()
        assert alert is not None
        alert_id = alert.id
        previous_updated_at = alert.updated_at

    response = client.post(
        "/api/checkins",
        json={"patientId": "p3", "wellbeing": 7, "pain": 2},
    )
    assert response.status_code == 200
    with Session(database.engine) as session:
        closed = session.get(Alert, alert_id)
        assert closed is not None
        assert closed.status == "closed"
        assert closed.closed_by == "system"
        assert closed.outcome is None
        assert closed.closed_at is not None
        assert closed.updated_at == previous_updated_at


def test_alert_api_validation_acknowledgement_and_descending_id(client: TestClient) -> None:
    with Session(database.engine) as session:
        open_alerts = session.exec(
            select(Alert)
            .where(column("status").in_(["new", "acknowledged"]))
            .order_by(column("id"))
        ).all()
        assert len(open_alerts) >= 2
        open_alerts[0].updated_at = datetime(2030, 1, 1, tzinfo=UTC)
        open_alerts[-1].updated_at = datetime(2020, 1, 1, tzinfo=UTC)
        session.add_all(open_alerts)
        session.commit()

    listing = client.get("/api/alerts", params={"status": "open"})
    assert listing.status_code == 200
    alerts = listing.json()
    assert len(alerts) >= 2
    assert [item["id"] for item in alerts] == sorted((item["id"] for item in alerts), reverse=True)
    alert_id = alerts[0]["id"]

    missing_outcome = client.post(
        f"/api/alerts/{alert_id}/ack",
        json={"clinicianId": "c1", "close": True},
    )
    assert missing_outcome.status_code == 422
    assert missing_outcome.json() == {"detail": "Opozorila ni mogoče zapreti brez izbranega izida."}

    acknowledged = client.post(
        f"/api/alerts/{alert_id}/ack",
        json={"clinicianId": "c1", "note": "Preveriti stanje"},
    )
    assert acknowledged.status_code == 200
    ack_json = acknowledged.json()
    assert ack_json["status"] == "acknowledged"
    assert ack_json["acknowledgedBy"] == "dr. Ana Novak"
    assert ack_json["acknowledgedAt"] is not None
    assert ack_json["note"] == "Preveriti stanje"

    closed = client.post(
        f"/api/alerts/{alert_id}/ack",
        json={"clinicianId": "c1", "close": True, "outcome": "called_reassured"},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    assert closed.json()["closedBy"] == "dr. Ana Novak"

    repeated = client.post(
        f"/api/alerts/{alert_id}/ack",
        json={"clinicianId": "c1"},
    )
    assert repeated.status_code == 422
    assert repeated.json() == {"detail": "Opozorilo je že zaprto."}
    closed_alerts = client.get("/api/alerts", params={"status": "closed"}).json()
    assert [item["id"] for item in closed_alerts] == sorted(
        (item["id"] for item in closed_alerts), reverse=True
    )
    assert alert_id in [item["id"] for item in closed_alerts]


def test_alert_api_unknown_alert_and_clinician(client: TestClient) -> None:
    unknown_alert = client.post("/api/alerts/99999/ack", json={"clinicianId": "c1"})
    assert unknown_alert.status_code == 404
    assert unknown_alert.json() == {"detail": "Opozorilo ne obstaja"}

    alerts = client.get("/api/alerts").json()
    unknown_clinician = client.post(
        f"/api/alerts/{alerts[0]['id']}/ack", json={"clinicianId": "unknown"}
    )
    assert unknown_clinician.status_code == 404
    assert unknown_clinician.json() == {"detail": "Zdravnik ne obstaja"}
