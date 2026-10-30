"""A week of sea surface temperature maps."""

from pathlib import Path

from databrowser import DataPage

page = DataPage("site/index.html", "SST, North Atlantic, week 43", columns=1, max_image_width_px=720)
for day in range(20, 27):
    image = f"maps/2026-10-{day}.svg"
    Path(f"site/{image}").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/{image}").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1"/>', encoding="utf-8")
    page.add_row([(image, "daily mean, 0.25 deg grid")], label=f"2026-10-{day}")
page.write()
