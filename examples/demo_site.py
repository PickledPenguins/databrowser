"""Build a small demo site: a top page listing series, a page per series listing its sweeps,
and a page per sweep with a grid of images. The images are made-up SVG plots.

    PYTHONPATH=src python examples/demo_site.py [OUTPUT_DIR]

OUTPUT_DIR defaults to .build/demo-site. Open index.html in it.
"""

import math
import sys
from pathlib import Path

from databrowser import Badge, DataPage, GroupPage, Theme

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


def write_title_image(path: Path) -> None:
    """Write a wide SVG of layered waves to show behind page titles."""
    layers = []
    for layer, color in enumerate(["#1d4f91", "#2b6fd6", "#5b95f0", "#9cc2ff"]):
        base = 120 + layer * 45
        points = " ".join(f"{x},{base + (18 - layer * 3) * math.sin(x / (90 + layer * 25) + layer):.1f}"
                          for x in range(0, 1601, 20))
        layers.append(f'<polygon points="0,400 {points} 1600,400" fill="{color}" opacity="0.55"/>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 400" preserveAspectRatio="none">'
                    f'<rect width="1600" height="400" fill="#0b1f3f"/>{"".join(layers)}</svg>', encoding="utf-8")


def write_sweep(folder: Path, height_cm: float, parent: GroupPage) -> int:
    """Write a sweep's images and its data page, one row per wave period. Return how many images are missing."""
    page = DataPage(folder / "index.html", folder.name, columns=len(PLOTS), header=f"Regular waves, H = {height_cm} cm",
                    footer="Made by reduce-tool 3.2.1", column_titles=[plot.title() for plot in PLOTS],
                    max_image_width_px=300, parent=parent, theme=parent.theme)
    missing = 0
    for row, period in enumerate(PERIODS_S):
        images = []
        for column, plot in enumerate(PLOTS):
            if folder.name == "sweep_03" and period == 1.4 and plot == "probe":
                images.append((None, "probe 4 offline"))
                continue
            image = f"T{period}/{plot}.svg"
            write_plot(folder / image, frequency=1 + column + row * 0.5, damping=height_cm)
            images.append((image, f"max {2 + row * 0.3:.2f} cm\nrms {0.7 + row * 0.1 + column * 0.05:.2f} cm"))
        row_missing = sum(image is None for image, _ in images)
        missing += row_missing
        badge = Badge(f"{row_missing} missing", "warn") if row_missing else None
        page.add_row(images, label=f"Period T = {period} s", badge=badge)
    page.write()
    return missing


def write_series(folder: Path, parent: GroupPage) -> GroupPage:
    """Write a series' sweeps and its group page listing them, and return that page."""
    page = GroupPage(folder / "index.html", folder.name, ["Sweep", "Wave height (cm)", "Periods", "Status"],
                     header="Flat bottom, depth 0.80 m", footer="Built 2026-10-30", parent=parent, theme=parent.theme)
    for number, height_cm in enumerate([2.0, 4.0, 6.0], start=1):
        sweep = f"sweep_{number:02d}"
        missing = write_sweep(folder / sweep, height_cm, page)
        status = Badge(f"{missing} image missing", "warn") if missing else Badge("complete", "ok")
        page.add_row(f"{sweep}/index.html", [sweep, height_cm, len(PERIODS_S), status])
    page.write()
    return page


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".build/demo-site")
    write_title_image(root / "title.svg")
    theme = Theme(banner="Coastal Hydraulics Lab", title_image=str(root / "title.svg"))
    page = GroupPage(root / "index.html", "Wave tank campaign 2026", ["Series", "Sweeps", "Notes", "Status"],
                     header="Tank B. Each row is a test series.", footer="Built 2026-10-30", theme=theme)
    for series, notes, status in [("series_A", "Baseline", Badge("needs review", "warn")),
                                  ("series_B", "Sloped bottom 1:20", Badge("in progress", "info"))]:
        page.add_row(write_series(root / series, page), [series, 3, notes, status])
    page.write()
    print(root / "index.html")


if __name__ == "__main__":
    main()
