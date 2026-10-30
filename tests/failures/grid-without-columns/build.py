"""A data page whose column count came from an empty list of plots."""

from databrowser import DataPage

plots = []
DataPage("site/index.html", "Sweep 1", columns=len(plots)).write()
