"""FastAPI app: API under /api/*, built frontend served from the same origin.
Shared hot file (router registration): only the orchestrator / Matevž edits it.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import seed
from app.routers import admin, alerts, checkins, messages, pathways, patients, sessions

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # the database is disposable and the clock offset lives in memory: reseed on every start
    # unless APP_KEEP_DB=1 (keep an existing file database)
    if os.environ.get("APP_KEEP_DB") == "1":
        seed.seed_if_empty()
    else:
        seed.reset_database()
    yield


app = FastAPI(title="Platforma za spremljanje pacientov po odpustu",
              description="Raziskovalni prototip na sintetičnih podatkih.", version="0.1.0",
              lifespan=lifespan)

for r in (pathways, patients, checkins, sessions, alerts, messages, admin):
    app.include_router(r.router)

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        file = FRONTEND_DIST / path
        return FileResponse(file if path and file.is_file() else FRONTEND_DIST / "index.html")
