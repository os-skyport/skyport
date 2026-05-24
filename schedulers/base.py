from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, Iterable, Optional

from core.models import CLASS_ORDER, Counter, Passenger, PassengerClass

QueueMap = dict[PassengerClass, Deque[Passenger]]


class Scheduler(ABC):
    name: str

    @abstractmethod
    def select(self, now: int, counter: Counter, queues: QueueMap) -> Optional[Passenger]:
        """Remove and return the next passenger for an idle counter."""


def iter_queues(queues: QueueMap, classes: Iterable[PassengerClass] = CLASS_ORDER) -> Iterable[Passenger]:
    for cls in classes:
        yield from queues[cls]


def remove_passenger(queues: QueueMap, passenger: Passenger) -> Passenger:
    queues[passenger.cls].remove(passenger)
    return passenger


def fcfs_key(passenger: Passenger) -> tuple[int, str]:
    return (passenger.arrival_time, passenger.passenger_id)


def hrrn_sort_key(now: int, passenger: Passenger) -> tuple[float, int, str]:
    waiting = now - passenger.arrival_time
    response_ratio = (waiting + passenger.service_time) / passenger.service_time
    return (-response_ratio, passenger.service_time, passenger.passenger_id)


def hrrn_pick(now: int, queues: QueueMap, classes: Iterable[PassengerClass]) -> Optional[Passenger]:
    candidates = list(iter_queues(queues, classes))
    if not candidates:
        return None
    best = min(candidates, key=lambda p: hrrn_sort_key(now, p))
    return remove_passenger(queues, best)
