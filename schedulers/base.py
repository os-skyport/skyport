from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Deque, Iterable

from core.models import CLASS_ORDER, Counter, Passenger, PassengerClass

QueueMap = dict[PassengerClass, Deque[Passenger]]


class Scheduler(ABC):
    name: str

    @abstractmethod
    def select(self, now: int, counter: Counter, queues: QueueMap) -> Passenger | None:
        """Remove and return the next passenger for an idle counter."""


def pop_best(
    queues: QueueMap,
    key: Callable[[Passenger], tuple],
    classes: Iterable[PassengerClass] = CLASS_ORDER,
) -> Passenger | None:
    """Remove and return the waiting passenger with the smallest key, or None if none wait."""
    best = min((p for cls in classes for p in queues[cls]), key=key, default=None)
    if best is not None:
        queues[best.cls].remove(best)
    return best
