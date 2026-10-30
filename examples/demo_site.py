"""Build a small demo site with databrowser: a top table of series, a table of sweeps per
series, and an image grid per sweep. Images are made-up SVG plots written alongside.

    PYTHONPATH=src python examples/demo_site.py [OUTPUT_DIR]

OUTPUT_DIR defaults to .build/demo-site. Open index.html in it.
"""

import math
import posixpath
import sys
from pathlib import Path

from databrowser import (GridLayout, HBoxLayout, Image, ImageControls, KeyValue, Label, Link, Page, Placeholder,
                         Status, Table)

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


def build_sweep(root: Path, page: Page, sweep: str, height_cm: float) -> list[str]:
    """Write one sweep's images and fill its page with an image grid. Return the site paths of its images."""
    page.header.add_widget(Label(sweep, style="title"))
    page.header.add_widget(Label(f"Regular waves, H = {height_cm} cm.", style="muted"))
    page.header.add_widget(KeyValue({"Records": len(PERIODS_S), "Duration": "120 s each"}))
    sweep_dir = posixpath.dirname(page.path)
    page.add_widget(ImageControls())
    grid = page.add_layout(GridLayout(spacing_px=2))
    for column, plot in enumerate(PLOTS, start=1):
        grid.add_widget(Label(plot, style="heading"), row=0, column=column)
    image_paths = []
    for row, period in enumerate(PERIODS_S, start=1):
        grid.add_widget(Label([f"T = {period} s", f"run {300 + row}"], style="mono"), row=row, column=0)
        for column, plot in enumerate(PLOTS, start=1):
            if sweep == "sweep_03" and period == 1.4 and column == 2:
                grid.add_widget(Placeholder(caption="probe 4 offline"), row, column)
                continue
            image_path = f"{sweep_dir}/T{period}/{column}.svg"
            write_plot(root / image_path, frequency=column + row * 0.5, damping=height_cm)
            image_paths.append(image_path)
            grid.add_widget(Image(image_path, caption=[f"max {2 + row * 0.3:.2f} cm", "t 0..120 s"], alt=plot),
                            row, column)
    page.footer.add_widget(KeyValue({"Tool": "reduce-tool 3.2.1", "Source": f"/data/{sweep_dir}"}))
    return image_paths


def build_series(root: Path, page: Page, series: str) -> int:
    """Write a series' sweep pages and fill its page with a table of them. Return how many images the series holds."""
    page.header.add_widget(Label(series, style="title"))
    page.header.add_widget(KeyValue({"Depth": "0.80 m", "Probes": 6}))
    table = page.add_widget(Table(["Name", "Preview", "Rows", "Height (cm)", "Status"]))
    sweeps = [f"sweep_{number:02d}" for number in range(1, 4)]
    total_images = 0
    for number, sweep in enumerate(sweeps):
        height_cm = 2.0 * (number + 1)
        sweep_page = page.child(f"{series}/{sweep}/index.html", sweep)
        if number > 0:
            sweep_page.nav.add_widget(Link(f"< {sweeps[number - 1]}", f"{series}/{sweeps[number - 1]}/index.html"))
        if number < len(sweeps) - 1:
            sweep_page.nav.add_widget(Link(f"{sweeps[number + 1]} >", f"{series}/{sweeps[number + 1]}/index.html"))
        image_paths = build_sweep(root, sweep_page, sweep, height_cm)
        sweep_page.write(root)
        total_images += len(image_paths)
        preview = HBoxLayout(spacing_px=2)
        for path in image_paths[:2]:
            preview.add_widget(Image(path, height_px=28))
        status = Status("1 missing", "warn") if sweep == "sweep_03" else Status("ok")
        table.add_row([Link(sweep, sweep_page.path), preview, len(PERIODS_S), height_cm, status],
                      target=sweep_page.path)
    return total_images


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".build/demo-site")
    home = Page("index.html", "Campaign 2026")
    home.header.add_widget(Label("Wave tank campaign 2026", style="title"))
    home.header.add_widget(Label("Rows are test series.", style="muted"))
    home.header.add_widget(KeyValue({"Facility": "Tank B", "Series": 2}))
    table = home.add_widget(Table(["Name", "Images", "Status", "Notes"]))
    for series, notes in [("series_A", "Baseline, flat bottom"), ("series_B", "Sloped bottom 1:20")]:
        series_page = home.child(f"{series}/index.html", series)
        images = build_series(root, series_page, series)
        series_page.write(root)
        table.add_row([Link(series, series_page.path), images, Status("complete"), notes], target=series_page.path)
    home.footer.add_widget(KeyValue({"Builder": "databrowser 0.1"}))
    print(home.write(root))


if __name__ == "__main__":
    main()
