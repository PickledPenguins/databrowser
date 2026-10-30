"""Latest runs of every campaign, linked from one front page."""

from pathlib import Path

from databrowser import DataPage, GroupPage

latest = GroupPage("site/index.html", "Latest runs", ["Run", "Campaign"])
for campaign, tank, run in [("2026", "tank-b", "run-07"), ("2025", "flume", "run-31")]:
    folder = f"site/campaigns/{campaign}/{tank}/{run}"
    Path(f"{folder}/overview.svg").parent.mkdir(parents=True, exist_ok=True)
    Path(f"{folder}/overview.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>',
                                              encoding="utf-8")
    page = DataPage(f"{folder}/index.html", run, columns=1, parent=latest)
    page.add_row([("overview.svg", f"{tank} {run}")])
    page.write()
    latest.add_row(page, [run, f"{campaign} {tank}"])
latest.write()
