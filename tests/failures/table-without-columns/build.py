"""A table whose columns came from an empty header row."""

from databrowser import GroupPage

GroupPage("site/index.html", "Runs", []).write()
