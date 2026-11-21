"""Engine and session. The database is disposable: created and seeded at startup."""
import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  (registers tables)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def make_engine(url: str | None = None):
    url = url or os.environ.get("APP_DB_URL")
    if not url:
        DATA_DIR.mkdir(exist_ok=True)
        url = f"sqlite:///{DATA_DIR / 'app.db'}"
    kwargs = {"connect_args": {"check_same_thread": False}}
    if url in ("sqlite://", "sqlite:///:memory:"):
        kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


engine = make_engine()


def set_engine(new_engine) -> None:
    """Tests swap in an in-memory engine."""
    global engine
    engine = new_engine


def create_tables() -> None:
    SQLModel.metadata.create_all(engine)


def drop_tables() -> None:
    SQLModel.metadata.drop_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
