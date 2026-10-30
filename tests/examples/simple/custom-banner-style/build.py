"""A personal results page set apart by the user-page banner style."""

from databrowser import GroupPage, Theme

theme = Theme(banner="Jo's scratch results", styles={"top-banner": "user-page"})
GroupPage("site/index.html", "Unreviewed runs", ["Run", "Date"], theme=theme).write()
