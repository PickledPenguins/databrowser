"""A site where the drafts page stands out from the reviewed results."""

import dataclasses

from databrowser import GroupPage, Theme

theme = Theme(banner="Acoustics Lab", banner_color="#263238", bottom_banner="Acoustics Lab")
drafts_theme = dataclasses.replace(theme, banner_color="#b45309", styles={"top-banner": "user-page"})
index = GroupPage("site/index.html", "Reverberation measurements", ["Room", "Status"], theme=theme)
drafts = GroupPage("site/drafts/index.html", "Drafts, not reviewed", ["Room"], parent=index, theme=drafts_theme)
index.add_row(drafts, ["Drafts", "unreviewed"])
drafts.write()
index.write()
