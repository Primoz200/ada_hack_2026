"""Unit tests for daily check-in ingestion."""

from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

import app.db as database
import app.services.clock as clock
from app.models.tables import Checkin
from app.services.ingest import ingest_checkin


def test_checkin_is_stored_for_today_with_rating_answers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid request stores today's ratings and returns its generated identifier."""
    created_at = datetime(2026, 11, 21, 9, 30, tzinfo=UTC)
    monkeypatch.setattr(clock, "now", lambda: created_at)

    response = client.post(
        "/api/checkins",
        json={"patientId": "p3", "wellbeing": 8, "pain": 3},
    )

    assert response.status_code == 200
    checkin_id = response.json()["checkinId"]
    assert isinstance(checkin_id, int)
    with Session(database.engine) as session:
        checkin = session.get(Checkin, checkin_id)
        assert checkin is not None
        assert checkin.patient_id == "p3"
        assert checkin.day == date(2026, 11, 21)
        assert checkin.created_at == created_at
        assert checkin.answers == {"wellbeing": 8, "pain": 3}


def test_ingest_accepts_seed_date_and_time_overrides(client: TestClient) -> None:
    """Seed callers can place a check-in on a deterministic historical date and time."""
    override_day = date(2026, 11, 18)
    override_time = datetime(2026, 11, 18, 8, 15, tzinfo=UTC)
    with Session(database.engine) as session:
        checkin = ingest_checkin(
            session,
            patient_id="p3",
            wellbeing=7,
            pain=4,
            day=override_day,
            created_at=override_time,
        )

    assert checkin.id is not None
    with Session(database.engine) as session:
        stored = session.get(Checkin, checkin.id)
        assert stored is not None
        assert stored.day == override_day
        assert stored.created_at == override_time


def test_second_same_day_checkin_replaces_answers_and_time_but_keeps_id(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The latest same-day check-in replaces the first row without changing its id."""
    timestamps = iter(
        [
            datetime(2026, 11, 21, 9, 30, tzinfo=UTC),
            datetime(2026, 11, 21, 15, 45, tzinfo=UTC),
        ]
    )
    monkeypatch.setattr(clock, "now", lambda: next(timestamps))
    first_response = client.post(
        "/api/checkins",
        json={"patientId": "p3", "wellbeing": 8, "pain": 3},
    )
    second_response = client.post(
        "/api/checkins",
        json={"patientId": "p3", "wellbeing": 5, "pain": 7},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    checkin_id = first_response.json()["checkinId"]
    assert second_response.json() == {"checkinId": checkin_id}
    with Session(database.engine) as session:
        checkins = list(session.exec(select(Checkin).where(Checkin.patient_id == "p3")).all())
        assert len(checkins) == 1
        assert checkins[0].id == checkin_id
        assert checkins[0].answers == {"wellbeing": 5, "pain": 7}
        assert checkins[0].created_at == datetime(2026, 11, 21, 15, 45, tzinfo=UTC)


def test_unknown_patient_returns_not_found(client: TestClient) -> None:
    """An unknown patient receives the required Slovenian 404 response."""
    response = client.post(
        "/api/checkins",
        json={"patientId": "missing", "wellbeing": 5, "pain": 5},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Pacient ne obstaja"}


@pytest.mark.parametrize("rating_field", ["wellbeing", "pain"])
@pytest.mark.parametrize("rating", [0, 11, 1.5, True])
def test_ratings_outside_integer_scale_are_rejected(
    client: TestClient, rating_field: str, rating: object
) -> None:
    """Both ratings must be integer values from one through ten."""
    payload: dict[str, object] = {"patientId": "p3", "wellbeing": 5, "pain": 5}
    payload[rating_field] = rating
    response = client.post("/api/checkins", json=payload)

    assert response.status_code == 422
