"""A theme asking for big badges."""

from databrowser import GroupPage, Theme

GroupPage("site/index.html", "Runs", ["Run"], theme=Theme(styles={"badges": "big"})).write()
