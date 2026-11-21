"""FastAPI application entry point."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.db import engine
from app.routers.admin import router as admin_router
from app.routers.alerts import router as alerts_router
from app.routers.checkins import router as checkins_router
from app.routers.pathways import router as pathways_router
from app.routers.patients import router as patients_router
from app.routers.sessions import router as sessions_router
from app.seed.demo import initialize_demo


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Create the schema and seed/reset demo data at startup."""
    del application
    keep_db = os.getenv("APP_KEEP_DB") == "1"
    with Session(engine) as session:
        initialize_demo(session, keep_existing=keep_db)
    yield


app = FastAPI(title="Rehabilitation Monitoring API", lifespan=lifespan)
app.include_router(admin_router)
app.include_router(alerts_router)
app.include_router(checkins_router)
app.include_router(pathways_router)
app.include_router(patients_router)
app.include_router(sessions_router)

default_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
frontend_dist = Path(os.getenv("APP_FRONTEND_DIST", str(default_frontend_dist))).resolve()
if frontend_dist.is_dir():
    assets = frontend_dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{frontend_path:path}", include_in_schema=False)
    def serve_frontend(frontend_path: str) -> FileResponse:
        """Serve built frontend routes when a distribution is available."""
        if frontend_path == "api" or frontend_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Pot ni bila najdena.")
        requested = (frontend_dist / frontend_path).resolve()
        if requested.is_relative_to(frontend_dist) and requested.is_file():
            return FileResponse(requested)
        return FileResponse(frontend_dist / "index.html")
