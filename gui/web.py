from __future__ import annotations

import json
from pathlib import Path

from core.engine import SimulationEngine
from core.models import CLASS_ORDER, Passenger
from core.snapshot import SimSnapshot
from schedulers import SCHEDULERS


def write_web_gui(passengers: list[Passenger], scheduler_key: str, output_path: str | Path) -> Path:
    trace = build_trace(passengers, scheduler_key)
    html = HTML_TEMPLATE.replace("__TRACE_JSON__", json.dumps(trace, ensure_ascii=False))
    path = Path(output_path)
    path.write_text(html, encoding="utf-8")
    return path


def build_trace(passengers: list[Passenger], scheduler_key: str) -> dict:
    """Pre-compute every scheduler's whole run; the page is a pure replay of this."""
    runs = {}
    for key, scheduler_cls in SCHEDULERS.items():
        engine = SimulationEngine(passengers, scheduler_cls())
        snapshots = [_snapshot_to_dict(engine.snapshot())]
        while not engine.is_done:
            snapshots.append(_snapshot_to_dict(engine.tick()))
        runs[key] = {
            "key": key,
            "name": scheduler_cls.name,
            "snapshots": snapshots,
            "bars": [_bar(p) for p in engine.completed],
            "att": snapshots[-1]["metrics"]["overallAtt"],
        }
    return {"schedulerKey": scheduler_key, "runs": runs}


def _bar(passenger: Passenger) -> dict:
    return {
        "passengerId": passenger.passenger_id,
        "className": passenger.cls.name,
        "counterId": passenger.counter_id,
        "startTime": passenger.service_start_time,
        "completionTime": passenger.completion_time,
    }


def _snapshot_to_dict(snapshot: SimSnapshot) -> dict:
    return {
        "time": snapshot.time,
        "counters": [
            {
                "counterId": c.counter_id,
                "kind": c.kind.value,
                "passengerId": c.current.passenger_id if c.current else None,
                "className": c.current.cls.name if c.current else None,
                "startTime": c.current.service_start_time if c.current else None,
                "remaining": c.remaining,
            }
            for c in snapshot.counters
        ],
        "queues": {
            cls.name: [p.passenger_id for p in snapshot.queues[cls]] for cls in CLASS_ORDER
        },
        "metrics": {
            "totalCount": snapshot.metrics.total_count,
            "completedCount": snapshot.metrics.completed_count,
            "overallAtt": round(snapshot.metrics.overall_att, 2),
            "classAtt": {cls.name: round(snapshot.metrics.class_att[cls], 2) for cls in CLASS_ORDER},
        },
        "events": list(snapshot.events_this_tick),
    }


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SkyPort Scheduler GUI</title>
  <style>
    :root {
      --bg: #f8fafc;
      --panel: #ffffff;
      --line: #d7dee8;
      --text: #172033;
      --muted: #64748b;
      --first: #b45309;
      --business: #0369a1;
      --economy: #15803d;
      --idle: #e2e8f0;
      --accent: #2d6cab;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      height: 58px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      padding: 0 18px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1 { font-size: 18px; margin: 0; font-weight: 700; color: var(--accent); }
    main {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 330px;
      gap: 12px;
      padding: 12px;
      min-height: calc(100vh - 58px);
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }
    .left { display: grid; grid-template-rows: auto auto minmax(280px, 1fr); gap: 12px; }
    .right { display: grid; grid-template-rows: auto auto minmax(240px, 1fr); gap: 12px; }
    .controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    button {
      border: 1px solid var(--line);
      background: #f8fafc;
      color: var(--text);
      min-width: 36px;
      height: 34px;
      border-radius: 7px;
      font-size: 14px;
      cursor: pointer;
    }
    button:hover { background: #eef2f7; }
    input[type="range"] { width: 130px; accent-color: var(--accent); }
    .time-entry {
      width: 70px;
      height: 34px;
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 0 8px;
      font-size: 14px;
    }
    .label { color: var(--muted); font-size: 12px; }
    select {
      height: 34px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #f8fafc;
      color: var(--text);
      padding: 0 8px;
      font-size: 14px;
    }
    .time-nav {
      display: flex;
      align-items: center;
      gap: 6px;
      min-width: 260px;
    }
    #timeline { width: 180px; }
    .counters {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(105px, 1fr));
      gap: 8px;
    }
    .counter {
      min-height: 104px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      display: grid;
      align-content: space-between;
      border-left: 6px solid var(--idle);
    }
    .counter.busy.FIRST { border-left-color: var(--first); }
    .counter.busy.BUSINESS { border-left-color: var(--business); }
    .counter.busy.ECONOMY { border-left-color: var(--economy); }
    .counter strong { font-size: 16px; }
    .counter small { color: var(--muted); }
    .queue-row {
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr);
      align-items: start;
      gap: 8px;
      min-height: 38px;
      padding: 6px 0;
      border-bottom: 1px solid #edf1f5;
    }
    .queue-row:last-child { border-bottom: 0; }
    .chips { display: flex; flex-wrap: wrap; gap: 5px; }
    .chip {
      border-radius: 999px;
      color: white;
      font-size: 12px;
      min-width: 38px;
      padding: 4px 8px;
      text-align: center;
    }
    .chip.FIRST { background: var(--first); }
    .chip.BUSINESS { background: var(--business); }
    .chip.ECONOMY { background: var(--economy); }
    .gantt-wrap { overflow: auto; }
    svg { width: 100%; min-width: 760px; height: 300px; display: block; }
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      min-height: 66px;
    }
    .metric b { display: block; font-size: 21px; margin-top: 4px; }
    .compare-row {
      display: grid;
      grid-template-columns: 120px 1fr 48px;
      gap: 8px;
      align-items: center;
      margin: 8px 0;
      font-size: 13px;
    }
    .bar { height: 12px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
    .bar span { display: block; height: 100%; background: var(--accent); }
    .log {
      height: 100%;
      overflow: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      line-height: 1.55;
      white-space: pre-wrap;
    }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { text-align: left; border-bottom: 1px solid #edf1f5; padding: 5px; }
    @media (max-width: 920px) {
      main { grid-template-columns: 1fr; }
      .counters { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
    }
  </style>
</head>
<body>
  <header>
    <h1>SkyPort Scheduler GUI</h1>
    <div class="controls">
      <span class="label">Scheduler</span>
      <select id="schedulerSelect"></select>
      <button id="play" title="Play">▶</button>
      <button id="pause" title="Pause">⏸</button>
      <button id="step" title="Step">⏭</button>
      <button id="reset" title="Reset">⏹</button>
      <span class="time-nav">
        <span class="label">Time</span>
        <input id="timeInput" class="time-entry" type="text" inputmode="numeric" pattern="[0-9]*" value="0">
        <button id="goTime" title="Go to time">Go</button>
        <input id="timeline" type="range" min="0" value="0">
      </span>
      <span class="label">Speed</span>
      <input id="speed" type="range" min="1" max="10" value="5">
    </div>
  </header>
  <main>
    <div class="left">
      <section><div class="counters" id="counters"></div></section>
      <section id="queues"></section>
      <section class="gantt-wrap"><svg id="gantt" viewBox="0 0 900 300" role="img"></svg></section>
    </div>
    <div class="right">
      <section><div class="metrics-grid" id="metrics"></div></section>
      <section id="comparison"></section>
      <section><div class="log" id="log"></div></section>
    </div>
  </main>
  <script>
    const data = __TRACE_JSON__;
    const classColors = { FIRST: "#b45309", BUSINESS: "#0369a1", ECONOMY: "#15803d" };
    let selectedKey = data.schedulerKey;
    let index = 0;
    let timer = null;

    const $ = (id) => document.getElementById(id);
    const schedulerSelect = $("schedulerSelect");
    schedulerSelect.innerHTML = Object.values(data.runs).map((run) => (
      `<option value="${run.key}">${run.name}</option>`
    )).join("");
    schedulerSelect.value = selectedKey;
    updateTimelineBounds();

    function activeRun() { return data.runs[selectedKey]; }
    function activeSnapshots() { return activeRun().snapshots; }
    function finalTime() { return activeSnapshots()[activeSnapshots().length - 1].time; }
    function current() { return activeSnapshots()[index]; }
    function render() {
      const snap = current();
      renderCounters(snap);
      renderQueues(snap);
      renderMetrics(snap);
      renderGantt(snap);
      renderLog(snap);
      renderComparison();
      syncTimeControls(snap);
    }

    function renderCounters(snap) {
      $("counters").innerHTML = snap.counters.map((c) => `
        <div class="counter ${c.passengerId ? "busy " + c.className : ""}">
          <div><strong>${c.counterId}</strong><br><small>${c.kind}</small></div>
          <div>${c.passengerId ? `${c.passengerId} ${c.className}<br><small>remaining ${c.remaining}</small>` : "<small>IDLE</small>"}</div>
        </div>
      `).join("");
    }

    function renderQueues(snap) {
      $("queues").innerHTML = Object.keys(snap.queues).map((cls) => `
        <div class="queue-row">
          <strong>${cls}</strong>
          <div class="chips">${snap.queues[cls].map((id) => `<span class="chip ${cls}">${id}</span>`).join("") || "<span class='label'>empty</span>"}</div>
        </div>
      `).join("");
    }

    function renderMetrics(snap) {
      const m = snap.metrics;
      $("metrics").innerHTML = `
        <div class="metric"><span class="label">Time</span><b>${String(snap.time).padStart(3, "0")}</b></div>
        <div class="metric"><span class="label">Done</span><b>${m.completedCount}/${m.totalCount}</b></div>
        <div class="metric"><span class="label">ATT</span><b>${m.overallAtt.toFixed(2)}</b></div>
        <div class="metric"><span class="label">FIRST</span><b>${m.classAtt.FIRST.toFixed(2)}</b></div>
        <div class="metric"><span class="label">BUSINESS</span><b>${m.classAtt.BUSINESS.toFixed(2)}</b></div>
        <div class="metric"><span class="label">ECONOMY</span><b>${m.classAtt.ECONOMY.toFixed(2)}</b></div>
      `;
    }

    function renderGantt(snap) {
      const svg = $("gantt");
      const maxTime = Math.max(60, finalTime());
      const left = 44;
      const top = 20;
      const rowH = 240 / snap.counters.length;
      const scale = 820 / maxTime;
      const rows = new Map(snap.counters.map((c, i) => [c.counterId, i]));
      let html = "";
      snap.counters.forEach((c, i) => {
        const y = top + i * rowH;
        html += `<text x="8" y="${y + 19}" font-size="13" font-weight="700">${c.counterId}</text>`;
        html += `<line x1="${left}" y1="${y + 24}" x2="880" y2="${y + 24}" stroke="#d7dee8"/>`;
      });
      for (const p of activeRun().bars) {
        if (p.completionTime > snap.time) continue;
        const row = rows.get(p.counterId);
        const x = left + p.startTime * scale;
        const w = Math.max(4, (p.completionTime - p.startTime) * scale);
        const y = top + row * rowH + 5;
        html += `<rect x="${x}" y="${y}" width="${w}" height="26" rx="4" fill="${classColors[p.className]}"></rect>`;
        if (w > 24) html += `<text x="${x + w / 2}" y="${y + 18}" text-anchor="middle" font-size="11" fill="white">${p.passengerId}</text>`;
      }
      for (const c of snap.counters) {
        if (!c.passengerId) continue;
        const row = rows.get(c.counterId);
        const x = left + c.startTime * scale;
        const w = Math.max(4, (snap.time - c.startTime + 1) * scale);
        const y = top + row * rowH + 5;
        html += `<rect x="${x}" y="${y}" width="${w}" height="26" rx="4" fill="${classColors[c.className]}" opacity="0.72"></rect>`;
      }
      html += `<line x1="${left + snap.time * scale}" y1="10" x2="${left + snap.time * scale}" y2="285" stroke="#111827" stroke-width="2"/>`;
      svg.innerHTML = html;
    }

    function renderLog() {
      const lines = activeSnapshots().slice(0, index + 1).flatMap((snap) => snap.events);
      $("log").textContent = lines.slice(-90).join("\\n") || "No events yet.";
    }

    function renderComparison() {
      const runs = Object.values(data.runs);
      const max = Math.max(...runs.map((run) => run.att));
      $("comparison").innerHTML = runs.map((row) => `
        <div class="compare-row">
          <strong>${row.name}${row.key === selectedKey ? " ✓" : ""}</strong>
          <div class="bar"><span style="width:${(row.att / max) * 100}%"></span></div>
          <span>${row.att.toFixed(2)}</span>
        </div>
      `).join("");
    }

    function syncTimeControls(snap) {
      $("timeline").value = index;
      $("timeInput").value = snap.time;
    }

    function updateTimelineBounds() {
      $("timeline").max = activeSnapshots().length - 1;
      $("timeInput").max = finalTime();
    }

    function seekToIndex(nextIndex) {
      index = Math.max(0, Math.min(Number(nextIndex), activeSnapshots().length - 1));
      render();
    }

    function seekToTime(timeValue) {
      const target = Math.max(0, Math.min(Number(timeValue) || 0, finalTime()));
      let nextIndex = 0;
      const snapshots = activeSnapshots();
      for (let i = 0; i < snapshots.length; i += 1) {
        if (snapshots[i].time <= target) nextIndex = i;
        if (snapshots[i].time > target) break;
      }
      seekToIndex(nextIndex);
    }

    function step() {
      seekToIndex(index + 1);
      if (index === activeSnapshots().length - 1) pause();
    }
    function play() {
      if (timer) return;
      timer = setInterval(step, Math.max(40, 700 / Number($("speed").value)));
    }
    function pause() {
      clearInterval(timer);
      timer = null;
    }
    function reset() {
      pause();
      seekToIndex(0);
    }
    $("play").addEventListener("click", play);
    $("pause").addEventListener("click", pause);
    $("step").addEventListener("click", step);
    $("reset").addEventListener("click", reset);
    schedulerSelect.addEventListener("change", () => {
      pause();
      selectedKey = schedulerSelect.value;
      index = 0;
      updateTimelineBounds();
      render();
    });
    $("goTime").addEventListener("click", () => seekToTime($("timeInput").value));
    $("timeInput").addEventListener("keydown", (event) => {
      if (event.key === "Enter") seekToTime($("timeInput").value);
    });
    $("timeline").addEventListener("input", () => {
      pause();
      seekToIndex($("timeline").value);
    });
    $("speed").addEventListener("input", () => {
      if (timer) {
        pause();
        play();
      }
    });
    render();
  </script>
</body>
</html>
"""
