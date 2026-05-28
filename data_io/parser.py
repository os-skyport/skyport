from __future__ import annotations

import csv
from pathlib import Path

from core.models import Passenger, PassengerClass


def load_passengers(path: str | Path) -> list[Passenger]:
    """Read `id, arrival_time, class, service_time` rows, comma- or whitespace-separated."""
    passengers = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = next(csv.reader([line])) if "," in line else line.split()
        if fields[0].strip().lower() == "passenger_id":
            continue
        if len(fields) != 4:
            raise ValueError(f"Expected 4 fields, got {len(fields)} in line: {line}")
        passenger_id, arrival_time, cls, service_time = fields
        passengers.append(
            Passenger(
                _normalize_id(passenger_id),
                int(arrival_time),
                PassengerClass.parse(cls),
                int(service_time),
            )
        )
    return sorted(passengers, key=lambda p: (p.arrival_time, p.passenger_id))


def _normalize_id(raw: str) -> str:
    value = raw.strip().upper()
    digits = value.removeprefix("P")
    return f"P{int(digits):02d}" if digits.isdigit() else value
