"""Unit tests for seeded demo records and reset behavior."""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, select

import app.db as database
import app.services.clock as clock
from app.models.tables import Checkin, Clinician, GameSession, Pathway, Patient


def test_seeded_demo_has_pathways_clinician_and_ten_story_patients(
    client: TestClient,
) -> None:
    """Startup seed creates the pathways, clinician, and story-derived patient dates."""
    with Session(database.engine) as session:
        pathways = list(session.exec(select(Pathway)).all())
        clinicians = list(session.exec(select(Clinician)).all())
        patients = list(session.exec(select(Patient).order_by(text("sort_order"))).all())
        assert session.exec(select(Checkin.id)).first() is None
        assert session.exec(select(GameSession.id)).first() is None

    assert {pathway.code: pathway.name for pathway in pathways} == {
        "stroke": "Možganska kap",
        "ctr": "Operacija karpalnega kanala",
    }
    assert [(clinician.id, clinician.name, clinician.role) for clinician in clinicians] == [
        ("c1", "dr. Ana Novak", "zdravnica")
    ]
    assert len(patients) == 10
    assert [patient.id for patient in patients] == [
        "p1",
        "p2",
        "p3",
        "p4",
        "p5",
        "p6",
        "p7",
        "p8",
        "p9",
        "demo",
    ]
    assert [
        (patient.name, patient.birth_year, patient.pathway_code, patient.side)
        for patient in patients
    ] == [
        ("Marija Kovač", 1952, "stroke", "right"),
        ("Franc Horvat", 1948, "stroke", "left"),
        ("Ivan Zupan", 1955, "stroke", "right"),
        ("Ana Potočnik", 1961, "ctr", "right"),
        ("Marta Novak", 1957, "ctr", "left"),
        ("Jože Kranjc", 1950, "stroke", "right"),
        ("Silvester Mlakar", 1946, "stroke", "left"),
        ("Tone Vidmar", 1953, "stroke", "right"),
        ("Nina Božič", 1969, "ctr", "right"),
        ("Janez Demo", 1958, "stroke", "right"),
    ]
    assert [patient.sort_order for patient in patients] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 99]
    assert [patient.is_demo for patient in patients] == [False] * 9 + [True]
    today = date(2026, 11, 21)
    expected_discharge_offsets = [28, 36, 40, 35, 28, 30, 15, 30, 3, 21]
    expected_visit_offsets = [14, 9, 30, None, 10, 8, 13, 12, 25, 20]
    assert [patient.discharge_date for patient in patients] == [
        today - timedelta(days=days) for days in expected_discharge_offsets
    ]
    assert [
        (patient.next_visit_date - today).days if patient.next_visit_date else None
        for patient in patients
    ] == expected_visit_offsets


def test_reset_recreates_demo_and_clears_clock_shift(client: TestClient) -> None:
    """Admin reset restores all ten seed patients and clears date adjustments."""
    clock.shift_days(5)
    assert client.get("/api/meta").json()["today"] == "2026-11-26"

    response = client.post("/api/admin/reset")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "patients": 10}
    assert client.get("/api/meta").json()["today"] == "2026-11-21"
    with Session(database.engine) as session:
        assert len(session.exec(select(Patient.id)).all()) == 10
