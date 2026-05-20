from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PassengerClass(Enum):
    FIRST = 1
    BUSINESS = 2
    ECONOMY = 3

    @classmethod
    def parse(cls, value: str) -> "PassengerClass":
        normalized = value.strip().upper()
        numeric = {"1": cls.FIRST, "2": cls.BUSINESS, "3": cls.ECONOMY}
        if normalized in numeric:
            return numeric[normalized]
        return cls[normalized]


class CounterKind(Enum):
    FIRST_ONLY = "FIRST_ONLY"
    BUSINESS_ONLY = "BUSINESS_ONLY"
    ECONOMY_ONLY = "ECONOMY_ONLY"
    FLEX = "FLEX"


class EventKind(Enum):
    ARRIVAL = "ARRIVAL"
    DISPATCH = "DISPATCH"
    COMPLETION = "COMPLETE"


@dataclass
class Passenger:
    passenger_id: str
    arrival_time: int
    cls: PassengerClass
    service_time: int
    service_start_time: Optional[int] = None
    completion_time: Optional[int] = None
    counter_id: Optional[str] = None

    @property
    def turnaround_time(self) -> Optional[int]:
        if self.completion_time is None:
            return None
        return self.completion_time - self.arrival_time

    def clone_fresh(self) -> "Passenger":
        return Passenger(
            passenger_id=self.passenger_id,
            arrival_time=self.arrival_time,
            cls=self.cls,
            service_time=self.service_time,
        )


@dataclass
class Counter:
    counter_id: str
    kind: CounterKind
    current: Optional[Passenger] = None
    remaining: int = 0

    @property
    def is_idle(self) -> bool:
        return self.current is None


@dataclass(frozen=True)
class Event:
    time: int
    kind: EventKind
    message: str
    passenger_id: Optional[str] = None
    counter_id: Optional[str] = None


CLASS_ORDER = (
    PassengerClass.FIRST,
    PassengerClass.BUSINESS,
    PassengerClass.ECONOMY,
)


def default_counters() -> list[Counter]:
    return [
        Counter("C1", CounterKind.FIRST_ONLY),
        Counter("C2", CounterKind.BUSINESS_ONLY),
        Counter("C3", CounterKind.ECONOMY_ONLY),
        Counter("C4", CounterKind.FLEX),
        Counter("C5", CounterKind.FLEX),
    ]


def counter_accepts(counter: Counter, passenger: Passenger) -> bool:
    if counter.kind is CounterKind.FLEX:
        return True
    if counter.kind is CounterKind.FIRST_ONLY:
        return passenger.cls is PassengerClass.FIRST
    if counter.kind is CounterKind.BUSINESS_ONLY:
        return passenger.cls is PassengerClass.BUSINESS
    if counter.kind is CounterKind.ECONOMY_ONLY:
        return passenger.cls is PassengerClass.ECONOMY
    return False


def counter_can_spill_to(counter: Counter, passenger: Passenger) -> bool:
    if counter.kind is CounterKind.FLEX:
        return True
    if counter.kind is CounterKind.FIRST_ONLY:
        return passenger.cls in {PassengerClass.FIRST, PassengerClass.BUSINESS, PassengerClass.ECONOMY}
    if counter.kind is CounterKind.BUSINESS_ONLY:
        return passenger.cls in {PassengerClass.FIRST, PassengerClass.BUSINESS, PassengerClass.ECONOMY}
    if counter.kind is CounterKind.ECONOMY_ONLY:
        return passenger.cls in {PassengerClass.FIRST, PassengerClass.BUSINESS, PassengerClass.ECONOMY}
    return False

