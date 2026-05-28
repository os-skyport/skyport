from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class PassengerClass(Enum):
    FIRST = 1
    BUSINESS = 2
    ECONOMY = 3

    @classmethod
    def parse(cls, value: str) -> "PassengerClass":
        text = value.strip().upper()
        return cls(int(text)) if text.isdigit() else cls[text]


class CounterKind(Enum):
    FIRST_ONLY = "FIRST_ONLY"
    BUSINESS_ONLY = "BUSINESS_ONLY"
    ECONOMY_ONLY = "ECONOMY_ONLY"
    FLEX = "FLEX"


@dataclass
class Passenger:
    passenger_id: str
    arrival_time: int
    cls: PassengerClass
    service_time: int
    service_start_time: int | None = None
    completion_time: int | None = None
    counter_id: str | None = None

    @property
    def turnaround_time(self) -> int | None:
        if self.completion_time is None:
            return None
        return self.completion_time - self.arrival_time

    def clone_fresh(self) -> "Passenger":
        return replace(self, service_start_time=None, completion_time=None, counter_id=None)


@dataclass
class Counter:
    counter_id: str
    kind: CounterKind
    current: Passenger | None = None
    remaining: int = 0


# FIRST -> BUSINESS -> ECONOMY, also the fixed-priority order.
CLASS_ORDER = tuple(PassengerClass)


def default_counters() -> list[Counter]:
    # Any counter may serve any class; kind is only a preference (see HybridMLQScheduler).
    return [
        Counter("C1", CounterKind.FIRST_ONLY),
        Counter("C2", CounterKind.BUSINESS_ONLY),
        Counter("C3", CounterKind.ECONOMY_ONLY),
        Counter("C4", CounterKind.FLEX),
        Counter("C5", CounterKind.FLEX),
    ]
