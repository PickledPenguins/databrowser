"""A row whose badge is given as plain text instead of a Badge."""

from databrowser import DataPage

page = DataPage("site/index.html", "Sweep 1", columns=1)
page.add_row([("elevation.png", "max 3.1 cm")], badge="1 missing")
page.write()
