"""Two small spectra, kept at their natural width."""

from pathlib import Path

from databrowser import DataPage

page = DataPage("site/index.html", "Sample 88, Raman spectra", columns=2, max_image_width_px=320)
row = []
for laser in ("532nm", "785nm"):
    Path(f"site/{laser}.svg").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/{laser}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 24"/>',
                                         encoding="utf-8")
    row.append((f"{laser}.svg", f"excitation {laser}"))
page.add_row(row)
page.write()
