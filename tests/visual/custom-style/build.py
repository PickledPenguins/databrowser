"""The shipped custom banner style next to a page with its own banner color: two pages of one
site, each with its own Theme."""

import dataclasses

from databrowser import Badge, GroupPage, Theme

theme = Theme(banner="Coastal Hydraulics Lab", bottom_banner="Contact: waves@example.org", banner_color="#e0b030")
top = GroupPage("site/index.html", "Campaigns", ["Campaign", "Status"], theme=theme)
user = GroupPage("site/users/ana/index.html", "Ana's runs", ["Run", "Status"], parent=top,
                 theme=dataclasses.replace(theme, banner="Ana Ruiz", styles={"top-banner": "user-page"}))
user.add_row("run-1/index.html", ["run-1", Badge("complete", "ok")])
top.add_row(user, ["Ana's runs", Badge("in progress", "info")])
top.write()
user.write()
