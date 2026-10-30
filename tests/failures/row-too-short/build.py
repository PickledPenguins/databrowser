"""A run whose status was forgotten in its row."""

from databrowser import GroupPage

page = GroupPage("site/index.html", "Runs", ["Run", "Events", "Status"])
page.add_row("run-01.html", ["run-01", 10200])
page.write()
