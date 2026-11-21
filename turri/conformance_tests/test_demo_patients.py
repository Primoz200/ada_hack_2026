# conformance tests of backend:demo-patients

from __future__ import annotations

import httpx


# conformance scenario reset-seeds-ten-patients of backend:demo-patients
def test_reset_seeds_ten_patients(api: httpx.Client) -> None:
    response = api.post("/api/admin/reset")
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    result = response.json()
    assert result.get("ok") is True, f"Expected reset ok true, got {result!r}"
    assert result.get("patients") == 10, (
        f"Expected 10 seeded patients, got {result.get('patients')!r}"
    )
