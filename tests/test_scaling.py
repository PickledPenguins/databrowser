"""Cost against size, one dimension at a time: table rows, image rows, and the depth of a page
below the top. Each doubling or quadrupling must cost about that much more, not its square;
the bound on the ratio of per-item times is loose enough for timing noise and tight enough
that a quadratic step fails it."""

import functools
import time

import pytest

from databrowser import Badge, DataPage, GroupPage

pytestmark = pytest.mark.long

# Per-item time at the largest size may be at most this many times that at the smallest. A
# quadratic step over a 16-fold growth would give 16.
RATIO = 4


def best_time(build, repeats: int = 3) -> float:
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        build()
        times.append(time.perf_counter() - start)
    return min(times)


def per_item(build, sizes) -> list[float]:
    return [best_time(functools.partial(build, size)) / size for size in sizes]


def test_table_rows(site):
    def build(rows):
        page = GroupPage("index.html", "Top", ["Name", "Images", "Size", "Status"])
        for row in range(rows):
            page.add_row(f"run-{row}/index.html", [f"run-{row}", row, row * 1.5, Badge("ok", "ok")])
        page.write()

    small, large = per_item(build, (2000, 32000))
    assert large < RATIO * small, (small, large)


def test_image_rows(site):
    def build(rows):
        page = DataPage("index.html", "Grid", columns=4, column_titles=["a", "b", "c", "d"])
        for row in range(rows):
            page.add_row([(f"img/{row}-{column}.png", f"row {row}\ncolumn {column}") for column in range(4)],
                         label=f"row {row}", badge=Badge("1 missing", "warn"))
        page.write()

    small, large = per_item(build, (500, 8000))
    assert large < RATIO * small, (small, large)


def test_depth_below_the_top(site):
    """Each page links every page above it, by a path as long as its depth, so a page's cost
    grows with the square of its depth, from a base that dominates at any real depth: per
    page 0.7 ms at depth 10, 1.0 ms at 40 and 4 ms at 160. The bound catches anything worse
    than that over the depths a site has."""
    def build(depth):
        parent = None
        for level in range(depth):
            page = GroupPage("/".join(["d"] * level + ["index.html"]), f"level {level}", ["Name"], parent=parent)
            page.write()
            parent = page

    small, large = per_item(build, (10, 40))
    assert large < RATIO * small, (small, large)
