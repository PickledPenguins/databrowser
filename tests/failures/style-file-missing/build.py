"""A theme naming a table style nobody wrote."""

from databrowser import GroupPage, Theme

GroupPage("site/index.html", "Runs", ["Run"], theme=Theme(styles={"table": "compact"})).write()
