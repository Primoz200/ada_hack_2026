"""Deterministic synthetic patient story plans used by the demo history replay."""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

LEVELS = (1, 2, 3)
LEVEL_OFFSET = {1: 5.0, 2: 0.0, 3: -7.0}


def rng_for(patient_id: str, day_index: int, tag: str = "") -> random.Random:
    return random.Random(f"{patient_id}:{day_index}:{tag}")


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _rating(value: float) -> int:
    return int(_clip(round(value), 1, 10))


def ratings(wellbeing: float, pain: float, rng: random.Random, sd: float = 0.5) -> dict[str, int]:
    return {
        "wellbeing": _rating(wellbeing + rng.gauss(0, sd)),
        "pain": _rating(pain + rng.gauss(0, sd)),
    }


def _rt_p1(k: int, rng: random.Random) -> dict[str, int]:
    return ratings(5.0 + min(3.0, k / 9), max(2.0, 4.5 - k / 10), rng)


def _rt_p2(k: int, rng: random.Random) -> dict[str, int]:
    return ratings(5.5 + 2.0 * (1 - math.exp(-k / 6)), 3.5 - 1.5 * (1 - math.exp(-k / 6)), rng)


def _rt_p3(k: int, rng: random.Random) -> dict[str, int]:
    return ratings(7.0, 2.5, rng, 0.35)


def _rt_p4(k: int, rng: random.Random) -> dict[str, int]:
    if k < 27:
        return ratings(5.5 + 1.5 * min(1.0, k / 14), 5.0 - 3.0 * min(1.0, k / 14), rng, 0.4)
    factor = min(1.0, (k - 26) / 4)
    return ratings(7.0 - 3.0 * factor, 2.0 + 3.5 * factor, rng, 0.4)


def _rt_p5(k: int, rng: random.Random) -> dict[str, int]:
    pain = 3.0 if k <= 7 else 6.0 if k <= 14 else max(1.5, 4.0 - 0.2 * (k - 14))
    return ratings(6.5, pain, rng, 0.4)


def _rt_p6(k: int, rng: random.Random) -> dict[str, int]:
    if k < 24:
        return ratings(7.0, 2.0, rng, 0.4)
    return ratings(4.0, 3.5, rng, 0.4)


def _rt_p7(k: int, rng: random.Random) -> dict[str, int]:
    return ratings(6.0, 3.0, rng)


def _rt_p8(k: int, rng: random.Random) -> dict[str, int]:
    return ratings(6.5, 3.0, rng, 0.9)


def _rt_p9(k: int, rng: random.Random) -> dict[str, int]:
    return ratings(5.5, 4.0, rng)


def _rt_demo(k: int, rng: random.Random) -> dict[str, int]:
    return ratings(7.0, 2.0, rng, 0.4)


def _ramp(start: float, slope: float, cap: float) -> Callable[[int], float]:
    return lambda k: min(cap, start + slope * k)


def _p3_curve(k: int) -> float:
    if k <= 21:
        return 80.0 + 0.25 * k
    return 80.0 + 0.25 * 21 - 0.85 * (k - 21)


def _p4_curve(k: int) -> float:
    return 66.0 if k <= 26 else 66.0 - 2.5 * (k - 26)


def _demo_curve(k: int) -> float:
    return 63.0 + 0.1 * k


@dataclass(frozen=True)
class Story:
    id: str
    discharge_ago: int
    curve: Callable[[int], float]
    rating_plan: Callable[[int, random.Random], dict[str, int]]
    noise: float = 2.5
    skip_prob: float = 0.07
    reliable_from: int = 10**6
    always: frozenset[int] = frozenset()
    days: frozenset[int] | None = None
    from_k: int = 1
    bad_days: dict[int, float] = field(default_factory=dict)
    level_offsets: dict[int, float] | None = None
    acks: dict[int, tuple[bool, str | None, str | None]] = field(default_factory=dict)
    input_device: str = "touch"

    def active(self, k: int) -> bool:
        if k < self.from_k:
            return False
        if self.days is not None:
            return k in self.days
        if k >= self.reliable_from or k <= 3 or k in self.always:
            return True
        missed = rng_for(self.id, k, "skip").random() < self.skip_prob
        prev_missed = rng_for(self.id, k - 1, "skip").random() < self.skip_prob
        next_missed = rng_for(self.id, k + 1, "skip").random() < self.skip_prob
        return not (missed and not prev_missed and not next_missed)

    def plan(self, k: int) -> tuple[dict[str, int], dict[int, float]] | None:
        if not self.active(k):
            return None
        center = self.curve(k) + self.bad_days.get(k, 0.0)
        offsets = self.level_offsets or LEVEL_OFFSET
        scores = {
            level: round(
                _clip(
                    center
                    + offsets[level]
                    + rng_for(self.id, k, f"score{level}").gauss(0, self.noise),
                    4.0,
                    98.0,
                ),
                1,
            )
            for level in LEVELS
        }
        return self.rating_plan(k, rng_for(self.id, k, "ratings")), scores


STORIES = [
    Story("p1", 28, _ramp(50, 0.85, 76), _rt_p1, reliable_from=24),
    Story(
        "p2",
        36,
        lambda k: 52 + 28 * (1 - math.exp(-k / 5)),
        _rt_p2,
        noise=2.0,
        reliable_from=30,
        input_device="mouse",
    ),
    Story(
        "p3",
        40,
        _p3_curve,
        _rt_p3,
        noise=0.7,
        reliable_from=21,
        level_offsets={1: 2.0, 2: 0.0, 3: -2.0},
        input_device="mouse",
    ),
    Story("p4", 35, _p4_curve, _rt_p4, noise=2.0, reliable_from=24),
    Story(
        "p5",
        28,
        _ramp(52, 0.9, 76),
        _rt_p5,
        noise=2.5,
        reliable_from=22,
        always=frozenset({4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}),
        acks={
            13: (False, None, None),
            14: (
                True,
                "called_reassured",
                "Poklicala pacientko: močnejša bolečina v drugem tednu po operaciji je "
                "pričakovana, brez posebnih ukrepov.",
            ),
        },
    ),
    Story("p6", 30, lambda k: 64.0, _rt_p6, noise=2.0, reliable_from=20),
    Story(
        "p7",
        15,
        lambda k: 58.0 + 0.5 * k,
        _rt_p7,
        days=frozenset({1, 2, 3, 5, 6, 9}),
        input_device="mouse",
    ),
    Story(
        "p8",
        30,
        lambda k: 62.0 + 0.15 * k,
        _rt_p8,
        noise=4.0,
        reliable_from=8,
        always=frozenset({11, 21}),
        bad_days={11: -12.0, 21: -20.0},
    ),
    Story("p9", 3, lambda k: 55.0, _rt_p9, skip_prob=0.0),
    Story("demo", 21, _demo_curve, _rt_demo, noise=1.2, reliable_from=6),
]
