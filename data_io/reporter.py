from __future__ import annotations

import csv
from pathlib import Path
from typing import TextIO

from core.models import CLASS_ORDER, Passenger, PassengerClass
from core.snapshot import SimSnapshot


def print_report(snapshot: SimSnapshot, stream: TextIO) -> None:
    rows = sorted(snapshot.completed, key=lambda p: p.passenger_id)
    print("passenger_id,arrival_time,class,service_time,service_start_time,completion_time,turnaround_time,counter_id", file=stream)
    for p in rows:
        print(
            f"{p.passenger_id},{p.arrival_time},{p.cls.name},{p.service_time},"
            f"{p.service_start_time},{p.completion_time},{p.turnaround_time},{p.counter_id}",
            file=stream,
        )
    print("", file=stream)
    print(summary_text(snapshot), file=stream)


def summary_text(snapshot: SimSnapshot) -> str:
    counts = {cls: sum(1 for p in snapshot.completed if p.cls is cls) for cls in CLASS_ORDER}
    lines = ["Class      Count   Avg TAT"]
    for cls in CLASS_ORDER:
        lines.append(f"{cls.name:<10} {counts[cls]:>5}   {snapshot.metrics.class_att[cls]:>7.2f}")
    lines.append(f"{'TOTAL':<10} {snapshot.metrics.completed_count:>5}   ATT = {snapshot.metrics.overall_att:.2f}")
    return "\n".join(lines)


def write_csv(path: str | Path, passengers: list[Passenger]) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(
            [
                "passenger_id",
                "arrival_time",
                "class",
                "service_time",
                "service_start_time",
                "completion_time",
                "turnaround_time",
                "counter_id",
            ]
        )
        for p in sorted(passengers, key=lambda passenger: passenger.passenger_id):
            writer.writerow(
                [
                    p.passenger_id,
                    p.arrival_time,
                    p.cls.name,
                    p.service_time,
                    p.service_start_time,
                    p.completion_time,
                    p.turnaround_time,
                    p.counter_id,
                ]
            )

