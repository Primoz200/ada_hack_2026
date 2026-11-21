# conformance tests of backend:patient-list

from __future__ import annotations

import httpx


def reset_demo(api: httpx.Client) -> None:
    response = api.post("/api/admin/reset")
    assert response.status_code == 200, (
        f"Expected reset HTTP 200, got {response.status_code}: {response.text}"
    )


# conformance scenario list-all-patients of backend:patient-list
def test_list_all_patients(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.get("/api/patients")
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    result = response.json()
    assert result.get("today") == "2026-11-21", (
        f"Expected today 2026-11-21, got {result.get('today')!r}"
    )
    patients = result.get("patients")
    assert isinstance(patients, list) and len(patients) == 10, (
        f"Expected ten patients, got {patients!r}"
    )
    counters = result.get("counters", {})
    assert counters.get("total") == 10, (
        f"Expected total counter 10, got {counters.get('total')!r}"
    )
    status_sum = (
        counters.get("needsAttention", 0)
        + counters.get("noData", 0)
        + counters.get("stable", 0)
    )
    assert status_sum == 10, f"Expected triage counters to sum to 10, got {counters!r}"


# conformance scenario sorted-by-urgency of backend:patient-list
def test_patients_sorted_by_urgency(api: httpx.Client) -> None:
    reset_demo(api)
    response = api.get("/api/patients")
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    patients = response.json().get("patients", [])
    priority = {
        "red": 0,
        "yellow": 1,
        "no_data": 2,
        "insufficient_data": 3,
        "stable": 4,
    }
    statuses = [patient.get("status") for patient in patients]
    assert all(status in priority for status in statuses), (
        f"Expected recognized triage statuses, got {statuses!r}"
    )
    ranks = [priority[status] for status in statuses]
    assert ranks == sorted(ranks), (
        f"Expected urgency order red/yellow/no_data/insufficient_data/stable, got {statuses!r}"
    )
