"""A public and an internal site built with the same look."""

from databrowser import GroupPage, Theme

theme = Theme(banner="Ocean Mixing Group", banner_color="#0b3954", bottom_banner="Ocean Mixing Group")
for site, title in [("public", "Released datasets"), ("internal", "Working data")]:
    top = GroupPage(f"{site}/index.html", title, ["Cruise"], theme=theme)
    cruise = GroupPage(f"{site}/cruises/JC251/index.html", "JC251", ["Cast"], parent=top, theme=theme)
    top.add_row(cruise, ["JC251"])
    cruise.write()
    top.write()
