from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk

from core.engine import SimulationEngine
from core.models import CLASS_ORDER, PassengerClass, default_counters
from data_io.parser import load_passengers
from data_io.reporter import summary_text
from schedulers.registry import SCHEDULERS


CLASS_COLORS = {
    PassengerClass.FIRST: "#c2410c",
    PassengerClass.BUSINESS: "#0369a1",
    PassengerClass.ECONOMY: "#15803d",
}


class SkyPortApp(tk.Tk):
    def __init__(self, input_path: str, scheduler_key: str) -> None:
        super().__init__()
        self.title("SkyPort Check-in Scheduler")
        self.geometry("1180x780")
        self.input_path = input_path
        self.scheduler_var = tk.StringVar(value=scheduler_key)
        self.speed_var = tk.IntVar(value=4)
        self.time_var = tk.IntVar(value=0)
        self.running = False
        self.after_id: str | None = None
        self.gantt_rows: dict[str, int] = {}
        self.passengers = load_passengers(self.input_path)
        self.engine = self._new_engine()
        self._build_ui()
        self._render(self.engine.snapshot())

    def _new_engine(self) -> SimulationEngine:
        scheduler = SCHEDULERS[self.scheduler_var.get()]()
        return SimulationEngine(self.passengers, default_counters(), scheduler)

    def _build_ui(self) -> None:
        self.configure(bg="#f8fafc")
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill="x")

        ttk.Label(toolbar, text="Scheduler").pack(side="left", padx=(0, 6))
        scheduler_box = ttk.Combobox(
            toolbar,
            state="readonly",
            width=12,
            textvariable=self.scheduler_var,
            values=list(SCHEDULERS.keys()),
        )
        scheduler_box.pack(side="left", padx=(0, 8))
        scheduler_box.bind("<<ComboboxSelected>>", lambda _event: self.reset())

        ttk.Button(toolbar, text="Load CSV", command=self.load_file).pack(side="left", padx=3)
        ttk.Button(toolbar, text="▶", width=3, command=self.play).pack(side="left", padx=3)
        ttk.Button(toolbar, text="⏸", width=3, command=self.pause).pack(side="left", padx=3)
        ttk.Button(toolbar, text="⏭", width=3, command=self.step).pack(side="left", padx=3)
        ttk.Button(toolbar, text="⏹", width=3, command=self.reset).pack(side="left", padx=3)
        ttk.Label(toolbar, text="Time").pack(side="left", padx=(18, 4))
        self.time_spin = ttk.Spinbox(toolbar, from_=0, to=1000, width=5, textvariable=self.time_var, command=self.seek_to_time)
        self.time_spin.pack(side="left", padx=3)
        ttk.Button(toolbar, text="Go", width=4, command=self.seek_to_time).pack(side="left", padx=3)
        ttk.Label(toolbar, text="Speed").pack(side="left", padx=(18, 4))
        ttk.Scale(toolbar, from_=1, to=10, variable=self.speed_var, orient="horizontal", length=140).pack(side="left")

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left = ttk.Frame(body)
        right = ttk.Frame(body, width=310)
        body.add(left, weight=4)
        body.add(right, weight=1)

        self.counter_frame = ttk.LabelFrame(left, text="Counters", padding=10)
        self.counter_frame.pack(fill="x", pady=(0, 8))
        self.counter_labels: dict[str, ttk.Label] = {}
        for idx, counter_id in enumerate(["C1", "C2", "C3", "C4", "C5"]):
            label = ttk.Label(self.counter_frame, anchor="center", relief="ridge", padding=12)
            label.grid(row=0, column=idx, padx=5, sticky="ew")
            self.counter_frame.columnconfigure(idx, weight=1, minsize=130)
            self.counter_labels[counter_id] = label

        self.queue_frame = ttk.LabelFrame(left, text="Queues", padding=10)
        self.queue_frame.pack(fill="x", pady=(0, 8))
        self.queue_labels: dict[PassengerClass, ttk.Label] = {}
        for row, cls in enumerate(CLASS_ORDER):
            ttk.Label(self.queue_frame, text=f"{cls.name:<8}").grid(row=row, column=0, sticky="w", pady=3)
            label = ttk.Label(self.queue_frame, text="", anchor="w")
            label.grid(row=row, column=1, sticky="ew", pady=3)
            self.queue_labels[cls] = label
        self.queue_frame.columnconfigure(1, weight=1)

        gantt_frame = ttk.LabelFrame(left, text="Gantt", padding=10)
        gantt_frame.pack(fill="both", expand=True)
        self.gantt = tk.Canvas(gantt_frame, bg="white", height=280, highlightthickness=0)
        self.gantt.pack(fill="both", expand=True)

        metrics_frame = ttk.LabelFrame(right, text="Metrics", padding=10)
        metrics_frame.pack(fill="x", pady=(0, 8))
        self.metrics_text = tk.Text(metrics_frame, height=10, wrap="none", relief="flat", bg="#f8fafc")
        self.metrics_text.pack(fill="x")

        log_frame = ttk.LabelFrame(right, text="Event log", padding=10)
        log_frame.pack(fill="both", expand=True)
        self.log_list = tk.Listbox(log_frame)
        self.log_list.pack(fill="both", expand=True)

    def load_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Load passengers",
            filetypes=[("Data files", "*.csv *.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        self.input_path = path
        self.passengers = load_passengers(path)
        self.reset()

    def play(self) -> None:
        if self.running:
            return
        self.running = True
        self._schedule_next()

    def pause(self) -> None:
        self.running = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def step(self) -> None:
        if self.engine.is_done:
            return
        snapshot = self.engine.tick()
        self._render(snapshot)

    def reset(self) -> None:
        self.pause()
        self.engine = self._new_engine()
        self.time_var.set(0)
        self.gantt.delete("all")
        self.log_list.delete(0, "end")
        self._render(self.engine.snapshot())

    def seek_to_time(self) -> None:
        self.pause()
        target = max(0, self.time_var.get())
        self.engine = self._new_engine()
        self.gantt.delete("all")
        self.log_list.delete(0, "end")
        snapshot = self.engine.snapshot()
        while not self.engine.is_done and snapshot.time < target:
            snapshot = self.engine.tick()
            for event in snapshot.events_this_tick:
                self.log_list.insert("end", event.message)
        if target == 0 and not self.engine.is_done:
            snapshot = self.engine.tick()
            for event in snapshot.events_this_tick:
                self.log_list.insert("end", event.message)
        self._render(snapshot, append_events=False)

    def _schedule_next(self) -> None:
        if not self.running:
            return
        self.step()
        if self.engine.is_done:
            self.running = False
            return
        delay = max(40, int(1000 / self.speed_var.get()))
        self.after_id = self.after(delay, self._schedule_next)

    def _render(self, snapshot, append_events: bool = True) -> None:
        self.time_var.set(snapshot.time)
        for counter in snapshot.counters:
            text = f"{counter.counter_id}\n{counter.kind}\n"
            if counter.passenger_id:
                text += f"{counter.passenger_id} {counter.passenger_class.name}\nrem {counter.remaining}"
            else:
                text += "IDLE"
            self.counter_labels[counter.counter_id].configure(text=text)

        for cls in CLASS_ORDER:
            queue_text = " ".join(p.passenger_id for p in snapshot.queues[cls])
            self.queue_labels[cls].configure(text=queue_text or "-")

        self.metrics_text.configure(state="normal")
        self.metrics_text.delete("1.0", "end")
        self.metrics_text.insert("end", f"Time: {snapshot.time:03d}\n")
        self.metrics_text.insert("end", f"Done: {snapshot.metrics.completed_count}/{snapshot.metrics.total_count}\n\n")
        self.metrics_text.insert("end", summary_text(snapshot))
        self.metrics_text.configure(state="disabled")

        if append_events:
            for event in snapshot.events_this_tick:
                self.log_list.insert("end", event.message)
                self.log_list.see("end")

        self._draw_gantt(snapshot)

    def _draw_gantt(self, snapshot) -> None:
        width = max(self.gantt.winfo_width(), 800)
        row_height = 44
        left_pad = 38
        unit = max(8, (width - left_pad - 20) / max(60, snapshot.time + 1))
        self.gantt.delete("all")
        for row, counter in enumerate(snapshot.counters):
            y = 18 + row * row_height
            self.gantt.create_text(15, y + 12, text=counter.counter_id, anchor="w", font=("TkDefaultFont", 10, "bold"))
            self.gantt.create_line(left_pad, y + 25, width - 10, y + 25, fill="#e2e8f0")

        completed = list(snapshot.completed)
        active = [
            p
            for p in self.engine.passengers
            if p.service_start_time is not None and p.completion_time is None and p.counter_id is not None
        ]
        for p in completed + active:
            if p.service_start_time is None or p.counter_id is None:
                continue
            row = int(p.counter_id[1:]) - 1
            end = p.completion_time if p.completion_time is not None else snapshot.time
            x1 = left_pad + p.service_start_time * unit
            x2 = left_pad + max(end, p.service_start_time + 1) * unit
            y1 = 8 + row * row_height
            y2 = y1 + 24
            self.gantt.create_rectangle(x1, y1, x2, y2, fill=CLASS_COLORS[p.cls], outline="")
            if x2 - x1 > 24:
                self.gantt.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=p.passenger_id, fill="white")


def run_app(input_path: str, scheduler_key: str) -> None:
    app = SkyPortApp(input_path, scheduler_key)
    app.mainloop()
