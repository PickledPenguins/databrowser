"""A data page: column titles, row labels with badges, captions of two lines, a missing image,
a capped image width and a darkened banner image."""

from databrowser import Badge, DataPage, GroupPage, Theme
from svg import plot

plot("assets/banner.svg", 30, [9, 9, 9, 9], width=1200, height=80)
theme = Theme(banner="Coastal Hydraulics Lab", banner_image="assets/banner.svg")
top = GroupPage("site/index.html", "Wave tank campaign 2026", ["Sweep"], theme=theme)
page = DataPage("site/sweep_03/index.html", "sweep_03", columns=3, column_titles=["Elevation", "Probe", "Spectrum"],
                max_image_width_px=260, parent=top, theme=theme, header="Regular waves, stroke 40 mm")
for row, period in enumerate(("0.8", "1.2")):
    images = []
    for column, hue in enumerate((210, 140, 20)):
        if (row, column) == (1, 1):
            images.append((None, "probe offline"))
            continue
        plot(f"site/sweep_03/T{period}/{column}.svg", hue, [(row * 3 + column + i) % 10 + 1 for i in range(6)])
        images.append((f"T{period}/{column}.svg", f"T = {period} s\nmax {row + column + 2}.{column} cm"))
    page.add_row(images, label=f"T = {period} s", badge=Badge("1 image missing", "warn") if row else None)
top.add_row(page, ["sweep_03"])
top.write()
page.write()
