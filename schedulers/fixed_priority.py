from __future__ import annotations

from core.models import CLASS_ORDER, Counter, Passenger
from schedulers.base import QueueMap, Scheduler


class FixedPriorityScheduler(Scheduler):
    name = "Fixed-Priority"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Passenger | None:
        for cls in CLASS_ORDER:
            if queues[cls]:
                return queues[cls].popleft()
        return None
