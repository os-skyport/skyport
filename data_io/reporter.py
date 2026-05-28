from __future__ import annotations

from typing import TextIO

from core.models import CLASS_ORDER
from core.snapshot import SimSnapshot

COLUMNS = (
    "passenger_id,arrival_time,class,service_time,"
    "service_start_time,completion_time,turnaround_time,counter_id"
)


def print_report(snapshot: SimSnapshot, stream: TextIO) -> None:
    print(COLUMNS, file=stream)
    for p in sorted(snapshot.completed, key=lambda p: p.passenger_id):
        print(
            f"{p.passenger_id},{p.arrival_time},{p.cls.name},{p.service_time},"
            f"{p.service_start_time},{p.completion_time},{p.turnaround_time},{p.counter_id}",
            file=stream,
        )
    print("", file=stream)
    print("Class      Count   Avg TAT", file=stream)
    for cls in CLASS_ORDER:
        count = sum(1 for p in snapshot.completed if p.cls is cls)
        print(f"{cls.name:<10} {count:>5}   {snapshot.metrics.class_att[cls]:>7.2f}", file=stream)
    print(
        f"{'TOTAL':<10} {snapshot.metrics.completed_count:>5}   ATT = {snapshot.metrics.overall_att:.2f}",
        file=stream,
    )
