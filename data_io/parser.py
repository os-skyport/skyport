from __future__ import annotations

import csv
from pathlib import Path

from core.models import Passenger, PassengerClass


def load_passengers(path: str | Path) -> list[Passenger]:
    text = Path(path).read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if not lines:
        return []
    if "," in lines[0] or lines[0].lower().startswith("passenger_id"):
        return _parse_csv(lines)
    return _parse_whitespace(lines)


def _parse_csv(lines: list[str]) -> list[Passenger]:
    reader = csv.DictReader(lines)
    passengers = []
    for row in reader:
        passengers.append(
            Passenger(
                passenger_id=_normalize_id(row["passenger_id"]),
                arrival_time=int(row["arrival_time"]),
                cls=PassengerClass.parse(row["class"]),
                service_time=int(row["service_time"]),
            )
        )
    return sorted(passengers, key=lambda p: (p.arrival_time, p.passenger_id))


def _parse_whitespace(lines: list[str]) -> list[Passenger]:
    passengers = []
    for line in lines:
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"Expected 4 fields, got {len(parts)} in line: {line}")
        passenger_id, arrival_time, cls, service_time = parts
        passengers.append(
            Passenger(
                passenger_id=_normalize_id(passenger_id),
                arrival_time=int(arrival_time),
                cls=PassengerClass.parse(cls),
                service_time=int(service_time),
            )
        )
    return sorted(passengers, key=lambda p: (p.arrival_time, p.passenger_id))


def _normalize_id(raw: str) -> str:
    value = raw.strip()
    if value.upper().startswith("P"):
        suffix = value[1:]
        if suffix.isdigit():
            return f"P{int(suffix):02d}"
        return value.upper()
    if value.isdigit():
        return f"P{int(value):02d}"
    return value

