# conformance tests of backend:meta-and-pathways

from __future__ import annotations

import httpx


# conformance scenario meta-today-and-defaults of backend:meta-and-pathways
def test_meta_today_and_defaults(api: httpx.Client) -> None:
    response = api.get("/api/meta")
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    meta = response.json()
    assert meta["today"] == "2026-11-21", (
        f"Expected fixed today, got {meta.get('today')!r}"
    )
    assert meta["syntheticData"] is True, (
        f"Expected syntheticData true, got {meta.get('syntheticData')!r}"
    )
    assert meta["defaultPatientId"] == "p3", (
        f"Expected default patient p3, got {meta.get('defaultPatientId')!r}"
    )
    assert meta["modelVersion"] == "tracer-gbm-0.1", (
        f"Expected tracer model version, got {meta.get('modelVersion')!r}"
    )
    clinicians = meta["clinicians"]
    assert len(clinicians) == 1 and clinicians[0]["id"] == "c1", (
        f"Expected one clinician with id c1, got {clinicians!r}"
    )
    expected_outcomes = {
        "called_reassured",
        "adjusted_exercises",
        "visit_moved_earlier",
        "urgent_referral",
        "unreachable",
        "false_alarm",
    }
    assert set(meta["outcomes"]) == expected_outcomes, (
        f"Expected outcome ids {expected_outcomes!r}, got {set(meta['outcomes'])!r}"
    )


# conformance scenario two-pathways of backend:meta-and-pathways
def test_two_pathways(api: httpx.Client) -> None:
    response = api.get("/api/pathways")
    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}: {response.text}"
    )
    pathways = response.json()
    assert {pathway["code"] for pathway in pathways} == {"stroke", "ctr"}, (
        f"Expected stroke and ctr pathways, got {pathways!r}"
    )
    for pathway in pathways:
        assert len(pathway["games"]) == 2, (
            f"Expected trace and camera games for {pathway['code']}, got {pathway['games']!r}"
        )
        trace, camera = pathway["games"]
        assert trace["gameType"] == "trace" and trace["levels"] == [1, 2, 3], (
            f"Expected trace levels [1, 2, 3] for {pathway['code']}, got {trace!r}"
        )
        assert trace["optionalLevels"] == [], (
            f"Expected no optional trace levels for {pathway['code']}, got {trace!r}"
        )
        assert camera["gameType"] == "camera" and camera["levels"] == [1, 2, 3], (
            f"Expected camera levels [1, 2, 3] for {pathway['code']}, got {camera!r}"
        )
        assert camera["optionalLevels"] == [2, 3], (
            f"Expected optional camera levels [2, 3] for {pathway['code']}, got {camera!r}"
        )
        question_ids = {question["id"] for question in pathway["questions"]}
        assert question_ids == {"wellbeing", "pain"}, (
            f"Expected wellbeing and pain questions for {pathway['code']}, got {question_ids!r}"
        )
