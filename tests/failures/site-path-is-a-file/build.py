"""A file named site left where the site directory goes."""

from pathlib import Path

from databrowser import GroupPage

Path("site").write_text("notes\n", encoding="utf-8")
GroupPage("site/runs/index.html", "Runs", ["Run"]).write()
