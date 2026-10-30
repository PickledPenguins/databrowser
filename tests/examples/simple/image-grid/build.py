"""Three diagnostic plots of one model fit, side by side."""

from pathlib import Path

from databrowser import DataPage


def plot(path):
    """A small SVG standing in for a plot."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
                          '<rect width="160" height="120" fill="#eef"/></svg>', encoding="utf-8")


page = DataPage("site/index.html", "Fit diagnostics, model 7", columns=3)
images = []
for name, text in [("residuals", "residuals vs fitted"), ("qq", "normal Q-Q"), ("leverage", "Cook's distance")]:
    plot(f"site/{name}.svg")
    images.append((f"{name}.svg", text))
page.add_row(images)
page.write()
