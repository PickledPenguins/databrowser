"""Samples stored in folders named the way people name them."""

from pathlib import Path

from databrowser import DataPage, GroupPage

index = GroupPage("site/index.html", "Dilution series", ["Sample", "Dilution"])
for sample, dilution in [("sample #3", "50%"), ("sample #4 (repeat)", "25%")]:
    page = DataPage(f"site/{sample}/index.html", sample, columns=2, parent=index)
    row = []
    for view in ("plate photo", f"OD at {dilution}"):
        image = Path(f"site/{sample}/{view}.svg")
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>', encoding="utf-8")
        row.append((f"{view}.svg", view))
    page.add_row(row)
    page.write()
    index.add_row(page, [sample, dilution])
index.write()
