"""Two plates of a screen, four channels per well, a few wells not imaged."""

from pathlib import Path

from databrowser import Badge, DataPage, GroupPage, Theme


def plot(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>', encoding="utf-8")


plot("assets/cells.svg")
theme = Theme(banner="High-content screening core", title_image="assets/cells.svg")
channels = ["DAPI", "GFP", "mCherry", "Brightfield"]
not_imaged = {("P01", "B3", "GFP"), ("P02", "A1", "DAPI"), ("P02", "A1", "GFP")}
screen = GroupPage("site/index.html", "Kinase inhibitor screen", ["Plate", "Wells", "Missing", "Status"], theme=theme)
for plate in ("P01", "P02"):
    page = DataPage(f"site/{plate}/index.html", f"Plate {plate}", columns=4, column_titles=channels,
                    max_image_width_px=180, parent=screen, theme=theme, header="20x objective, 9 fields per well")
    missing = 0
    for well in ("A1", "A2", "B3"):
        row = []
        for channel in channels:
            if (plate, well, channel) in not_imaged:
                row.append((None, f"{well} {channel}"))
                continue
            plot(f"site/{plate}/{well}/{channel}.svg")
            row.append((f"{well}/{channel}.svg", f"{well} {channel}"))
        row_missing = sum(image is None for image, _ in row)
        missing += row_missing
        page.add_row(row, label=f"Well {well}", badge=Badge(f"{row_missing} not imaged", "warn") if row_missing else None)
    page.write()
    status = Badge("complete", "ok") if not missing else Badge("re-image", "warn")
    screen.add_row(page, [plate, 3, missing, status])
screen.write()
