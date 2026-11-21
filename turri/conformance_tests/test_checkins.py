# conformance tests of backend:checkins

from __future__ import annotations

import httpx


def reset_demo(api: httpx.Client) -> None:
    response = api.post("/api/admin/reset")
    assert response.status_code == 200, (
        f"Expected reset HTTP 200, got {response.status_code}: {response.text}"
    )


# conformance scenario store-checkin of backend:checkins
def test_store_checkin(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.post(
        "/api/checkins", json={"patientId": "p9", "wellbeing": 7, "pain": 3}
    )
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    checkin_id = response.json().get("checkinId")
    assert isinstance(checkin_id, int), (
        f"Expected integer checkinId, got {checkin_id!r}"
    )


# conformance scenario same-day-replaces of backend:checkins
def test_same_day_replaces_checkin(api: httpx.Client) -> None:
    reset_demo(api)
    first = api.post(
        "/api/checkins", json={"patientId": "p9", "wellbeing": 7, "pain": 3}
    )
    second = api.post(
        "/api/checkins", json={"patientId": "p9", "wellbeing": 8, "pain": 2}
    )
    assert first.status_code == 200, (
        f"Expected first check-in HTTP 200, got {first.status_code}: {first.text}"
    )
    assert second.status_code == 200, (
        f"Expected second check-in HTTP 200, got {second.status_code}: {second.text}"
    )
    first_id = first.json().get("checkinId")
    second_id = second.json().get("checkinId")
    assert first_id == second_id, (
        f"Expected replacement to retain id {first_id!r}, got {second_id!r}"
    )


# acceptance scenario unknown-patient of backend:checkins
def test_checkin_unknown_patient(api: httpx.Client) -> None:
    response = api.post(
        "/api/checkins", json={"patientId": "nobody", "wellbeing": 7, "pain": 3}
    )
    assert response.status_code == 404, (
        f"Expected HTTP 404 for unknown patient, got {response.status_code}"
    )


# acceptance scenario rating-out-of-range of backend:checkins
def test_checkin_rating_out_of_range(api: httpx.Client) -> None:
    response = api.post(
        "/api/checkins", json={"patientId": "p9", "wellbeing": 11, "pain": 3}
    )
    assert response.status_code == 422, (
        f"Expected HTTP 422 for out-of-range rating, got {response.status_code}"
    )
