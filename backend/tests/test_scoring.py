import math
import random

import pytest

from app.services import scoring


def trace(dev: float, n: int = 120, seed: int = 1):
    """A line trace (level 1, normalised 0-1) with random lateral error of roughly `dev`."""
    rnd = random.Random(seed)
    xs = [0.1 + 0.8 * i / (n - 1) for i in range(n)]
    ys = [0.5 + dev * math.sin(i / 7) + rnd.gauss(0, dev / 3) for i in range(n)]
    return {"targetX": [0.1, 0.9], "targetY": [0.5, 0.5], "t": [i * 80.0 for i in range(n)],
            "x": xs, "y": ys, "strokeId": [0.0] * n}


@pytest.fixture(autouse=True)
def _no_external_model(monkeypatch):
    monkeypatch.setitem(scoring._hook, "tried", True)
    monkeypatch.setitem(scoring._hook, "fn", None)
    monkeypatch.setitem(scoring._hook, "failed", False)


def test_standin_near_perfect_is_high_and_sloppy_is_lower():
    good = scoring.score_session("trace", 1, "right", 10_000, trace(0.012), {})
    sloppy = scoring.score_session("trace", 1, "right", 10_000, trace(0.04), {})
    awful = scoring.score_session("trace", 1, "right", 10_000, trace(0.09), {})
    assert 85 <= good.score <= 95 and good.impairment_class == "normal"
    assert sloppy.score < good.score - 20
    assert awful.score < sloppy.score
    assert good.model_version == scoring.STANDIN_VERSION == scoring.current_model_version()


def test_empty_trace_scores_zero():
    assert scoring.score_session("trace", 1, "right", 1000, {}, {}).score == 0.0


def test_external_model_is_used_with_converted_format(monkeypatch):
    seen = {}

    def fake(game_type, level, hand, duration_ms, series, client_meta):
        seen.update(level=level, x=series["x"][0], t=series["t"][1])
        return {"score": 77.0, "impairment_class": "mild", "features": {"a": 1}, "model_version": "ext-1"}

    monkeypatch.setitem(scoring._hook, "fn", fake)
    monkeypatch.setitem(scoring._hook, "version", "ext-1")
    r = scoring.score_session("trace", 2, "right", 9000, trace(0.01), {})
    assert (r.score, r.model_version) == (77.0, "ext-1")
    assert seen["level"] == "circle" and seen["x"] == pytest.approx(100.0) and seen["t"] == 80.0
    assert scoring.current_model_version() == "ext-1"


@pytest.mark.parametrize("bad", [RuntimeError("boom"), "nan", "garbage"])
def test_external_failure_falls_back_to_standin(monkeypatch, bad):
    def broken(*a):
        if isinstance(bad, Exception):
            raise bad
        return {"score": float("nan")} if bad == "nan" else "garbage"

    monkeypatch.setitem(scoring._hook, "fn", broken)
    monkeypatch.setitem(scoring._hook, "version", "ext-1")
    r = scoring.score_session("trace", 1, "right", 10_000, trace(0.012), {})
    assert r.model_version == scoring.STANDIN_VERSION
    assert scoring.current_model_version() == scoring.STANDIN_VERSION


def test_real_tracer_model_loads_and_scores(monkeypatch):
    monkeypatch.setitem(scoring._hook, "tried", False)
    monkeypatch.setitem(scoring._hook, "fn", None)
    r = scoring.score_session("trace", 1, "right", 10_000, trace(0.012), {})
    # Primož's trained model (backend/models/tracer/artifacts) is picked up through the bridge
    assert r.model_version.startswith("tracer-gbm")
    assert 0 <= r.score <= 100 and "dev_rms" in r.features
