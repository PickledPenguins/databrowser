"""Eight-direction cross-sections of a particle shower, a row per energy."""

from pathlib import Path

from databrowser import DataPage

angles = [f"{angle} deg" for angle in range(0, 360, 45)]
page = DataPage("site/index.html", "Shower profiles", columns=8, column_titles=angles, max_image_width_px=120)
for energy in (10, 50, 100):
    row = []
    for angle in range(0, 360, 45):
        image = f"E{energy}/a{angle:03d}.svg"
        Path(f"site/{image}").parent.mkdir(parents=True, exist_ok=True)
        Path(f"site/{image}").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>',
                                         encoding="utf-8")
        row.append((image, f"{energy} GeV"))
    page.add_row(row, label=f"E = {energy} GeV")
page.write()
