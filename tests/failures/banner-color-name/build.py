"""A theme with the banner color written as a name."""

from databrowser import GroupPage, Theme

GroupPage("site/index.html", "Runs", ["Run"], theme=Theme(banner="Lab", banner_color="navy")).write()
