"""A project page linking its sub-pages and its raw files alike."""

from pathlib import Path

from databrowser import GroupPage

index = GroupPage("site/index.html", "Bridge monitoring, span 3", ["Item", "Kind"])
details = GroupPage("site/sensors/index.html", "Sensors", ["Sensor"], parent=index)
details.write()
Path("site/docs").mkdir(parents=True)
Path("site/docs/install-report.pdf").write_bytes(b"%PDF-1.4\n")
Path("site/data").mkdir()
Path("site/data/strain-2026-10.csv").write_text("t,strain\n", encoding="utf-8")
index.add_row(details, ["Sensors", "page"])
index.add_row("docs/install-report.pdf", ["Installation report", "PDF"])
index.add_row(Path("data") / "strain-2026-10.csv", ["Strain, October", "CSV"])
index.write()
