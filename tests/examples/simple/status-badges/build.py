"""Nightly pipeline jobs and how each one ended."""

from pathlib import Path

from databrowser import Badge, GroupPage

jobs = [("ingest", Badge("passed", "ok")), ("calibrate", Badge("skipped: no new data", "info")),
        ("reduce", Badge("2 warnings", "warn")), ("publish", Badge("failed", "error"))]
index = GroupPage("site/index.html", "Nightly pipeline 2026-10-29", ["Job", "Result"])
for job, result in jobs:
    Path(f"site/logs/{job}.log").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/logs/{job}.log").write_text("log\n", encoding="utf-8")
    index.add_row(f"logs/{job}.log", [job, result])
index.write()
