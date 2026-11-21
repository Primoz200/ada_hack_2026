# conformance tests of backend:patient-home

from __future__ import annotations

import httpx


def reset_demo(api: httpx.Client) -> None:
    response = api.post("/api/admin/reset")
    assert response.status_code == 200, (
        f"Expected reset HTTP 200, got {response.status_code}: {response.text}"
    )


# conformance scenario selfcheck-steps of backend:patient-home
def test_selfcheck_steps(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.get("/api/patients/p3/home")
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    steps = response.json().get("steps", [])
    step_ids = [step.get("id") for step in steps]
    assert step_ids == ["ratings", "trace:1", "trace:2", "trace:3"], (
        f"Expected ratings and three trace steps in order, got {step_ids!r}"
    )

    checkin_response = api.post(
        "/api/checkins",
        json={"patientId": "p3", "wellbeing": 7, "pain": 3},
    )
    assert checkin_response.status_code == 200, (
        f"Expected check-in HTTP 200, got {checkin_response.status_code}: {checkin_response.text}"
    )
    updated_response = api.get("/api/patients/p3/home")
    assert updated_response.status_code == 200, (
        f"Expected updated home HTTP 200, got {updated_response.status_code}: {updated_response.text}"
    )
    updated_steps = updated_response.json().get("steps", [])
    ratings_step = next(
        (step for step in updated_steps if step.get("id") == "ratings"), None
    )
    assert ratings_step is not None and ratings_step.get("done") is True, (
        f"Expected today's ratings step done after check-in, got {ratings_step!r}"
    )


# acceptance scenario unknown-patient-home of backend:patient-home
def test_unknown_patient_home(api: httpx.Client) -> None:
    response = api.get("/api/patients/nobody/home")
    assert response.status_code == 404, (
        f"Expected HTTP 404 for unknown patient, got {response.status_code}"
    )
