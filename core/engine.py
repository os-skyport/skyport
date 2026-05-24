from __future__ import annotations

from collections import deque
from typing import Iterable

from core.models import (
    CLASS_ORDER,
    Counter,
    Event,
    EventKind,
    Passenger,
    PassengerClass,
    counter_can_spill_to,
    default_counters,
)
from core.snapshot import CounterState, Metrics, PassengerView, SimSnapshot
from schedulers.base import QueueMap, Scheduler

SAFETY_LIMIT = 1000


class SimulationEngine:
    def __init__(
        self,
        passengers: list[Passenger],
        counters: list[Counter] | None,
        scheduler: Scheduler,
    ) -> None:
        self._original_passengers = [p.clone_fresh() for p in passengers]
        self._counter_templates = counters or default_counters()
        self.scheduler = scheduler
        self.reset()

    def reset(self) -> None:
        self.time = 0
        self.passengers = sorted(
            [p.clone_fresh() for p in self._original_passengers],
            key=lambda p: (p.arrival_time, p.passenger_id),
        )
        self.pending = deque(self.passengers)
        self.counters = [Counter(c.counter_id, c.kind) for c in self._counter_templates]
        self.queues: QueueMap = {cls: deque() for cls in CLASS_ORDER}
        self.completed: list[Passenger] = []
        self.events: list[Event] = []
        self._last_events: tuple[Event, ...] = ()

    @property
    def is_done(self) -> bool:
        return len(self.completed) == len(self.passengers)

    def tick(self) -> SimSnapshot:
        if self.is_done:
            self._last_events = ()
            return self.snapshot()
        if self.time > SAFETY_LIMIT:
            raise RuntimeError(f"Simulation exceeded safety limit {SAFETY_LIMIT}")

        events: list[Event] = []
        events.extend(self._handle_arrivals())
        events.extend(self._handle_completions())
        events.extend(self._dispatch_idle_counters())
        self._advance_busy_counters()
        self._last_events = tuple(events)
        self.events.extend(events)
        snapshot = self.snapshot()
        self.time += 1
        return snapshot

    def run(self) -> SimSnapshot:
        snapshot = self.snapshot()
        while not self.is_done:
            snapshot = self.tick()
        return snapshot

    def snapshot(self) -> SimSnapshot:
        completed_views = tuple(_passenger_view(p) for p in sorted(self.completed, key=lambda p: p.completion_time or 0))
        queues = {cls: tuple(_passenger_view(p) for p in self.queues[cls]) for cls in CLASS_ORDER}
        counters = tuple(
            CounterState(
                counter_id=c.counter_id,
                kind=c.kind.value,
                passenger_id=c.current.passenger_id if c.current else None,
                passenger_class=c.current.cls if c.current else None,
                remaining=c.remaining,
            )
            for c in self.counters
        )
        return SimSnapshot(
            time=self.time,
            counters=counters,
            queues=queues,
            completed=completed_views,
            metrics=self._metrics(),
            events_this_tick=self._last_events,
        )

    def _handle_arrivals(self) -> list[Event]:
        events: list[Event] = []
        arrivals: list[Passenger] = []
        while self.pending and self.pending[0].arrival_time == self.time:
            arrivals.append(self.pending.popleft())
        for passenger in sorted(arrivals, key=lambda p: p.passenger_id):
            self.queues[passenger.cls].append(passenger)
            events.append(
                Event(
                    time=self.time,
                    kind=EventKind.ARRIVAL,
                    passenger_id=passenger.passenger_id,
                    message=f"t={self.time:02d} ARRIVAL  {passenger.passenger_id} ({passenger.cls.name}, st={passenger.service_time})",
                )
            )
        return events

    def _handle_completions(self) -> list[Event]:
        events: list[Event] = []
        for counter in sorted(self.counters, key=lambda c: c.counter_id):
            if counter.current and counter.remaining == 0:
                passenger = counter.current
                passenger.completion_time = self.time
                self._assert_finished(passenger)
                self.completed.append(passenger)
                events.append(
                    Event(
                        time=self.time,
                        kind=EventKind.COMPLETION,
                        passenger_id=passenger.passenger_id,
                        counter_id=counter.counter_id,
                        message=(
                            f"t={self.time:02d} COMPLETE {passenger.passenger_id} @ {counter.counter_id} "
                            f"(TAT={passenger.turnaround_time})"
                        ),
                    )
                )
                counter.current = None
        return events

    def _dispatch_idle_counters(self) -> list[Event]:
        events: list[Event] = []
        for counter in sorted(self.counters, key=lambda c: c.counter_id):
            if not counter.is_idle:
                continue
            passenger = self.scheduler.select(self.time, counter, self.queues)
            if passenger is None:
                continue
            if passenger.arrival_time > self.time:
                raise AssertionError("Scheduler selected a passenger before arrival")
            if not counter_can_spill_to(counter, passenger):
                raise AssertionError(f"{counter.counter_id} cannot accept {passenger.cls.name}")
            passenger.service_start_time = self.time
            passenger.counter_id = counter.counter_id
            counter.current = passenger
            counter.remaining = passenger.service_time
            events.append(
                Event(
                    time=self.time,
                    kind=EventKind.DISPATCH,
                    passenger_id=passenger.passenger_id,
                    counter_id=counter.counter_id,
                    message=f"t={self.time:02d} DISPATCH {passenger.passenger_id} -> {counter.counter_id}",
                )
            )
        return events

    def _advance_busy_counters(self) -> None:
        for counter in self.counters:
            if counter.current:
                counter.remaining -= 1
                if counter.remaining < 0:
                    raise AssertionError("Counter remaining time became negative")

    def _metrics(self) -> Metrics:
        class_att = {}
        for cls in CLASS_ORDER:
            done = [p for p in self.completed if p.cls is cls]
            class_att[cls] = _average_tat(done)
        return Metrics(
            total_count=len(self.passengers),
            completed_count=len(self.completed),
            overall_att=_average_tat(self.completed),
            class_att=class_att,
        )

    def _assert_finished(self, passenger: Passenger) -> None:
        if passenger.service_start_time is None or passenger.completion_time is None:
            raise AssertionError("Finished passenger has incomplete timing data")
        if passenger.completion_time - passenger.service_start_time != passenger.service_time:
            raise AssertionError("Non-preemptive timing invariant violated")


def _average_tat(passengers: Iterable[Passenger]) -> float:
    values = [p.turnaround_time for p in passengers if p.turnaround_time is not None]
    if not values:
        return 0.0
    return sum(values) / len(values)


def _passenger_view(passenger: Passenger) -> PassengerView:
    return PassengerView(
        passenger_id=passenger.passenger_id,
        arrival_time=passenger.arrival_time,
        cls=passenger.cls,
        service_time=passenger.service_time,
        service_start_time=passenger.service_start_time,
        completion_time=passenger.completion_time,
        turnaround_time=passenger.turnaround_time,
        counter_id=passenger.counter_id,
    )

