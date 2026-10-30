"""Camera frames of one test, one camera having failed to trigger."""

from pathlib import Path

from databrowser import DataPage

page = DataPage("site/index.html", "Drop test 3, t = 12 ms", columns=3, column_titles=["Cam 1", "Cam 2", "Cam 3"])
row = []
for camera in (1, 2, 3):
    if camera == 2:
        row.append((None, "no trigger"))
        continue
    Path(f"site/cam{camera}.svg").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/cam{camera}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>',
                                             encoding="utf-8")
    row.append((f"cam{camera}.svg", f"frame 0412, camera {camera}"))
page.add_row(row)
page.write()
