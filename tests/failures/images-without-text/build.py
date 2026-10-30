"""A row given as image paths alone."""

from databrowser import DataPage

page = DataPage("site/index.html", "Sweep 1", columns=2)
page.add_row(["elevation.png", "probe.png"])
page.write()
