"""RSS + tracemalloc + gc-object sampler.

Samples the current process's memory at a fixed interval, in a background thread.
Captures:
- rss_kb: resident set from psutil
- vms_kb: virtual memory size
- uss_kb: unique set size (more accurate than rss for leak measurement)
- tracemalloc_kb: Python-allocated bytes tracked by tracemalloc
- gc_objects: total count of tracked Python objects
- iteration: monotonic counter
- elapsed_s: seconds since sampler start

Writes a CSV file suitable for pandas/awk later.
"""

from __future__ import annotations

import csv
import gc
import os
import threading
import time
import tracemalloc
from pathlib import Path

import psutil


class Sampler:
    def __init__(self, csv_path: Path, interval_s: float = 10.0) -> None:
        self.csv_path = Path(csv_path)
        self.interval_s = interval_s
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._process = psutil.Process(os.getpid())
        self._iteration = 0
        self._start_wall = 0.0

    def start(self) -> None:
        tracemalloc.start()
        self._start_wall = time.monotonic()
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "iteration",
                    "timestamp",
                    "elapsed_s",
                    "rss_kb",
                    "vms_kb",
                    "uss_kb",
                    "tracemalloc_kb",
                    "gc_objects",
                ]
            )
        self._thread = threading.Thread(target=self._loop, daemon=True, name="sampler")
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._iteration += 1
            now = time.time()
            elapsed = time.monotonic() - self._start_wall
            try:
                mem = self._process.memory_full_info()
                rss_kb = mem.rss // 1024
                vms_kb = mem.vms // 1024
                uss_kb = getattr(mem, "uss", 0) // 1024
            except psutil.Error:
                rss_kb = vms_kb = uss_kb = 0
            tm_current, _ = tracemalloc.get_traced_memory()
            tm_kb = tm_current // 1024
            gc_count = len(gc.get_objects())
            with self.csv_path.open("a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        self._iteration,
                        f"{now:.3f}",
                        f"{elapsed:.2f}",
                        rss_kb,
                        vms_kb,
                        uss_kb,
                        tm_kb,
                        gc_count,
                    ]
                )
            self._stop_event.wait(self.interval_s)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        try:
            tracemalloc.stop()
        except Exception:
            pass

    def take_snapshot(self, top_n: int = 15) -> str:
        """Return a string with the top-N allocation callsites by size."""
        if not tracemalloc.is_tracing():
            return "tracemalloc not active"
        snap = tracemalloc.take_snapshot()
        stats = snap.statistics("lineno")[:top_n]
        lines = [f"{'size_kb':>10s}  {'count':>6s}  {'file:line':s}"]
        for s in stats:
            size_kb = s.size // 1024
            frame = s.traceback[0]
            lines.append(
                f"{size_kb:>10d}  {s.count:>6d}  {frame.filename}:{frame.lineno}"
            )
        return "\n".join(lines)
