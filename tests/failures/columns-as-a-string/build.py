"""A table given one column name as a string instead of a list."""

from databrowser import GroupPage

page = GroupPage("site/index.html", "Runs", "Run")
page.add_row("run-01.html", ["run-01"])
page.write()
