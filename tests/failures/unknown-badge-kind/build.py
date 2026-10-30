"""A status badge with a kind spelled out in full."""

from databrowser import Badge, GroupPage

page = GroupPage("site/index.html", "Runs", ["Run", "Status"])
page.add_row("run-01.html", ["run-01", Badge("2 warnings", "warning")])
page.write()
