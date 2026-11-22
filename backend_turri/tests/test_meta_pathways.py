"""Unit tests for pathway and metadata HTTP endpoints."""

import pytest
from fastapi.testclient import TestClient

import app.services.scoring as scoring


def test_pathways_include_game_and_rating_configuration(client: TestClient) -> None:
    """Both recovery pathways expose their complete configured self-check."""
    response = client.get("/api/pathways")

    assert response.status_code == 200
    assert sorted(response.json(), key=lambda item: item["code"]) == [
        {
            "code": "ctr",
            "name": "Operacija karpalnega kanala",
            "frequency": "vsak dan",
            "games": [
                {
                    "gameType": "trace",
                    "title": "Sledi poti",
                    "levels": [1, 2, 3],
                    "optionalLevels": [],
                },
                {
                    "gameType": "camera",
                    "title": "Vaje s kamero",
                    "levels": [1, 2, 3],
                    "optionalLevels": [2, 3],
                },
            ],
            "questions": [
                {
                    "id": "wellbeing",
                    "text": "Kako se počutite danes?",
                    "shortLabel": "Počutje",
                    "kind": "scale",
                    "min": 1,
                    "max": 10,
                    "minLabel": "Zelo slabo",
                    "maxLabel": "Odlično",
                    "higherIsWorse": False,
                },
                {
                    "id": "pain",
                    "text": "Kako močna je bolečina?",
                    "shortLabel": "Bolečina",
                    "kind": "scale",
                    "min": 1,
                    "max": 10,
                    "minLabel": "Brez bolečine",
                    "maxLabel": "Zelo močna",
                    "higherIsWorse": True,
                },
            ],
        },
        {
            "code": "stroke",
            "name": "Možganska kap",
            "frequency": "vsak dan",
            "games": [
                {
                    "gameType": "trace",
                    "title": "Sledi poti",
                    "levels": [1, 2, 3],
                    "optionalLevels": [],
                },
                {
                    "gameType": "camera",
                    "title": "Vaje s kamero",
                    "levels": [1, 2, 3],
                    "optionalLevels": [2, 3],
                },
            ],
            "questions": [
                {
                    "id": "wellbeing",
                    "text": "Kako se počutite danes?",
                    "shortLabel": "Počutje",
                    "kind": "scale",
                    "min": 1,
                    "max": 10,
                    "minLabel": "Zelo slabo",
                    "maxLabel": "Odlično",
                    "higherIsWorse": False,
                },
                {
                    "id": "pain",
                    "text": "Kako močna je bolečina?",
                    "shortLabel": "Bolečina",
                    "kind": "scale",
                    "min": 1,
                    "max": 10,
                    "minLabel": "Brez bolečine",
                    "maxLabel": "Zelo močna",
                    "higherIsWorse": True,
                },
            ],
        },
    ]


def test_metadata_returns_today_clinician_outcomes_and_standin(client: TestClient) -> None:
    """Metadata uses the application clock and required demo constants."""
    response = client.get("/api/meta")

    assert response.status_code == 200
    assert response.json() == {
        "today": "2026-11-21",
        "syntheticData": True,
        "clinicians": [{"id": "c1", "name": "dr. Ana Novak", "role": "zdravnica"}],
        "outcomes": {
            "called_reassured": "Poklical, pomiril",
            "adjusted_exercises": "Prilagodil vaje",
            "visit_moved_earlier": "Pregled prestavljen naprej",
            "urgent_referral": "Nujna napotitev",
            "unreachable": "Nedosegljiv",
            "false_alarm": "Lažni alarm ali težava s podatki",
        },
        "modelVersion": "standin-0.1",
        "defaultPatientId": "p3",
    }


def test_metadata_reports_loaded_external_model_version(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(scoring, "_external_load_attempted", True)
    monkeypatch.setattr(scoring, "_external_scorer", lambda *args: {})
    monkeypatch.setattr(scoring, "_external_model_version", "tracer-test-2")
    monkeypatch.setattr(scoring, "_external_last_call_failed", False)

    response = client.get("/api/meta")

    assert response.status_code == 200
    assert response.json()["modelVersion"] == "tracer-test-2"
