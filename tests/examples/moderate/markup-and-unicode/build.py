"""Pages whose names and notes contain markup characters and several scripts."""

from pathlib import Path

from databrowser import Badge, DataPage, GroupPage

index = GroupPage("site/index.html", "Results <draft> & notes", ["Sample", "λ (nm)", "Note"],
                  header='Contains "quoted" text & <tags>', footer="© Lab für Optik")
page = DataPage("site/sample/index.html", "測定 1: α < β", columns=2, column_titles=["I(λ)", "Phase <rad>"], parent=index)
for name in ("intensity", "phase"):
    Path(f"site/sample/{name}.svg").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/sample/{name}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>',
                                               encoding="utf-8")
page.add_row([("intensity.svg", "peak at 532 nm & 1064 nm"), ("phase.svg", "unwrapped <-pi, pi>")],
             label="Sample \u00e9t\u00e9 'A'", badge=Badge("check <units>", "warn"))
page.write()
index.add_row(page, ["測定 1", 532, "a 'quoted' & <b>bold</b> note"])
index.write()
