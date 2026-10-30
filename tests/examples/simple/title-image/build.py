"""A page with an aurora picture behind its title, the picture kept outside the site."""

from pathlib import Path

from databrowser import GroupPage, Theme

Path("art").mkdir(exist_ok=True)
Path("art/aurora.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 2">'
                                  '<rect width="8" height="2" fill="#1b4"/></svg>', encoding="utf-8")
theme = Theme(title_image="art/aurora.svg")
GroupPage("site/index.html", "All-sky camera, winter 2026", ["Night", "Frames"], theme=theme).write()
