from __future__ import annotations

import argparse
import sys

from core.engine import SimulationEngine
from core.models import PassengerClass, default_counters
from data_io.parser import load_passengers
from data_io.reporter import print_report
from schedulers.registry import SCHEDULERS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SkyPort check-in counter scheduler simulator")
    parser.add_argument("--input", "-i", default="input.txt", help="Input CSV or whitespace data file")
    parser.add_argument("--scheduler", "-s", choices=SCHEDULERS, default="hybrid")
    parser.add_argument("--compare", action="store_true", help="Run every scheduler and print ATT comparison")
    parser.add_argument("--gui", action="store_true", help="Launch Tkinter GUI")
    parser.add_argument("--web", metavar="PATH", help="Write a browser-checkable HTML GUI")
    parser.add_argument("--log", action="store_true", help="Print event log after a headless run")
    args = parser.parse_args(argv)

    if args.gui:
        from gui.app import run_app

        run_app(args.input, args.scheduler)
        return 0

    passengers = load_passengers(args.input)
    if args.web:
        from gui.web import write_web_gui

        path = write_web_gui(passengers, args.scheduler, args.web)
        print(f"Wrote web GUI: {path}")
        return 0

    if args.compare:
        print_comparison(passengers)
        return 0

    scheduler = SCHEDULERS[args.scheduler]()
    engine = SimulationEngine(passengers, default_counters(), scheduler)
    snapshot = engine.run()
    print_report(snapshot, sys.stdout)
    if args.log:
        print("\nEvent log")
        for event in engine.events:
            print(event.message)
    return 0


def print_comparison(passengers) -> None:
    print("Scheduler              ATT     FIRST   BUSINESS   ECONOMY")
    for key, scheduler_cls in SCHEDULERS.items():
        engine = SimulationEngine(passengers, default_counters(), scheduler_cls())
        snapshot = engine.run()
        metrics = snapshot.metrics
        print(
            f"{scheduler_cls.name:<20} {metrics.overall_att:>6.2f}  "
            f"{metrics.class_att[PassengerClass.FIRST]:>7.2f}  "
            f"{metrics.class_att[PassengerClass.BUSINESS]:>9.2f}  "
            f"{metrics.class_att[PassengerClass.ECONOMY]:>8.2f}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
