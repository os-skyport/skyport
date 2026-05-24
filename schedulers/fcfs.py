from __future__ import annotations

from typing import Optional

from core.models import CLASS_ORDER, Counter, CounterKind, Passenger, PassengerClass, counter_can_spill_to
from schedulers.base import QueueMap, Scheduler, fcfs_key, iter_queues, remove_passenger


class FCFSScheduler(Scheduler):
    name = "FCFS"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Optional[Passenger]:
        del now
        classes = _allowed_classes(counter, queues)
        candidates = [p for p in iter_queues(queues, classes) if counter_can_spill_to(counter, p)]
        if not candidates:
            return None
        return remove_passenger(queues, min(candidates, key=fcfs_key))


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
