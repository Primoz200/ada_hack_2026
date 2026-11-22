"""Coverage for deterministic replay of the synthetic demo stories."""

from __future__ import annotations

import math
import os
import random
from collections.abc import Generator
from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.tables import Alert, Checkin, GameSession, GameSessionRaw
from app.seed.camera import features as camera_seed_features
from app.seed.demo import seed_demo
from app.seed.stories import STORIES, rng_for
from app.seed.traces import level_features, synthetic_trace
from app.services import clock


@pytest.fixture(scope="module")
def history_engine() -> Generator[Engine, None, None]:
    """Replay once into a shared in-memory database for this test module."""
    prior_today = os.environ.get("APP_TODAY")
    prior_history = os.environ.get("APP_SEED_HISTORY")
    os.environ["APP_TODAY"] = "2026-11-21"
    os.environ["APP_SEED_HISTORY"] = "1"
    clock.clear_shift()
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        assert seed_demo(session) == 10
    yield engine
    engine.dispose()
    clock.clear_shift()
    if prior_today is None:
        os.environ.pop("APP_TODAY", None)
    else:
        os.environ["APP_TODAY"] = prior_today
    if prior_history is None:
        os.environ.pop("APP_SEED_HISTORY", None)
    else:
        os.environ["APP_SEED_HISTORY"] = prior_history


def test_camera_seed_features_are_deterministic() -> None:
    expected = {
        1: {
            "fps": 28.2,
            "detect_frac": 0.994,
            "quality_ok": 1.0,
            "n_reps": 7.0,
            "part_position": 0.685,
            "part_reps": 1.0,
            "open_level": 1.439,
            "fist_level": 0.883,
            "open_range": 0.556,
            "part_open": 0.677,
            "part_close": 0.692,
            "visibility": 1.0,
        },
        2: {
            "fps": 20.2,
            "detect_frac": 0.974,
            "quality_ok": 1.0,
            "n_reps": 5.0,
            "part_position": 0.685,
            "part_reps": 1.0,
            "top_level": 82.199,
            "rest_level": 15.085,
            "lean_deg": 2.17,
            "hike": 0.19,
            "top_visibility": 0.92,
            "part_lean_penalty": 0.0,
            "part_hike_penalty": 0.0,
        },
        3: {
            "fps": 21.8,
            "detect_frac": 0.992,
            "quality_ok": 1.0,
            "n_reps": 5.0,
            "part_position": 0.685,
            "part_reps": 1.0,
            "top_level": 1.38,
            "rest_level": -1.17,
            "lean_deg": 3.55,
            "hike": 0.209,
            "top_visibility": 0.858,
            "part_lean_penalty": 0.0,
            "part_hike_penalty": 0.0,
        },
    }
    for level, expected_features in expected.items():
        assert (
            camera_seed_features(level, 73.2, random.Random(f"p3:12:camfeat{level}"))
            == expected_features
        )


def test_demo_story_registry_preserves_camera_story_coverage() -> None:
    stories = {story.id: story for story in STORIES}
    assert set(stories) == {"p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "demo"}
    assert all(
        stories[patient_id].camera_curve is not None
        for patient_id in ("p1", "p2", "p3", "p4", "p5", "p6", "p7", "p9")
    )
    assert stories["p8"].camera_curve is None
    assert stories["demo"].camera_curve is None
    assert all(
        stories[patient_id].camera_levels == (1, 2, 3)
        for patient_id in ("p1", "p2", "p3", "p4", "p5", "p6", "p9")
    )
    assert stories["p3"].camera_noise == 0.6
    assert stories["p3"].camera_skip_prob == 0.0
    assert stories["p4"].camera_noise == 1.2
    assert stories["p6"].camera_noise == 1.0
    assert stories["p7"].camera_levels == (1,)
    assert stories["p9"].camera_skip_prob == 0.0
    assert stories["p1"].camera_curve is not None
    assert stories["p1"].camera_curve(10) == 87.5
    assert stories["p2"].camera_curve is not None
    assert stories["p2"].camera_curve(6) == pytest.approx(86 + 6 * (1 - math.exp(-1)))
    assert stories["p5"].camera_curve is not None
    assert stories["p5"].camera_curve(40) == 94.0
    assert stories["p6"].camera_curve is not None
    assert stories["p6"].camera_curve(40) == 90.0
    assert stories["p7"].camera_curve is not None
    assert stories["p7"].camera_curve(10) == 87.0
    assert stories["p9"].camera_curve is not None
    assert stories["p9"].camera_curve(10) == 87.0


def test_camera_plan_uses_per_story_noise_skip_levels_and_bad_days() -> None:
    p2 = next(story for story in STORIES if story.id == "p2")
    expected: dict[int, float] = {}
    assert p2.camera_curve is not None
    base = p2.camera_curve(16) + p2.camera_bad_days[16]
    for level in p2.camera_levels:
        if level in (2, 3) and rng_for("p2", 16, f"camskip{level}").random() < p2.camera_skip_prob:
            continue
        expected[level] = round(
            max(
                4.0,
                min(
                    100.0,
                    base
                    + {1: 2.0, 2: 0.0, 3: -3.0}[level]
                    + rng_for("p2", 16, f"cam{level}").gauss(0, p2.camera_noise),
                ),
            ),
            1,
        )
    assert p2.camera_plan(16) == expected

    p3 = next(story for story in STORIES if story.id == "p3")
    assert set(p3.camera_plan(12)) == {1, 2, 3}
    assert next(story for story in STORIES if story.id == "p7").camera_plan(1).keys() == {1}
    assert next(story for story in STORIES if story.id == "p8").camera_plan(1) == {}
    assert next(story for story in STORIES if story.id == "demo").camera_plan(1) == {}

    p2_action = p2.acks[22]
    assert p2_action == (
        True,
        "false_alarm",
        "Pogovor s pacientom: kamera je bila postavljena prenizko, roki nista bili v kadru. "
        "Navodila za postavitev ponovljena.",
    )


def test_story_entries_are_replayed_with_seeded_scores_and_metadata(history_engine: Engine) -> None:
    today = date(2026, 11, 21)
    with Session(history_engine) as session:
        checkins = list(session.exec(select(Checkin)).all())
        games = list(session.exec(select(GameSession)).all())
        raws = list(session.exec(select(GameSessionRaw)).all())
        alerts = list(session.exec(select(Alert)).all())

    assert checkins
    trace_games = [game for game in games if game.game_type == "trace"]
    camera_games = [game for game in games if game.game_type == "camera"]
    assert len(trace_games) == len(checkins) * 3
    assert camera_games
    assert len(raws) == len(games)
    assert all(game.completed and game.counts_for_trend for game in games)
    assert all(game.model_version == "standin-0.1" for game in trace_games)
    assert all(
        game.model_version == "camera-seed" and game.quality_ok is True for game in camera_games
    )
    assert all(game.score is not None and game.impairment_class is not None for game in games)
    assert all(
        set(game.features) == {"dev_mean", "duration_s", "n_pauses", "n_lifts"}
        for game in trace_games
    )
    assert all(game.day < today for game in games)
    assert all(checkin.day < today for checkin in checkins)
    assert all(game.started_at.tzinfo is not None for game in games)

    # Story dates and session times must be deterministic and grouped as specified.
    stories = {story.id: story for story in STORIES}
    first_checkin_by_patient = {
        patient_id: min(
            (checkin for checkin in checkins if checkin.patient_id == patient_id),
            key=lambda checkin: checkin.day,
        )
        for patient_id in {checkin.patient_id for checkin in checkins}
    }
    with Session(history_engine) as session:
        for checkin in first_checkin_by_patient.values():
            story = stories[checkin.patient_id]
            discharge_day = today - timedelta(days=story.discharge_ago)
            day_index = (checkin.day - discharge_day).days
            plan = story.plan(day_index)
            assert plan is not None
            expected_ratings, expected_scores, expected_camera_scores = plan
            assert checkin.answers == {
                "wellbeing": float(expected_ratings["wellbeing"]),
                "pain": float(expected_ratings["pain"]),
            }
            first_day_games = session.exec(
                select(GameSession).where(
                    GameSession.patient_id == checkin.patient_id,
                    GameSession.day == checkin.day,
                    GameSession.game_type == "trace",
                )
            ).all()
            assert {game.level: game.score for game in first_day_games} == expected_scores
            first_day_cameras = session.exec(
                select(GameSession).where(
                    GameSession.patient_id == checkin.patient_id,
                    GameSession.day == checkin.day,
                    GameSession.game_type == "camera",
                )
            ).all()
            assert {game.level: game.score for game in first_day_cameras} == expected_camera_scores
            for game in first_day_cameras:
                expected_features = camera_seed_features(
                    game.level,
                    expected_camera_scores[game.level],
                    rng_for(checkin.patient_id, day_index, f"camfeat{game.level}"),
                )
                assert game.features == expected_features
                raw = session.get(GameSessionRaw, game.id)
                assert raw is not None and raw.series == {}
                assert raw.client_meta["fpsMeasured"] == expected_features["fps"]
            for game in first_day_games:
                generated_features = level_features(
                    game.level,
                    expected_scores[game.level],
                    rng_for(checkin.patient_id, day_index, f"feat{game.level}"),
                )
                expected_features = {
                    "dev_mean": round(generated_features["mean_dev"] / 0.06, 3),
                    "duration_s": generated_features["duration_s"],
                    "n_pauses": float(
                        round(
                            generated_features["pause_rate_hz"]
                            * generated_features["duration_s"]
                            / 4
                        )
                    ),
                    "n_lifts": generated_features["lifts"],
                }
                assert game.features == expected_features
                raw = session.get(GameSessionRaw, game.id)
                assert raw is not None
                expected_duration = int(generated_features["duration_s"] * 1000)
                assert raw.series == synthetic_trace(
                    game.level,
                    generated_features["mean_dev"] * 1.4,
                    duration_ms=expected_duration,
                    lifts=int(generated_features["lifts"]),
                    seed=f"{checkin.patient_id}:{day_index}:{game.level}",
                )

        for checkin in checkins[:8]:
            patient_games = session.exec(
                select(GameSession).where(
                    GameSession.patient_id == checkin.patient_id,
                    GameSession.day == checkin.day,
                    GameSession.game_type == "trace",
                )
            ).all()
            assert len(patient_games) == 3
            patient = {story.id: story for story in STORIES}[checkin.patient_id]
            hour = 8 + sum(map(ord, checkin.patient_id)) % 9
            assert checkin.created_at == datetime.combine(
                checkin.day, time(hour - 1, 30), tzinfo=UTC
            )
            for game in patient_games:
                assert game.started_at == datetime.combine(
                    game.day, time(hour, 5 * game.level), tzinfo=UTC
                )
                assert game.input_device == patient.input_device
                raw = session.get(GameSessionRaw, game.id)
                assert raw is not None
                assert raw.client_meta["canvasW"] == (
                    360 if patient.input_device == "touch" else 480
                )
                assert raw.client_meta["devicePixelRatio"] == (
                    3 if patient.input_device == "touch" else 2
                )
                assert raw.client_meta["userAgent"] == f"seed ({patient.input_device})"

        for game in camera_games[:8]:
            raw = session.get(GameSessionRaw, game.id)
            assert raw is not None
            assert raw.series == {}
            assert raw.client_meta["inputDevice"] == "camera"
            assert raw.client_meta["videoW"] == 1280
            assert raw.client_meta["videoH"] == 720
            assert raw.client_meta["fpsMeasured"] == game.features["fps"]
            assert game.started_at.minute == 20 + 4 * game.level

    p5_closed = [
        alert for alert in alerts if alert.patient_id == "p5" and alert.closed_by == "dr. Ana Novak"
    ]
    assert p5_closed
    assert p5_closed[-1].outcome == "called_reassured"
    assert p5_closed[-1].note is not None

    p2_closed = [
        alert for alert in alerts if alert.patient_id == "p2" and alert.outcome == "false_alarm"
    ]
    assert p2_closed
    assert p2_closed[-1].closed_by == "dr. Ana Novak"
    assert p2_closed[-1].closed_at == datetime(2026, 11, 7, 12, tzinfo=UTC)
    assert p2_closed[-1].note == (
        "Pogovor s pacientom: kamera je bila postavljena prenizko, roki nista bili v kadru. "
        "Navodila za postavitev ponovljena."
    )
    assert p2_closed[-1].evidence["triggers"]
    assert all(trigger.get("game") == "camera" for trigger in p2_closed[-1].evidence["triggers"])
    assert clock.today() == today


def test_history_stops_at_yesterday_and_today_only_gets_missing_sweep(
    history_engine: Engine,
) -> None:
    today = date(2026, 11, 21)
    earliest = today - timedelta(days=max(story.discharge_ago for story in STORIES))
    with Session(history_engine) as session:
        days = [row.day for row in session.exec(select(Checkin)).all()]
        game_days = [row.day for row in session.exec(select(GameSession)).all()]
        assert min(days) == earliest + timedelta(days=1)
        assert max(days) == today - timedelta(days=1)
        assert max(game_days) == today - timedelta(days=1)
        assert all(row.day != today for row in session.exec(select(Checkin)).all())
