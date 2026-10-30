"""Wave gauge records with their statistics under each."""

from pathlib import Path

from databrowser import DataPage

page = DataPage("site/index.html", "Gauge records, H = 4 cm", columns=2)
row = []
for gauge, high, rms in [("WG1", 3.1, 1.2), ("WG2", 2.8, 1.1)]:
    Path(f"site/{gauge}.svg").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/{gauge}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>',
                                         encoding="utf-8")
    row.append((f"{gauge}.svg", f"max {high} cm\nrms {rms} cm\ngauge {gauge}"))
page.add_row(row)
page.write()
