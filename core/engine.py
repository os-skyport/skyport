from __future__ import annotations

from collections import deque
from dataclasses import replace
from typing import Iterable

from core.models import CLASS_ORDER, Counter, Passenger, default_counters
from core.snapshot import Metrics, SimSnapshot
from schedulers.base import QueueMap, Scheduler

SAFETY_LIMIT = 1000


class SimulationEngine:
    def __init__(
        self,
        passengers: list[Passenger],
        scheduler: Scheduler,
        counters: list[Counter] | None = None,
    ) -> None:
        self._original_passengers = [p.clone_fresh() for p in passengers]
        self._counter_templates = counters or default_counters()
        self.scheduler = scheduler
        self.reset()

    def reset(self) -> None:
        self.time = 0
        self.passengers = sorted(
            (p.clone_fresh() for p in self._original_passengers),
            key=lambda p: (p.arrival_time, p.passenger_id),
        )
        self.pending = deque(self.passengers)
        self.counters = [Counter(c.counter_id, c.kind) for c in self._counter_templates]
        self.queues: QueueMap = {cls: deque() for cls in CLASS_ORDER}
        self.completed: list[Passenger] = []
        self.events: list[str] = []
        self._last_events: tuple[str, ...] = ()

    @property
    def is_done(self) -> bool:
        return len(self.completed) == len(self.passengers)

    def tick(self) -> SimSnapshot:
        if self.is_done:
            self._last_events = ()
            return self.snapshot()
        if self.time > SAFETY_LIMIT:
            raise RuntimeError(f"Simulation exceeded safety limit {SAFETY_LIMIT}")

        # Order matters: a counter that frees up at t can take a new passenger at t.
        events = self._handle_arrivals() + self._handle_completions() + self._dispatch_idle_counters()
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
        return SimSnapshot(
            time=self.time,
            counters=tuple(
                replace(c, current=replace(c.current) if c.current else None) for c in self.counters
            ),
            queues={cls: tuple(replace(p) for p in self.queues[cls]) for cls in CLASS_ORDER},
            completed=tuple(
                replace(p) for p in sorted(self.completed, key=lambda p: p.completion_time or 0)
            ),
            metrics=self._metrics(),
            events_this_tick=self._last_events,
        )

    def _handle_arrivals(self) -> list[str]:
        arrivals = []
        while self.pending and self.pending[0].arrival_time == self.time:
            arrivals.append(self.pending.popleft())
        events = []
        for p in sorted(arrivals, key=lambda p: p.passenger_id):
            self.queues[p.cls].append(p)
            events.append(
                f"t={self.time:02d} ARRIVAL  {p.passenger_id} ({p.cls.name}, st={p.service_time})"
            )
        return events

    def _handle_completions(self) -> list[str]:
        events = []
        for counter in sorted(self.counters, key=lambda c: c.counter_id):
            if counter.current and counter.remaining == 0:
                p = counter.current
                p.completion_time = self.time
                assert p.completion_time - p.service_start_time == p.service_time, "preemption"
                self.completed.append(p)
                counter.current = None
                events.append(
                    f"t={self.time:02d} COMPLETE {p.passenger_id} @ {counter.counter_id} "
                    f"(TAT={p.turnaround_time})"
                )
        return events

    def _dispatch_idle_counters(self) -> list[str]:
        events = []
        for counter in sorted(self.counters, key=lambda c: c.counter_id):
            if counter.current:
                continue
            p = self.scheduler.select(self.time, counter, self.queues)
            if p is None:
                continue
            assert p.arrival_time <= self.time, "scheduler selected a passenger before arrival"
            p.service_start_time = self.time
            p.counter_id = counter.counter_id
            counter.current = p
            counter.remaining = p.service_time
            events.append(f"t={self.time:02d} DISPATCH {p.passenger_id} -> {counter.counter_id}")
        return events

    def _advance_busy_counters(self) -> None:
        for counter in self.counters:
            if counter.current:
                counter.remaining -= 1
                assert counter.remaining >= 0, "counter remaining time went negative"

    def _metrics(self) -> Metrics:
        return Metrics(
            total_count=len(self.passengers),
            completed_count=len(self.completed),
            overall_att=_average_tat(self.completed),
            class_att={
                cls: _average_tat([p for p in self.completed if p.cls is cls]) for cls in CLASS_ORDER
            },
        )


def _average_tat(passengers: Iterable[Passenger]) -> float:
    values = [p.turnaround_time for p in passengers if p.turnaround_time is not None]
    return sum(values) / len(values) if values else 0.0
