"""A page rewritten after each night's observations come in."""

from pathlib import Path

from databrowser import Badge, GroupPage

page = GroupPage("site/index.html", "Telescope nights", ["Night", "Frames", "Seeing (arcsec)", "Status"])
for night, frames, seeing in [("2026-10-25", 212, 1.1), ("2026-10-26", 0, None), ("2026-10-27", 188, 0.9),
                              ("2026-10-28", 240, 1.4)]:
    Path(f"site/{night}.log").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/{night}.log").write_text("night\n", encoding="utf-8")
    status = Badge("clouded out", "info") if frames == 0 else Badge("observed", "ok")
    page.add_row(f"{night}.log", [night, frames, seeing, status])
    page.write()
