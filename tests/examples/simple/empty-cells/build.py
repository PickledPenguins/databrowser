"""Boreholes, some not yet logged to their final depth or not yet described."""

from pathlib import Path

from databrowser import GroupPage

holes = [("BH-01", 42.5, "clay over sandstone"), ("BH-02", None, None), ("BH-03", 18.0, None),
         ("BH-04", 61.2, "weathered granite")]
index = GroupPage("site/index.html", "Site investigation boreholes", ["Borehole", "Depth (m)", "Notes"])
for name, depth, notes in holes:
    Path(f"site/{name}.pdf").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/{name}.pdf").write_bytes(b"%PDF-1.4\n")
    index.add_row(f"{name}.pdf", [name, depth, notes])
index.write()
