"""HTTP fixtures for the backend conformance suite."""

from __future__ import annotations

import os
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import httpx
import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[object]
) -> Iterator[None]:
    outcome = cast(Any, (yield))
    setattr(item, f"rep_{call.when}", outcome.get_result())


@pytest.fixture(scope="session")
def service_url(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[str, Path]]:
    """Start one isolated backend process for the complete test session."""
    build_dir_value = os.environ.get("BACKEND_BUILD_DIR")
    if build_dir_value is None:
        raise RuntimeError("BACKEND_BUILD_DIR must point to the built backend")
    build_dir = Path(build_dir_value)
    if not build_dir.is_dir():
        raise RuntimeError(f"Backend build directory does not exist: {build_dir}")

    state_dir = tmp_path_factory.mktemp("backend-service")
    models_dir_value = os.environ.get("BACKEND_MODELS_DIR")
    if models_dir_value is None:
        raise RuntimeError(
            "BACKEND_MODELS_DIR must point to the platform model directory"
        )
    models_dir = Path(models_dir_value)
    if not models_dir.is_dir():
        raise RuntimeError(f"Backend models directory does not exist: {models_dir}")
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
    server_log = state_dir / "server.log"
    log_handle = server_log.open("w", encoding="utf-8")
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
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 60
    ready = False
    while time.monotonic() < deadline:
        if process.poll() is not None:
            log_handle.flush()
            server_output = server_log.read_text(encoding="utf-8")
            raise RuntimeError(
                f"Backend process exited during startup with code {process.returncode}:\n"
                f"{server_output[-20000:]}"
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
        log_handle.flush()
        server_output = server_log.read_text(encoding="utf-8")
        log_handle.close()
        raise RuntimeError(
            "Backend did not answer GET /api/meta within 60 seconds:\n"
            f"{server_output[-20000:]}"
        )

    try:
        yield url, server_log
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        log_handle.close()


@pytest.fixture
def api(
    request: pytest.FixtureRequest, service_url: tuple[str, Path]
) -> Iterator[httpx.Client]:
    """Provide an HTTP client and include server logs when a test fails."""
    url, server_log = service_url
    try:
        with httpx.Client(base_url=url, timeout=30.0) as client:
            yield client
    finally:
        report = getattr(request.node, "rep_call", None)
        if report is not None and report.failed:
            output = server_log.read_text(encoding="utf-8")
            print(f"Backend server output (last 20000 characters):\n{output[-20000:]}")
