"""Three columns of plots, two titles."""

from databrowser import DataPage

DataPage("site/index.html", "Sweep 1", columns=3, column_titles=["Elevation", "Probe"]).write()
