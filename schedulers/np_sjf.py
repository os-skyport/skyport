from __future__ import annotations

from core.models import Counter, Passenger
from schedulers.base import QueueMap, Scheduler, pop_best


class NonPreemptiveSJFScheduler(Scheduler):
    name = "Non-preemptive SJF"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Passenger | None:
        return pop_best(queues, lambda p: (p.service_time, p.arrival_time, p.passenger_id))
