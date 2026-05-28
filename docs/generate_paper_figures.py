import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from core.engine import SimulationEngine
from core.models import CounterKind, PassengerClass, default_counters
from data_io.parser import load_passengers
from schedulers import SCHEDULERS


FIGURES = Path(__file__).resolve().parent / "figures"
COLORS = {
    PassengerClass.FIRST: "#3B82F6",
    PassengerClass.BUSINESS: "#F59E0B",
    PassengerClass.ECONOMY: "#10B981",
}


def run(key):
    engine = SimulationEngine(
        load_passengers(ROOT / "input.txt"),
        default_counters(),
        SCHEDULERS[key](),
    )
    return engine, engine.run()


def tradeoff_chart():
    labels = {
        "fcfs": "FCFS",
        "priority": "Fixed-Priority",
        "sjf": "SJF",
        "hybrid": "HybridMLQ",
    }
    offsets = {
        "fcfs": (5, -10),
        "priority": (-62, -2),
        "sjf": (5, -6),
        "hybrid": (5, -12),
    }
    colors = {
        "fcfs": "#64748B",
        "priority": "#F59E0B",
        "sjf": "#3B82F6",
        "hybrid": "#DC2626",
    }

    fig, ax = plt.subplots(figsize=(3.45, 2.45))
    for key in labels:
        _, snapshot = run(key)
        overall = snapshot.metrics.overall_att
        worst = max(snapshot.metrics.class_att.values())
        ax.scatter(
            overall,
            worst,
            s=78 if key == "hybrid" else 52,
            marker="*" if key == "hybrid" else "o",
            color=colors[key],
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        ax.annotate(
            labels[key],
            (overall, worst),
            xytext=offsets[key],
            textcoords="offset points",
            fontsize=7.5,
        )

    ax.annotate(
        "lower is better",
        xy=(14.7, 23.2),
        xytext=(17.0, 27.0),
        arrowprops={"arrowstyle": "->", "color": "#475569", "lw": 0.8},
        color="#475569",
        fontsize=7,
    )
    ax.set(xlabel="Overall ATT", ylabel="Worst class ATT", xlim=(14.5, 23.0), ylim=(22.5, 45.5))
    ax.set_xticks([15, 17, 19, 21, 23])
    ax.set_yticks([25, 30, 35, 40, 45])
    ax.grid(color="#CBD5E1", linewidth=0.6, alpha=0.7)
    ax.tick_params(labelsize=7.5)
    ax.xaxis.label.set_size(8)
    ax.yaxis.label.set_size(8)
    fig.tight_layout(pad=0.5)
    fig.savefig(FIGURES / "performance_tradeoff.pdf", bbox_inches="tight")
    plt.close(fig)


def gantt_chart():
    engine, _ = run("hybrid")
    counter_kinds = {counter.counter_id: counter.kind for counter in default_counters()}
    own_class = {
        CounterKind.FIRST_ONLY: PassengerClass.FIRST,
        CounterKind.BUSINESS_ONLY: PassengerClass.BUSINESS,
        CounterKind.ECONOMY_ONLY: PassengerClass.ECONOMY,
    }
    counter_ids = ["C1", "C2", "C3", "C4", "C5"]
    y_positions = {counter_id: len(counter_ids) - index for index, counter_id in enumerate(counter_ids)}

    fig, ax = plt.subplots(figsize=(3.45, 2.25))
    steals = 0
    for passenger in engine.completed:
        kind = counter_kinds[passenger.counter_id]
        stolen = kind in own_class and passenger.cls is not own_class[kind]
        steals += stolen
        y = y_positions[passenger.counter_id]
        ax.broken_barh(
            [(passenger.service_start_time, passenger.service_time)],
            (y - 0.32, 0.64),
            facecolors=COLORS[passenger.cls],
            edgecolors="#111827" if stolen else "white",
            linewidth=1.0 if stolen else 0.35,
            hatch="////" if stolen else None,
        )
        if stolen:
            ax.text(
                passenger.service_start_time + passenger.service_time / 2,
                y,
                passenger.passenger_id,
                ha="center",
                va="center",
                fontsize=6,
                color="#111827",
                bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.85},
            )

    assert steals == 2
    ax.set_xlim(0, max(passenger.completion_time for passenger in engine.completed))
    ax.set_xticks([0, 20, 40, 60, 80])
    ax.set_ylim(0.45, 5.55)
    ax.set_yticks([y_positions[counter_id] for counter_id in counter_ids], counter_ids)
    ax.set_xlabel("Time", fontsize=8)
    ax.set_ylabel("Counter", fontsize=8)
    ax.tick_params(labelsize=7.5)
    ax.grid(axis="x", color="#CBD5E1", linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.legend(
        handles=[
            Patch(facecolor=COLORS[PassengerClass.FIRST], label="FIRST"),
            Patch(facecolor=COLORS[PassengerClass.BUSINESS], label="BUSINESS"),
            Patch(facecolor=COLORS[PassengerClass.ECONOMY], label="ECONOMY"),
            Patch(facecolor="white", edgecolor="#111827", hatch="////", label="Work steal"),
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=4,
        frameon=False,
        fontsize=6.3,
        handlelength=1.2,
        columnspacing=0.8,
    )
    fig.tight_layout(pad=0.45)
    fig.savefig(FIGURES / "hybridmlq_gantt.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    FIGURES.mkdir(exist_ok=True)
    tradeoff_chart()
    gantt_chart()
