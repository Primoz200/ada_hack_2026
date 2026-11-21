"""Shared fixtures: every test gets a fresh in-memory database and a fixed "today"."""
import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import db as dbmod
from app.seed.pathways import fresh_clinicians, fresh_pathways
from app.services import clock

TODAY = date(2026, 11, 21)

# the app lifespan reseeds on every start; tests build their own data and keep it
os.environ["APP_KEEP_DB"] = "1"


@pytest.fixture(autouse=True)
def _fresh_db():
    dbmod.set_engine(dbmod.make_engine("sqlite://"))
    dbmod.create_tables()
    clock.reset()
    clock.set_today(TODAY)
    yield
    clock.reset()


@pytest.fixture
def db():
    """Empty database with pathways and clinicians only (no patients)."""
    with Session(dbmod.engine) as session:
        for row in fresh_pathways() + fresh_clinicians():
            session.add(row)
        session.commit()
        yield session


@pytest.fixture
def client():
    """API client on a seeded database."""
    from app import seed
    from app.main import app

    seed.seed_if_empty()
    with TestClient(app) as c:
        yield c
