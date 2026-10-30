"""Build a small demo site with databrowser: a top table of series, a table of sweeps per
series, and an image grid per sweep. Images are made-up SVG plots written alongside.

    PYTHONPATH=src python examples/demo_site.py [OUTPUT_DIR]

OUTPUT_DIR defaults to .build/demo-site. Open index.html in it.
"""

import math
import sys
from pathlib import Path

from databrowser import Image, ImageGrid, Link, Missing, Page, Section, Status, Table

PERIODS_S = [0.8, 1.0, 1.2, 1.4, 1.6]
PLOTS = ["Surface elevation", "Probe time series", "Spectrum"]


def write_plot(path: Path, frequency: float, damping: float) -> None:
    """Write a damped sine curve as an SVG file, standing in for an image a reader tool makes."""
    points = " ".join(f"{20 + x},{90 - 60 * math.exp(-damping * x / 200) * math.sin(frequency * x / 30):.1f}"
                      for x in range(0, 201, 4))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 180">'
                    '<rect width="240" height="180" fill="#fff"/><path d="M20 10V170H230" stroke="#888" fill="none"/>'
                    f'<polyline points="{points}" stroke="#2f5fa7" stroke-width="1.6" fill="none"/></svg>',
                    encoding="utf-8")


def build_sweep(root: Path, series: str, sweep: str, height_cm: float, crumbs: list[Link]) -> list[str]:
    """Write one sweep's images and its image grid page. Return the site paths of its images."""
    grid = ImageGrid(columns=PLOTS)
    image_paths = []
    for row, period in enumerate(PERIODS_S):
        cells = []
        for column, plot in enumerate(PLOTS):
            if sweep == "sweep_03" and period == 1.4 and column == 1:
                cells.append(Missing(caption="probe 4 offline"))
                continue
            image_path = f"{series}/{sweep}/T{period}/{column}.svg"
            write_plot(root / image_path, frequency=1 + column + row * 0.5, damping=height_cm)
            image_paths.append(image_path)
            cells.append(Image(image_path, caption=[f"max {2 + row * 0.3:.2f} cm", "t 0..120 s"], alt=plot))
        grid.add_row(cells, label=[f"T = {period} s", f"run {301 + row}"])
    page = Page(f"{series}/{sweep}/index.html", sweep, crumbs=crumbs,
                header=Section(title=sweep, text=f"Regular waves, H = {height_cm} cm.",
                               meta={"Records": len(PERIODS_S), "Duration": "120 s each"}),
                footer=Section(meta={"Tool": "reduce-tool 3.2.1", "Source": f"/data/{series}/{sweep}"}))
    page.add(grid)
    page.write(root)
    return image_paths


def build_series(root: Path, series: str, home: Link) -> int:
    """Write a series' sweeps and its table page. Return how many images it holds."""
    table = Table(["Name", "Preview", "Rows", "Height (cm)", "Status"])
    series_link = Link(series, f"{series}/index.html")
    total_images = 0
    for number, height_cm in enumerate([2.0, 4.0, 6.0], start=1):
        sweep = f"sweep_{number:02d}"
        image_paths = build_sweep(root, series, sweep, height_cm, crumbs=[home, series_link])
        total_images += len(image_paths)
        target = f"{series}/{sweep}/index.html"
        status = Status("1 missing", "warn") if sweep == "sweep_03" else Status("ok")
        preview = [Image(path) for path in image_paths[:2]]
        table.add_row([Link(sweep, target), preview, len(PERIODS_S), height_cm, status], target=target)
    page = Page(f"{series}/index.html", series, crumbs=[home],
                header=Section(title=series, meta={"Depth": "0.80 m", "Probes": 6}))
    page.add(table)
    page.write(root)
    return total_images


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".build/demo-site")
    home = Link("Campaign 2026", "index.html")
    table = Table(["Name", "Images", "Status", "Notes"])
    for series, notes in [("series_A", "Baseline, flat bottom"), ("series_B", "Sloped bottom 1:20")]:
        target = f"{series}/index.html"
        images = build_series(root, series, home)
        table.add_row([Link(series, target), images, Status("complete"), notes], target=target)
    page = Page("index.html", "Campaign 2026",
                header=Section(title="Wave tank campaign 2026", text="Rows are test series.",
                               meta={"Facility": "Tank B", "Series": 2}),
                footer=Section(meta={"Builder": "databrowser 0.1"}))
    page.add(table)
    print(page.write(root))


if __name__ == "__main__":
    main()
