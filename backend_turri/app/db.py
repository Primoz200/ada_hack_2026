"""Database engine and session configuration."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


def make_engine(database_url: str | None = None) -> Engine:
    """Create an engine using application database settings."""
    url = database_url or os.getenv("APP_DB_URL") or "sqlite:///data/app.db"
    options: dict[str, object] = {"echo": False}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            options["poolclass"] = StaticPool
        elif url.startswith("sqlite:///"):
            db_path = url.removeprefix("sqlite:///").split("?", maxsplit=1)[0]
            if db_path and db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, **options)


engine = make_engine()


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for a request."""
    with Session(engine) as session:
        yield session


def create_schema(target: Engine | None = None) -> None:
    """Create all database tables."""
    SQLModel.metadata.create_all(target or engine)


def reset_schema(target: Engine | None = None) -> None:
    """Drop and recreate all database tables."""
    database_engine = target or engine
    SQLModel.metadata.drop_all(database_engine)
    SQLModel.metadata.create_all(database_engine)
