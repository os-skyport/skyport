from __future__ import annotations

from core.models import CLASS_ORDER, Counter, CounterKind, Passenger, PassengerClass
from schedulers.base import QueueMap, Scheduler, pop_best

ECONOMY_AGING_THRESHOLD = 10

OWN_CLASS = {
    CounterKind.FIRST_ONLY: PassengerClass.FIRST,
    CounterKind.BUSINESS_ONLY: PassengerClass.BUSINESS,
    CounterKind.ECONOMY_ONLY: PassengerClass.ECONOMY,
}


class HybridMLQScheduler(Scheduler):
    """Per-class queues + SJF inside a queue + work stealing + Economy aging."""

    name = "HybridMLQ"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Passenger | None:
        own = OWN_CLASS.get(counter.kind)
        if own is None or not queues[own]:
            # Flex counter, or dedicated counter whose own queue is empty: steal shortest job.
            return pop_best(queues, _sjf_key, [cls for cls in CLASS_ORDER if cls is not own])
        if own is PassengerClass.ECONOMY:
            aged = min(
                (p for p in queues[own] if now - p.arrival_time >= ECONOMY_AGING_THRESHOLD),
                key=lambda p: hrrn_key(now, p),
                default=None,
            )
            if aged is not None:
                queues[own].remove(aged)
                return aged
        return pop_best(queues, _sjf_key, (own,))


def hrrn_key(now: int, passenger: Passenger) -> tuple[float, int, str]:
    waiting = now - passenger.arrival_time
    ratio = (waiting + passenger.service_time) / passenger.service_time
    return (-ratio, passenger.service_time, passenger.passenger_id)


def _sjf_key(passenger: Passenger) -> tuple[int, int, int, str]:
    return (
        passenger.service_time,
        passenger.cls.value,
        passenger.arrival_time,
        passenger.passenger_id,
    )
