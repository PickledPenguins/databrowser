"""A site built from absolute paths, as a script run from anywhere would make them."""

from pathlib import Path

from databrowser import GroupPage, Theme

root = Path.cwd() / "site"
(root / "art").mkdir(parents=True)
(root / "art" / "header.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 1"/>',
                                         encoding="utf-8")
theme = Theme(banner="Materials Testing", title_image=str(root / "art" / "header.svg"))
index = GroupPage(root / "index.html", "Fatigue tests", ["Specimen"], theme=theme)
specimen = GroupPage(root / "specimens" / "F-12" / "index.html", "F-12", ["Cycle block"], parent=index, theme=theme)
index.add_row(specimen, ["F-12"])
specimen.write()
index.write()
