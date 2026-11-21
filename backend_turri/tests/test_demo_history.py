"""Coverage for deterministic replay of the synthetic demo stories."""

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.tables import Alert, Checkin, GameSession, GameSessionRaw
from app.seed.demo import seed_demo
from app.seed.stories import STORIES, rng_for
from app.seed.trace_generator import level_features, synthetic_trace
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


def test_story_entries_are_replayed_with_seeded_scores_and_metadata(history_engine: Engine) -> None:
    today = date(2026, 11, 21)
    with Session(history_engine) as session:
        checkins = list(session.exec(select(Checkin)).all())
        games = list(session.exec(select(GameSession)).all())
        raws = list(session.exec(select(GameSessionRaw)).all())
        alerts = list(session.exec(select(Alert)).all())

    assert checkins
    assert len(games) == len(checkins) * 3
    assert len(raws) == len(games)
    assert all(game.completed and game.counts_for_trend for game in games)
    assert all(game.model_version == "standin-0.1" for game in games)
    assert all(game.score is not None and game.impairment_class is not None for game in games)
    assert all(
        set(game.features) == {"dev_mean", "duration_s", "n_pauses", "n_lifts"} for game in games
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
            expected_ratings, expected_scores = plan
            assert checkin.answers == {
                "wellbeing": float(expected_ratings["wellbeing"]),
                "pain": float(expected_ratings["pain"]),
            }
            first_day_games = session.exec(
                select(GameSession).where(
                    GameSession.patient_id == checkin.patient_id,
                    GameSession.day == checkin.day,
                )
            ).all()
            assert {game.level: game.score for game in first_day_games} == expected_scores
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

    p5_closed = [
        alert for alert in alerts if alert.patient_id == "p5" and alert.closed_by == "dr. Ana Novak"
    ]
    assert p5_closed
    assert p5_closed[-1].outcome == "called_reassured"
    assert p5_closed[-1].note is not None
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
