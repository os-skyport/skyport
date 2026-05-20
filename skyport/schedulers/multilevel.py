from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

from skyport.core.models import CLASS_ORDER, Counter, CounterKind, Passenger, PassengerClass
from skyport.schedulers.base import QueueMap, Scheduler, iter_queues, remove_passenger

ECONOMY_AGING_THRESHOLD = 10


class HybridMLQScheduler(Scheduler):
    name = "HybridMLQ"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Optional[Passenger]:
        own_class = _own_class(counter)
        if own_class is not None and queues[own_class]:
            return _pick_from_class(now, queues, own_class)

        if counter.kind is CounterKind.FIRST_ONLY:
            return _pick_sjf(queues, (PassengerClass.BUSINESS, PassengerClass.ECONOMY))
        if counter.kind is CounterKind.BUSINESS_ONLY:
            return _pick_sjf(queues, (PassengerClass.FIRST, PassengerClass.ECONOMY))
        if counter.kind is CounterKind.ECONOMY_ONLY:
            return _pick_sjf(queues, (PassengerClass.FIRST, PassengerClass.BUSINESS))
        return _pick_sjf(queues, CLASS_ORDER)


def _own_class(counter: Counter) -> Optional[PassengerClass]:
    if counter.kind is CounterKind.FIRST_ONLY:
        return PassengerClass.FIRST
    if counter.kind is CounterKind.BUSINESS_ONLY:
        return PassengerClass.BUSINESS
    if counter.kind is CounterKind.ECONOMY_ONLY:
        return PassengerClass.ECONOMY
    return None


def _pick_from_class(now: int, queues: QueueMap, cls: PassengerClass) -> Passenger:
    if cls is PassengerClass.ECONOMY:
        aged = [p for p in queues[cls] if now - p.arrival_time >= ECONOMY_AGING_THRESHOLD]
        if aged:
            best = min(aged, key=lambda p: _hrrn_key(now, p))
            return remove_passenger(queues, best)
    return _pick_sjf(queues, (cls,))


def _pick_sjf(queues: QueueMap, classes: Iterable[PassengerClass]) -> Optional[Passenger]:
    candidates = list(iter_queues(queues, classes))
    if not candidates:
        return None
    best = min(candidates, key=_sjf_priority_key)
    return remove_passenger(queues, best)


def _sjf_priority_key(passenger: Passenger) -> tuple[int, int, int, str]:
    return (
        passenger.service_time,
        passenger.cls.value,
        passenger.arrival_time,
        passenger.passenger_id,
    )


def _hrrn_key(now: int, passenger: Passenger) -> tuple[float, int, int, str]:
    waiting = now - passenger.arrival_time
    response_ratio = (waiting + passenger.service_time) / passenger.service_time
    return (
        -response_ratio,
        passenger.service_time,
        passenger.cls.value,
        passenger.passenger_id,
    )

