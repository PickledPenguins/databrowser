"""Timing and memory gates, run by tests/run-tests.sh perf and nothing else.

Timing compares the median of several runs of each workload with a baseline recorded on this
machine, .build/perf-baseline.json, written by tests/run-tests.sh perf-baseline. A baseline
from another machine means nothing, so it is not committed. A workload fails when its median
is more than THRESHOLD times its baseline.

Memory is gated in a run of its own, since tracing allocations slows every one of them: the
peak traced while a page is built and written must stay under a ceiling per row.
"""

import json
import os
import statistics
import time
import tracemalloc
from pathlib import Path

import pytest

from databrowser import Badge, DataPage, GroupPage, Theme

pytestmark = pytest.mark.perf

BASELINE = Path(__file__).resolve().parent.parent / ".build" / "perf-baseline.json"
RUNS = 9
# Medians of unchanged code across 10 separate runs spanned at most 3% from lowest to highest
# (see docs/testing.md); 1.25 leaves room for a busier machine and still catches a real
# slowdown.
THRESHOLD = 1.25


def many_small_pages():
    """A site of 200 pages of a few rows each: the per-page cost, which reading and inlining
    the style files dominates."""
    theme = Theme(banner="Lab", bottom_banner="Contact", banner_color="#0f3d3e", title_image="t.png")
    top = GroupPage("site/index.html", "Top", ["Name", "Pages"], theme=theme)
    for group in range(20):
        series = GroupPage(f"site/s{group}/index.html", f"s{group}", ["Name", "N"], parent=top, theme=theme)
        for run in range(9):
            data = DataPage(f"site/s{group}/r{run}/index.html", f"r{run}", columns=2, parent=series, theme=theme)
            data.add_row([("a.png", "a"), ("b.png", "b")], label="row", badge=Badge("ok", "ok"))
            data.write()
            series.add_row(data, [f"r{run}", run])
        series.write()
        top.add_row(series, [f"s{group}", 9])
    top.write()


def big_table(rows: int = 20000):
    page = GroupPage("site/index.html", "Top", ["Name", "Images", "Size", "Status"])
    for row in range(rows):
        page.add_row(f"run-{row}/index.html", [f"run-{row}", row, row * 1.5, Badge("ok", "ok")])
    page.write()


def big_grid(rows: int = 2000):
    page = DataPage("site/index.html", "Grid", columns=4, column_titles=["a", "b", "c", "d"])
    for row in range(rows):
        page.add_row([(f"img/{row}-{column}.png", f"row {row}\ncolumn {column}") for column in range(4)],
                     label=f"row {row}", badge=Badge("1 missing", "warn"))
    page.write()


WORKLOADS = {"many_small_pages": many_small_pages, "big_table": big_table, "big_grid": big_grid}


def median_time(workload) -> float:
    times = []
    for _ in range(RUNS):
        start = time.perf_counter()
        workload()
        times.append(time.perf_counter() - start)
    return statistics.median(times)


@pytest.mark.parametrize("name", WORKLOADS)
def test_time(name, site):
    median = median_time(WORKLOADS[name])
    if os.environ.get("PERF_RECORD") == "1":
        recorded = json.loads(BASELINE.read_text()) if BASELINE.exists() else {}
        recorded[name] = median
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(recorded, indent=2, sort_keys=True) + "\n")
        return
    assert BASELINE.exists(), f"no baseline: run tests/run-tests.sh perf-baseline to record {BASELINE}"
    baseline = json.loads(BASELINE.read_text())[name]
    print(f"{name}: median {median * 1000:.1f} ms, baseline {baseline * 1000:.1f} ms, "
          f"ratio {median / baseline:.2f}")
    assert median <= THRESHOLD * baseline, f"{name}: {median:.4f} s against a baseline of {baseline:.4f} s"


@pytest.mark.parametrize("workload, rows, ceiling", [
    # Measured peaks: 1103 bytes per table row and 4411 per grid row, both mostly the
    # finished page text held whole before it is written. The ceilings allow a quarter more.
    (big_table, 20000, 1400),
    (big_grid, 2000, 5500),
])
def test_memory(workload, rows, ceiling, site):
    tracemalloc.start()
    try:
        workload(rows)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak / rows < ceiling, f"{workload.__name__}: {peak / rows:.0f} bytes per row"
