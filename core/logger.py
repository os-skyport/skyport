from __future__ import annotations

from core.models import Event


class EventLogger:
    def __init__(self) -> None:
        self._events: list[Event] = []

    def extend(self, events: tuple[Event, ...]) -> None:
        self._events.extend(events)

    def lines(self) -> list[str]:
        return [event.message for event in self._events]

