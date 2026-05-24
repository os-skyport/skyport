from __future__ import annotations

from typing import Optional

from core.models import CLASS_ORDER, Counter, CounterKind, Passenger, PassengerClass
from schedulers.base import QueueMap, Scheduler


class FixedPriorityScheduler(Scheduler):
    name = "Fixed-Priority"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Optional[Passenger]:
        del now
        for cls in _priority_classes(counter):
            if queues[cls]:
                return queues[cls].popleft()
        return None


def _priority_classes(counter: Counter) -> tuple[PassengerClass, ...]:
    if counter.kind is CounterKind.FIRST_ONLY:
        return CLASS_ORDER
    if counter.kind is CounterKind.BUSINESS_ONLY:
        return (PassengerClass.BUSINESS, PassengerClass.ECONOMY)
    if counter.kind is CounterKind.ECONOMY_ONLY:
        return (PassengerClass.ECONOMY,)
    return CLASS_ORDER

