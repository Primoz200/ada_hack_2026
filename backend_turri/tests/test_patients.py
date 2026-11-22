"""Patient triage, detail, and timeline API tests."""

from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

import app.db as database
from app.models.tables import Alert, Checkin, GameSession, Patient, TrendSnapshot


def _add_patient_history() -> None:
    with Session(database.engine) as session:
        session.add(
            GameSession(
                patient_id="p3",
                game_type="trace",
                level=1,
                hand="right",
                started_at=datetime(2026, 11, 21, 10, tzinfo=UTC),
                day=date(2026, 11, 21),
                duration_ms=12_000,
                completed=True,
                input_device="touch",
                score=75.0,
                impairment_class="mild",
                model_version="standin-0.1",
                features={"example": 1.0},
                counts_for_trend=True,
            )
        )
        session.add(
            Checkin(
                patient_id="p3",
                day=date(2026, 11, 21),
                created_at=datetime(2026, 11, 21, 9, tzinfo=UTC),
                answers={"wellbeing": 8, "pain": 2},
            )
        )
        session.add(
            TrendSnapshot(
                patient_id="p3",
                metric="trace:all",
                day=date(2026, 11, 21),
                sessions=1,
                delta=2.5,
                direction="stable",
            )
        )
        session.commit()


def test_patient_list_triage_order_counters_and_sparklines(client: TestClient) -> None:
    _add_patient_history()
    response = client.get("/api/patients")

    assert response.status_code == 200
    result = response.json()
    patients = result["patients"]
    urgency = {"red": 0, "yellow": 1, "no_data": 2, "insufficient_data": 3, "stable": 4}
    assert [urgency[patient["status"]] for patient in patients] == sorted(
        urgency[patient["status"]] for patient in patients
    )
    assert result["counters"]["total"] == len(patients) == 10
    assert result["counters"]["needsAttention"] == sum(
        patient["status"] in {"red", "yellow"} for patient in patients
    )
    assert result["counters"]["noData"] == sum(
        patient["status"] == "no_data" for patient in patients
    )
    assert result["counters"]["stable"] == sum(
        patient["status"] in {"stable", "insufficient_data"} for patient in patients
    )
    p3 = next(patient for patient in patients if patient["id"] == "p3")
    assert p3["status"] == "stable"
    assert p3["reason"] == "Brez posebnosti; rezultati so blizu izhodišča."
    p1 = next(patient for patient in patients if patient["id"] == "p1")
    assert p1["status"] == "no_data"
    assert p1["reason"] == "Brez vnosa že 28 dni."
    p9 = next(patient for patient in patients if patient["id"] == "p9")
    assert p9["status"] == "insufficient_data"
    assert p9["reason"] == "Premalo sej za izhodišče (0 od 4)."
    assert p3["gameSparkline"]
    assert len(p3["gameSparkline"]) <= 21
    assert p3["wellbeingSparkline"]
    assert len(p3["wellbeingSparkline"]) <= 21
    assert all(point["value"] is not None for point in p3["gameSparkline"])
    assert all(point["value"] is not None for point in p3["wellbeingSparkline"])


def test_patient_detail_has_pathway_alert_and_activity_summary(client: TestClient) -> None:
    _add_patient_history()
    response = client.get("/api/patients/p3")

    assert response.status_code == 200
    result = response.json()
    assert result["id"] == "p3"
    assert result["birthYear"] == 1955
    assert result["pathway"]["code"] == "stroke"
    assert result["daysSinceDischarge"] == 40
    assert result["daysToNextVisit"] == 30
    assert result["status"] == "stable"
    assert result["reason"] == "Brez posebnosti; rezultati so blizu izhodišča."
    assert result["summary"]["nSessions"] == 1
    assert result["summary"]["nCheckins"] > 0
    assert result["summary"]["lastSessionDay"] is not None
    assert result["summary"]["lastCheckinDay"] == "2026-11-21"
    assert result["summary"]["combinedDelta"] == 2.5
    assert result["summary"]["combinedDirection"] == "stable"
    assert isinstance(result["diverging"], bool)
    assert result["openAlert"] is None

    alert_response = client.get("/api/patients/p1")
    assert alert_response.status_code == 200
    alert_patient = alert_response.json()
    assert alert_patient["status"] == "no_data"
    assert alert_patient["reason"] == "Brez vnosa že 28 dni."
    assert alert_patient["openAlert"]["severity"] == "grey"
    assert alert_patient["openAlert"]["patientId"] == "p1"


def test_patient_timeline_returns_ordered_non_raw_history(client: TestClient) -> None:
    _add_patient_history()
    response = client.get("/api/patients/p3/timeline")

    assert response.status_code == 200
    result = response.json()
    assert result["patientId"] == "p3"
    assert result["today"] == "2026-11-21"
    assert result["sessions"]
    assert result["checkins"]
    assert result["trends"]
    assert result["alerts"]
    assert [alert["id"] for alert in result["alerts"]] == sorted(
        alert["id"] for alert in result["alerts"]
    )
    assert [session["startedAt"] for session in result["sessions"]] == sorted(
        session["startedAt"] for session in result["sessions"]
    )
    assert [checkin["day"] for checkin in result["checkins"]] == sorted(
        checkin["day"] for checkin in result["checkins"]
    )
    assert [trend["day"] for trend in result["trends"]] == sorted(
        trend["day"] for trend in result["trends"]
    )
    assert result["sessions"][0]["startedAt"].endswith("Z")
    assert result["checkins"][0]["createdAt"].endswith("Z")
    assert "series" not in result["sessions"][0]
    assert "clientMeta" not in result["sessions"][0]


def test_patient_home_builds_daily_steps_and_last_entry(client: TestClient) -> None:
    with Session(database.engine) as session:
        session.add(
            Patient(
                id="home-test",
                name="Preizkusni pacient",
                birth_year=1970,
                pathway_code="stroke",
                side="left",
                sort_order=101,
                is_demo=False,
                discharge_date=date(2026, 11, 1),
            )
        )
        session.add(
            Checkin(
                patient_id="home-test",
                day=date(2026, 11, 21),
                created_at=datetime(2026, 11, 21, 9, tzinfo=UTC),
                answers={"wellbeing": 7, "pain": 3},
            )
        )
        session.add(
            GameSession(
                patient_id="home-test",
                game_type="trace",
                level=1,
                hand="left",
                started_at=datetime(2026, 11, 21, 10, tzinfo=UTC),
                day=date(2026, 11, 21),
                duration_ms=1000,
                completed=True,
                input_device="touch",
                score=80,
                counts_for_trend=True,
            )
        )
        session.add(
            GameSession(
                patient_id="home-test",
                game_type="trace",
                level=2,
                hand="left",
                started_at=datetime(2026, 11, 21, 11, tzinfo=UTC),
                day=date(2026, 11, 21),
                duration_ms=1000,
                completed=False,
                input_device="touch",
            )
        )
        session.commit()

    response = client.get("/api/patients/home-test/home")
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "Preizkusni pacient"
    assert result["pathwayCode"] == "stroke"
    assert result["pathwayName"] == "Možganska kap"
    assert result["hand"] == "left"
    assert result["today"] == "2026-11-21"
    assert result["patientId"] == "home-test"
    assert result["selfcheckDoneToday"] is False
    assert result["lastSelfcheckDay"] == "2026-11-21"
    assert [step["id"] for step in result["steps"]] == [
        "ratings",
        "trace:1",
        "trace:2",
        "trace:3",
        "camera:1",
        "camera:2",
        "camera:3",
    ]
    assert result["steps"][0] == {
        "id": "ratings",
        "kind": "ratings",
        "title": "Počutje in bolečina",
        "gameType": None,
        "level": None,
        "done": True,
        "skippable": False,
        "durationS": None,
    }
    assert result["steps"][1] == {
        "id": "trace:1",
        "kind": "game",
        "title": "Ravna črta",
        "gameType": "trace",
        "level": 1,
        "done": True,
        "skippable": False,
        "durationS": None,
    }
    assert [(step["id"], step["skippable"], step["durationS"]) for step in result["steps"][4:]] == [
        ("camera:1", False, None),
        ("camera:2", True, None),
        ("camera:3", True, None),
    ]


def test_feedback_without_snapshots_uses_first_day_message(client: TestClient) -> None:
    with Session(database.engine) as session:
        session.add(
            Patient(
                id="first-feedback",
                name="Nov pacient",
                birth_year=1970,
                pathway_code="stroke",
                side="right",
                sort_order=103,
                is_demo=False,
                discharge_date=date(2026, 11, 21),
            )
        )
        session.commit()

    response = client.get("/api/patients/first-feedback/selfcheck/summary")
    assert response.status_code == 200
    feedback = response.json()
    assert set(feedback) == {
        "tone",
        "trend",
        "title",
        "text",
        "patientId",
        "day",
        "levelsDone",
        "levelsTotal",
        "games",
    }
    assert feedback["patientId"] == "first-feedback"
    assert feedback["levelsDone"] == 0
    assert feedback["levelsTotal"] == 6
    assert feedback["games"] == []
    assert {key: feedback[key] for key in ("tone", "trend", "title", "text")} == {
        "tone": "first",
        "trend": "unknown",
        "title": "Hvala, samopregled je opravljen",
        "text": "Prvi rezultati nam pomagajo spoznati, kaj je za vas običajno.",
    }


def _add_feedback_patient() -> None:
    with Session(database.engine) as session:
        session.add(
            Patient(
                id="feedback-test",
                name="Povratni pacient",
                birth_year=1970,
                pathway_code="stroke",
                side="right",
                sort_order=102,
                is_demo=False,
                discharge_date=date(2026, 11, 1),
            )
        )
        for index, delta in enumerate((-10, -8, -7, -6, -4, -4)):
            session.add(
                TrendSnapshot(
                    patient_id="feedback-test",
                    metric="trace:all",
                    day=date(2026, 11, 16) + timedelta(days=index),
                    sessions=index + 1,
                    delta=delta,
                    direction="stable",
                )
            )
        for offset, answers in (
            (0, {"wellbeing": 7.0, "pain": 2.0}),
            (2, {"wellbeing": 8.0, "pain": 1.0}),
        ):
            checkin_day = date(2026, 11, 21) - timedelta(days=offset)
            session.add(
                Checkin(
                    patient_id="feedback-test",
                    day=checkin_day,
                    created_at=datetime.combine(checkin_day, datetime.min.time(), tzinfo=UTC),
                    answers=answers,
                )
            )
        session.add(
            GameSession(
                patient_id="feedback-test",
                game_type="trace",
                level=1,
                hand="right",
                started_at=datetime(2026, 11, 20, 10, tzinfo=UTC),
                day=date(2026, 11, 20),
                duration_ms=1000,
                completed=False,
                input_device="touch",
            )
        )
        session.add(
            Alert(
                patient_id="feedback-test",
                patient_name="Povratni pacient",
                source="checkin",
                rule="subjective_drop",
                severity="yellow",
                status="acknowledged",
                acknowledged_by="dr. Ana Novak",
                acknowledged_at=datetime(2026, 11, 21, 8, tzinfo=UTC),
                reason="Testno opozorilo.",
                evidence={"triggers": [{"rule": "trend_drop"}]},
                diverging=False,
                opened_day=date(2026, 11, 20),
                created_at=datetime(2026, 11, 20, tzinfo=UTC),
                updated_at=datetime(2026, 11, 20, tzinfo=UTC),
            )
        )
        session.commit()


def test_feedback_and_selfcheck_summary_use_points_and_open_game_alert(client: TestClient) -> None:
    _add_feedback_patient()
    response = client.get("/api/patients/feedback-test/selfcheck/summary")
    assert response.status_code == 200
    result = response.json()
    assert set(result) == {
        "tone",
        "trend",
        "title",
        "text",
        "patientId",
        "day",
        "levelsDone",
        "levelsTotal",
        "games",
    }
    assert result["patientId"] == "feedback-test"
    assert result["day"] == "2026-11-21"
    assert result["levelsDone"] == 0
    assert result["levelsTotal"] == 6
    assert len(result["games"]) == 1
    assert result["games"][0]["gameType"] == "trace"
    assert result["games"][0]["title"] == "Sledenje"
    assert result["games"][0]["trend"] == "declining"
    assert result["games"][0]["personalBestDay"] == "2026-11-21"
    assert len(result["games"][0]["points"]) == 6
    assert set(result["games"][0]) == {
        "gameType",
        "title",
        "trend",
        "points",
        "personalBestDay",
    }
    assert result["games"][0]["points"][-1] == {
        "day": "2026-11-21",
        "value": -4.0,
        "label": "usual",
    }
    assert {key: result[key] for key in ("tone", "trend", "title", "text")} == {
        "tone": "better",
        "trend": "declining",
        "title": "Danes je šlo bolje",
        "text": (
            "Danes je šlo bolje, zadnje dni pa gre nekoliko slabše kot prej. "
            "Vaš zdravnik ima vpogled v rezultate."
        ),
    }
    assert "value" not in result


def test_feedback_weights_game_histories_separately(client: TestClient) -> None:
    _add_feedback_patient()
    with Session(database.engine) as session:
        for index in range(6):
            session.add(
                TrendSnapshot(
                    patient_id="feedback-test",
                    metric="camera:all",
                    day=date(2026, 11, 16) + timedelta(days=index),
                    sessions=index + 1,
                    delta=2.0,
                    direction="stable",
                )
            )
        session.commit()

    response = client.get("/api/patients/feedback-test/progress")
    assert response.status_code == 200
    result = response.json()
    assert [game["gameType"] for game in result["games"]] == ["trace", "camera"]
    assert result["tone"] == "similar"
    assert result["trend"] == "declining"
    assert result["games"][0]["trend"] == "declining"
    assert result["games"][1]["trend"] == "stable"
    assert len(result["games"][1]["points"]) == 6
    assert result["games"][1]["personalBestDay"] == "2026-11-21"


def test_patient_progress_returns_all_history_and_tie_breaks_best_day_late(
    client: TestClient,
) -> None:
    _add_feedback_patient()
    response = client.get("/api/patients/feedback-test/progress")
    assert response.status_code == 200
    result = response.json()
    assert set(result) == {
        "tone",
        "trend",
        "title",
        "text",
        "patientId",
        "games",
        "ratings",
        "weekDone",
        "weekGoal",
        "clinicianReviewedAt",
    }
    assert result["patientId"] == "feedback-test"
    assert len(result["games"]) == 1
    assert result["games"][0]["gameType"] == "trace"
    assert len(result["games"][0]["points"]) == 6
    assert result["games"][0]["points"][-1]["value"] == -4.0
    assert result["games"][0]["personalBestDay"] == "2026-11-21"
    assert result["ratings"] == [
        {"day": "2026-11-19", "wellbeing": 8.0, "pain": 1.0},
        {"day": "2026-11-21", "wellbeing": 7.0, "pain": 2.0},
    ]
    assert result["weekDone"] == 3
    assert result["weekGoal"] == 5
    assert result["clinicianReviewedAt"] == "2026-11-21T08:00:00Z"
    assert result["trend"] == "declining"


def test_unknown_patient_is_not_found_on_every_patient_path(client: TestClient) -> None:
    for path in (
        "/api/patients/unknown",
        "/api/patients/unknown/timeline",
        "/api/patients/unknown/home",
        "/api/patients/unknown/selfcheck/summary",
        "/api/patients/unknown/progress",
    ):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json() == {"detail": "Pacient ne obstaja"}
