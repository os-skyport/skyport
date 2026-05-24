from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from core.models import Event, PassengerClass


@dataclass(frozen=True)
class PassengerView:
    passenger_id: str
    arrival_time: int
    cls: PassengerClass
    service_time: int
    service_start_time: Optional[int]
    completion_time: Optional[int]
    turnaround_time: Optional[int]
    counter_id: Optional[str]


@dataclass(frozen=True)
class CounterState:
    counter_id: str
    kind: str
    passenger_id: Optional[str]
    passenger_class: Optional[PassengerClass]
    remaining: int


@dataclass(frozen=True)
class Metrics:
    total_count: int
    completed_count: int
    overall_att: float
    class_att: Mapping[PassengerClass, float]


@dataclass(frozen=True)
class SimSnapshot:
    time: int
    counters: tuple[CounterState, ...]
    queues: Mapping[PassengerClass, tuple[PassengerView, ...]]
    completed: tuple[PassengerView, ...]
    metrics: Metrics
    events_this_tick: tuple[Event, ...]

