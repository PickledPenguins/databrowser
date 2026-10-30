"""Build a small demo site: a top page listing series, a page per series listing its sweeps,
and a page per sweep with a grid of images. The images are made-up SVG plots.

    PYTHONPATH=src python examples/demo_site.py [OUTPUT_DIR]

OUTPUT_DIR defaults to .build/demo-site. Open index.html in it.
"""

import math
import sys
from pathlib import Path

from databrowser import DataPage, GroupPage

PERIODS_S = [0.8, 1.0, 1.2, 1.4, 1.6]
PLOTS = ["elevation", "probe", "spectrum"]


def write_plot(path: Path, frequency: float, damping: float) -> None:
    """Write a damped sine curve as an SVG file, standing in for an image a reader tool makes."""
    points = " ".join(f"{20 + x},{90 - 60 * math.exp(-damping * x / 200) * math.sin(frequency * x / 30):.1f}"
                      for x in range(0, 201, 4))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 180">'
                    '<rect width="240" height="180" fill="#fff"/><path d="M20 10V170H230" stroke="#888" fill="none"/>'
                    f'<polyline points="{points}" stroke="#2f5fa7" stroke-width="1.6" fill="none"/></svg>',
                    encoding="utf-8")


def write_sweep(folder: Path, height_cm: float) -> None:
    """Write a sweep's images and its data page, one row per wave period."""
    page = DataPage(folder.name, columns=len(PLOTS), header=f"Regular waves, H = {height_cm} cm",
                    footer="Made by reduce-tool 3.2.1")
    for row, period in enumerate(PERIODS_S):
        images = []
        for column, plot in enumerate(PLOTS):
            if folder.name == "sweep_03" and period == 1.4 and plot == "probe":
                images.append((None, f"T = {period} s\nprobe 4 offline"))
                continue
            image = f"T{period}/{plot}.svg"
            write_plot(folder / image, frequency=1 + column + row * 0.5, damping=height_cm)
            images.append((image, f"T = {period} s, {plot}\nmax {2 + row * 0.3:.2f} cm"))
        page.add_row(images)
    page.write(folder / "index.html")


def write_series(folder: Path) -> None:
    """Write a series' sweeps and its group page listing them."""
    page = GroupPage(folder.name, ["Sweep", "Wave height", "Periods", "Status"], header="Flat bottom, depth 0.80 m")
    for number, height_cm in enumerate([2.0, 4.0, 6.0], start=1):
        sweep = f"sweep_{number:02d}"
        write_sweep(folder / sweep, height_cm)
        status = "1 image missing" if sweep == "sweep_03" else "ok"
        page.add_row(f"{sweep}/index.html", [sweep, f"{height_cm} cm", len(PERIODS_S), status])
    page.write(folder / "index.html")


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".build/demo-site")
    page = GroupPage("Wave tank campaign 2026", ["Series", "Sweeps", "Notes"],
                     header="Tank B. Each row is a test series.", footer="Built 2026-10-30")
    for series, notes in [("series_A", "Baseline"), ("series_B", "Sloped bottom 1:20")]:
        write_series(root / series)
        page.add_row(f"{series}/index.html", [series, 3, notes])
    page.write(root / "index.html")
    print(root / "index.html")


if __name__ == "__main__":
    main()
