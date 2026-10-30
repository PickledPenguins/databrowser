"""A group page under a top page: banners, breadcrumbs, a title band over an image, header
and footer text, a table with a number column and badges of every kind."""

from databrowser import Badge, GroupPage, Theme
from svg import plot

plot("assets/title.svg", 200, [3, 5, 8, 6, 9, 4, 7, 2], width=1200, height=300)
theme = Theme(banner="Coastal Hydraulics Lab", bottom_banner="Contact: waves@example.org\nData policy: internal",
              title_image="assets/title.svg")
top = GroupPage("site/index.html", "Wave tank campaign 2026", ["Series", "Runs"], theme=theme)
series = GroupPage("site/series_A/index.html", "Series A: regular waves", ["Sweep", "Runs", "Peak (cm)", "Status"],
                   header="Paddle stroke sweeps at 0.8 to 1.6 s periods.\nProbe 4 was recalibrated on day 2.",
                   footer="Processed with tankproc 3.2", parent=top, theme=theme)
for name, runs, peak, status in [("sweep_01", 12, 3.1, Badge("complete", "ok")),
                                 ("sweep_02", 12, 4.75, Badge("reprocessed", "info")),
                                 ("sweep_03", 11, 6.2, Badge("1 run missing", "warn")),
                                 ("sweep_04", 0, None, Badge("probe failure", "error"))]:
    series.add_row(f"{name}/index.html", [name, runs, peak, status])
top.add_row(series, ["Series A", 4])
top.write()
series.write()
