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
    assert step_ids == [
        "ratings",
        "trace:1",
        "trace:2",
        "trace:3",
        "camera:1",
        "camera:2",
        "camera:3",
    ], f"Expected ratings, trace and camera steps in order, got {step_ids!r}"
    camera_steps = {
        step["id"]: step for step in steps if step["id"].startswith("camera:")
    }
    assert camera_steps["camera:1"]["skippable"] is False, (
        f"Expected camera:1 not skippable, got {camera_steps['camera:1']!r}"
    )
    assert camera_steps["camera:1"]["durationS"] == 21, (
        f"Expected camera:1 durationS 21, got {camera_steps['camera:1']!r}"
    )
    assert camera_steps["camera:2"]["skippable"] is True, (
        f"Expected camera:2 skippable, got {camera_steps['camera:2']!r}"
    )
    assert camera_steps["camera:3"]["skippable"] is True, (
        f"Expected camera:3 skippable, got {camera_steps['camera:3']!r}"
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


# conformance scenario camera-never-blocks of backend:patient-home
def test_camera_never_blocks_selfcheck(api: httpx.Client) -> None:
    reset_demo(api)
    checkin_response = api.post(
        "/api/checkins",
        json={"patientId": "p3", "wellbeing": 7, "pain": 3},
    )
    assert checkin_response.status_code == 200, (
        f"Expected check-in HTTP 200, got {checkin_response.status_code}: {checkin_response.text}"
    )
    series = {
        "targetX": [0.1, 0.9],
        "targetY": [0.5, 0.5],
        "x": [0.1, 0.9],
        "y": [0.5, 0.5],
        "t": [0.0, 10000.0],
    }
    for level in (1, 2, 3):
        session_response = api.post(
            "/api/sessions",
            json={
                "patientId": "p3",
                "gameType": "trace",
                "level": level,
                "hand": "right",
                "startedAt": "2026-11-21T10:00:00Z",
                "durationMs": 10000,
                "completed": True,
                "abortReason": None,
                "series": series,
                "clientMeta": {
                    "inputDevice": "touch",
                    "canvasW": 360,
                    "canvasH": 360,
                    "devicePixelRatio": 3,
                    "userAgent": "conformance test",
                },
            },
        )
        assert session_response.status_code == 200, (
            f"Expected trace level {level} HTTP 200, got "
            f"{session_response.status_code}: {session_response.text}"
        )

    home_response = api.get("/api/patients/p3/home")
    assert home_response.status_code == 200, (
        f"Expected home HTTP 200, got {home_response.status_code}: {home_response.text}"
    )
    home = home_response.json()
    assert home.get("selfcheckDoneToday") is True, (
        f"Expected non-camera self-check complete without camera sessions, got {home!r}"
    )
    camera_steps = [step for step in home["steps"] if step["id"].startswith("camera:")]
    assert camera_steps and all(step["done"] is False for step in camera_steps), (
        f"Expected camera steps still incomplete, got {camera_steps!r}"
    )


# acceptance scenario unknown-patient-home of backend:patient-home
def test_unknown_patient_home(api: httpx.Client) -> None:
    response = api.get("/api/patients/nobody/home")
    assert response.status_code == 404, (
        f"Expected HTTP 404 for unknown patient, got {response.status_code}"
    )
