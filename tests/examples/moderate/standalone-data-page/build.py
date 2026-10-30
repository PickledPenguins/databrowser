"""One self-contained report page of a beam test."""

from pathlib import Path

from databrowser import DataPage, Theme

for name in ("strain", "deflection", "title"):
    Path(f"img/{name}.svg").parent.mkdir(parents=True, exist_ok=True)
    Path(f"img/{name}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>', encoding="utf-8")
theme = Theme(banner="Structures Lab", bottom_banner="Structures Lab, bay 2", title_image="img/title.svg")
page = DataPage("report.html", "Four-point bend, beam B12", columns=2, header="Load to failure at 2 mm/min",
                footer="Rig: Instron 8802", max_image_width_px=400, theme=theme)
page.add_row([("img/strain.svg", "gauge SG3"), ("img/deflection.svg", "LVDT 1")], label="Elastic range")
page.write()
