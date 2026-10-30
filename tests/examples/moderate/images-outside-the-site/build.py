"""A report page over plots left where the analysis wrote them."""

import os
from pathlib import Path

from databrowser import DataPage

for name in ("pressure", "velocity", "vorticity"):
    Path(f"results/cfd/{name}.svg").parent.mkdir(parents=True, exist_ok=True)
    Path(f"results/cfd/{name}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>',
                                               encoding="utf-8")
page_path = Path("site/report/index.html")
page = DataPage(page_path, "Cylinder wake, Re = 3900", columns=3, column_titles=["p", "|u|", "omega_z"])
# Image paths are relative to the page, so turn each result path into one.
page.add_row([(os.path.relpath(f"results/cfd/{name}.svg", page_path.parent), f"t = 120 s, {name}")
              for name in ("pressure", "velocity", "vorticity")], label="Mid-span slice")
page.write()
