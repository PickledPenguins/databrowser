"""Raw, denoised and segmented versions of three microscope fields."""

from pathlib import Path

from databrowser import DataPage


def plot(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
                          '<circle cx="50" cy="50" r="30" fill="#8a8"/></svg>', encoding="utf-8")


stages = ["raw", "denoised", "segmented"]
page = DataPage("site/index.html", "Slide 14, DAPI channel", columns=3, column_titles=[s.title() for s in stages])
for field in ["F01", "F02", "F03"]:
    row = []
    for stage in stages:
        plot(f"site/{field}/{stage}.svg")
        row.append((f"{field}/{stage}.svg", field))
    page.add_row(row)
page.write()
