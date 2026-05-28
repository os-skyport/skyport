from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.models import Counter, Passenger, PassengerClass


@dataclass(frozen=True)
class Metrics:
    total_count: int
    completed_count: int
    overall_att: float
    class_att: Mapping[PassengerClass, float]


@dataclass(frozen=True)
class SimSnapshot:
    """Frozen copy of engine state at one tick. The GUI reads only this."""

    time: int
    counters: tuple[Counter, ...]
    queues: Mapping[PassengerClass, tuple[Passenger, ...]]
    completed: tuple[Passenger, ...]
    metrics: Metrics
    events_this_tick: tuple[str, ...]
