"""Unit tests for per-level and combined trend snapshots."""

from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

import app.db as database
from app.models.tables import GameSession, TrendSnapshot
from app.services.trends import recompute_trend_snapshots


def _add_score(session: Session, *, level: int, score: float, day: date, minute: int) -> None:
    session.add(
        GameSession(
            patient_id="p3",
            game_type="trace",
            level=level,
            hand="right",
            started_at=datetime(2026, 11, day.day, 9, minute, tzinfo=UTC),
            day=day,
            duration_ms=10_000,
            completed=True,
            input_device="touch",
            score=score,
            impairment_class="moderate",
            model_version="standin-0.1",
            features={},
            counts_for_trend=True,
        )
    )


def test_snapshots_use_practice_exclusion_and_latest_unplayed_level(
    client: TestClient,
) -> None:
    days = [date(2026, 11, day) for day in (18, 19, 20, 21)]
    with Session(database.engine) as session:
        # Level 1 played today: practice 50, then baseline 60/70/80.
        for day, score, minute in zip(days, (50.0, 60.0, 70.0, 80.0), range(4), strict=True):
            _add_score(session, level=1, score=score, day=day, minute=minute)
        # Level 2 has its latest session yesterday; its historical delta still contributes.
        for day, score, minute in (
            (days[0], 20.0, 10),
            (days[1], 20.0, 11),
            (days[2], 20.0, 12),
            (days[2], 30.0, 13),
        ):
            _add_score(session, level=2, score=score, day=day, minute=minute)
        session.commit()

        recompute_trend_snapshots(session, "p3", "trace", days[-1])
        level_one = session.exec(
            select(TrendSnapshot).where(TrendSnapshot.metric == "trace:1")
        ).one()
        combined = session.exec(
            select(TrendSnapshot).where(TrendSnapshot.metric == "trace:all")
        ).one()

        assert level_one.sessions == 4
        assert level_one.baseline == 70.0
        assert level_one.ewma == pytest.approx(68.1)
        assert level_one.delta == pytest.approx(-1.9)
        assert level_one.direction == "stable"
        assert combined.sessions == 4
        assert combined.baseline is None
        assert combined.ewma is None
        assert combined.slope is None
        assert combined.delta_percent is None
        # Level 1 delta is -1.9; level 2 delta is 3.0 and was not played today.
        assert combined.delta == pytest.approx(0.55)
        assert combined.direction == "stable"
        assert (
            session.exec(select(TrendSnapshot).where(TrendSnapshot.metric == "trace:2")).first()
            is None
        )


def test_trend_values_are_empty_until_baseline_exists(client: TestClient) -> None:
    day = date(2026, 11, 21)
    with Session(database.engine) as session:
        for index, score in enumerate((80.0, 70.0, 60.0)):
            _add_score(session, level=1, score=score, day=day, minute=index)
        session.commit()
        recompute_trend_snapshots(session, "p3", "trace", day)
        snapshot = session.exec(
            select(TrendSnapshot).where(
                TrendSnapshot.patient_id == "p3",
                TrendSnapshot.metric == "trace:1",
                TrendSnapshot.day == day,
            )
        ).one()
        assert snapshot.sessions == 3
        assert snapshot.baseline is None
        assert snapshot.ewma is None
        assert snapshot.slope is None
        assert snapshot.delta is None
        assert snapshot.delta_percent is None
        assert snapshot.direction == "insufficient_data"


def test_trend_snapshot_upsert_does_not_duplicate_daily_rows(client: TestClient) -> None:
    with Session(database.engine) as session:
        for index, score in enumerate((80.0, 70.0, 70.0, 70.0)):
            _add_score(
                session,
                level=1,
                score=score,
                day=date(2026, 11, 21),
                minute=index,
            )
        session.commit()
        recompute_trend_snapshots(session, "p3", "trace", date(2026, 11, 21))
        recompute_trend_snapshots(session, "p3", "trace", date(2026, 11, 21))
        rows = list(
            session.exec(
                select(TrendSnapshot).where(
                    TrendSnapshot.patient_id == "p3", TrendSnapshot.day == date(2026, 11, 21)
                )
            ).all()
        )
        assert len(rows) == 2
        assert {row.metric for row in rows} == {"trace:1", "trace:all"}
