"""HTTP fixtures for the backend conformance suite."""

from __future__ import annotations

import os
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest


@pytest.fixture(scope="session")
def service_url(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Start one isolated backend process for the complete test session."""
    build_dir_value = os.environ.get("BACKEND_BUILD_DIR")
    if build_dir_value is None:
        raise RuntimeError("BACKEND_BUILD_DIR must point to the built backend")
    build_dir = Path(build_dir_value)
    if not build_dir.is_dir():
        raise RuntimeError(f"Backend build directory does not exist: {build_dir}")

    state_dir = tmp_path_factory.mktemp("backend-service")
    models_dir = state_dir / "models"
    models_dir.mkdir()
    database = state_dir / "app.db"
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]

    env = os.environ.copy()
    env.update(
        {
            "APP_TODAY": "2026-11-21",
            "APP_DB_URL": f"sqlite:///{database}",
            "APP_MODELS_DIR": str(models_dir),
            "APP_KEEP_DB": "1",
        }
    )
    process = subprocess.Popen(
        [
            "uv",
            "run",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=build_dir,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 60
    ready = False
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Backend process exited during startup with code {process.returncode}"
            )
        try:
            response = httpx.get(f"{url}/api/meta", timeout=1.0)
            if response.status_code == 200:
                ready = True
                break
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    if not ready:
        process.terminate()
        process.wait(timeout=10)
        raise RuntimeError("Backend did not answer GET /api/meta within 60 seconds")

    try:
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


@pytest.fixture
def api(service_url: str) -> Iterator[httpx.Client]:
    """Provide an HTTP client to the separately running service."""
    with httpx.Client(base_url=service_url, timeout=30.0) as client:
        yield client
