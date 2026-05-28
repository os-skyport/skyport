from __future__ import annotations

from core.models import Counter, Passenger
from schedulers.base import QueueMap, Scheduler, pop_best


class FCFSScheduler(Scheduler):
    name = "FCFS"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Passenger | None:
        return pop_best(queues, lambda p: (p.arrival_time, p.passenger_id))
