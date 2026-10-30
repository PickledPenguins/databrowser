"""A nightly build run twice: yesterday's data, then today's."""

from pathlib import Path

from databrowser import Badge, DataPage, GroupPage, Theme


def build(runs, color):
    theme = Theme(banner="Detector QA", banner_color=color)
    index = GroupPage("site/index.html", "QA runs", ["Run", "Events", "Status"], theme=theme)
    for run, events, ok in runs:
        page = DataPage(f"site/{run}/index.html", run, columns=1, parent=index, theme=theme)
        Path(f"site/{run}/hits.svg").parent.mkdir(parents=True, exist_ok=True)
        Path(f"site/{run}/hits.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>',
                                                encoding="utf-8")
        page.add_row([("hits.svg", f"{events} events")], label=run)
        page.write()
        index.add_row(page, [run, events, Badge("pass", "ok") if ok else Badge("fail", "error")])
    index.write()


build([("run-01", 10200, True), ("run-02", 9800, False)], "#334155")
build([("run-01", 10200, True), ("run-02b", 9950, True), ("run-03", 11020, True)], "#7c2d12")
