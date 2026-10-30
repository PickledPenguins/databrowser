"""A table of survey lines with a two-line description and a provenance footer."""

from pathlib import Path

from databrowser import GroupPage

index = GroupPage("site/index.html", "Bathymetry survey, Loch Fyne", ["Line", "Length (km)"],
                  header="Multibeam, 2026-05-12 to 2026-05-16\nDepths reduced to chart datum",
                  footer="Processed with swathed 4.1\nContact: survey team")
for line, length in [("L001", 12.4), ("L002", 12.1), ("L003", 11.8)]:
    Path(f"site/{line}.xyz").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/{line}.xyz").write_text("x y z\n", encoding="utf-8")
    index.add_row(f"{line}.xyz", [line, length])
index.write()
