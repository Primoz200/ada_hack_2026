"""Shared isolated FastAPI test fixture."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.db as database
import app.main as main
from app.services import clock
from app.services.alerts import sweep_missing_data_alerts


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    """Provide a fresh in-memory database and deterministic application date."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(main, "engine", test_engine)
    monkeypatch.setenv("APP_TODAY", "2026-11-21")
    monkeypatch.setenv("APP_KEEP_DB", "1")
    monkeypatch.setenv("APP_SEED_HISTORY", "0")
    SQLModel.metadata.drop_all(test_engine)
    with TestClient(main.app) as test_client:
        with Session(test_engine) as session:
            sweep_missing_data_alerts(session, clock.today())
        yield test_client
    main.app.dependency_overrides.clear()
    test_engine.dispose()
