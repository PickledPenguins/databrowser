"""A lab's front page with its name in a banner."""

from pathlib import Path

from databrowser import GroupPage, Theme

theme = Theme(banner="Soft Matter Group")
index = GroupPage("site/index.html", "Rheometer data", ["Sample", "Viscosity (Pa s)"], theme=theme)
for sample, viscosity in [("PEO-2", 1.8), ("PEO-5", 6.4)]:
    Path(f"site/{sample}.csv").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/{sample}.csv").write_text("rate,stress\n", encoding="utf-8")
    index.add_row(f"{sample}.csv", [sample, viscosity])
index.write()
