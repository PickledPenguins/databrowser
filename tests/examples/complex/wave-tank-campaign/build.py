"""A wave tank campaign: series of sweeps, each sweep a grid of plots per wave period."""

import dataclasses
from pathlib import Path

from databrowser import Badge, DataPage, GroupPage, Theme

PERIODS_S = [0.8, 1.0, 1.2, 1.4]
PLOTS = ["elevation", "probe", "spectrum"]
OFFLINE = {("series_A", "sweep_02", 1.2, "probe"), ("series_B", "sweep_01", 0.8, "probe"),
           ("series_B", "sweep_01", 1.0, "probe"), ("series_B", "sweep_01", 1.0, "spectrum")}


def plot(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>', encoding="utf-8")


plot("assets/waves.svg")
plot("assets/texture.svg")
theme = Theme(banner="Coastal Hydraulics Lab", banner_color="#0f3d3e", banner_image="assets/texture.svg",
              title_image="assets/waves.svg",
              bottom_banner="Coastal Hydraulics Lab - data@lab.example\nInternal data, do not share")
campaign = GroupPage("site/index.html", "Wave tank campaign 2026", ["Series", "Sweeps", "Missing", "Status"],
                     header="Tank B, regular waves", footer="Built 2026-10-30", theme=theme)
series_specs = [("series_A", "Flat bottom, depth 0.80 m", theme),
                ("series_B", "Sloped bottom 1:20", dataclasses.replace(theme, styles={"top-banner": "user-page"}))]
for series, description, series_theme in series_specs:
    series_page = GroupPage(f"site/{series}/index.html", series, ["Sweep", "H (cm)", "Periods", "Missing", "Status"],
                            header=description, parent=campaign, theme=series_theme)
    series_missing = 0
    for number, height_cm in enumerate([2.0, 4.0, None], start=1):
        sweep = f"sweep_{number:02d}"
        page = DataPage(f"site/{series}/{sweep}/index.html", sweep, columns=len(PLOTS),
                        column_titles=[name.title() for name in PLOTS], max_image_width_px=300,
                        header=f"H = {height_cm} cm" if height_cm else "H not measured",
                        footer="Made by reduce-tool 3.2.1", parent=series_page, theme=series_theme)
        missing = 0
        for period in PERIODS_S:
            row = []
            for name in PLOTS:
                if (series, sweep, period, name) in OFFLINE:
                    row.append((None, f"{name} offline"))
                    continue
                image = f"T{period}/{name}.svg"
                plot(f"site/{series}/{sweep}/{image}")
                row.append((image, f"T = {period} s\n{name}"))
            row_missing = sum(image is None for image, _ in row)
            missing += row_missing
            badge = Badge(f"{row_missing} missing", "warn") if row_missing else None
            page.add_row(row, label=f"Period T = {period} s", badge=badge)
        page.write()
        series_missing += missing
        status = Badge(f"{missing} missing", "warn") if missing else Badge("complete", "ok")
        series_page.add_row(page, [sweep, height_cm, len(PERIODS_S), missing, status])
    series_page.write()
    status = Badge("needs review", "warn") if series_missing else Badge("complete", "ok")
    campaign.add_row(series_page, [series, 3, series_missing, status])
campaign.write()
