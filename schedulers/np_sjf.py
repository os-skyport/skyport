from __future__ import annotations

from typing import Optional

from core.models import CLASS_ORDER, Counter, CounterKind, Passenger, PassengerClass
from schedulers.base import QueueMap, Scheduler, iter_queues, remove_passenger


class NonPreemptiveSJFScheduler(Scheduler):
    name = "Non-preemptive SJF"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Optional[Passenger]:
        del now
        candidates = list(iter_queues(queues, _allowed_classes(counter, queues)))
        if not candidates:
            return None
        best = min(candidates, key=lambda p: (p.service_time, p.arrival_time, p.passenger_id))
        return remove_passenger(queues, best)


def _allowed_classes(counter: Counter, queues: QueueMap) -> tuple[PassengerClass, ...]:
    if counter.kind is CounterKind.FIRST_ONLY:
        if queues[PassengerClass.FIRST]:
            return (PassengerClass.FIRST,)
        return (PassengerClass.BUSINESS, PassengerClass.ECONOMY)
    if counter.kind is CounterKind.BUSINESS_ONLY:
        if queues[PassengerClass.BUSINESS]:
            return (PassengerClass.BUSINESS,)
        return (PassengerClass.BUSINESS, PassengerClass.ECONOMY)
    if counter.kind is CounterKind.ECONOMY_ONLY:
        return (PassengerClass.ECONOMY,)
    return CLASS_ORDER
