"""A width cap read from a config value that was never set."""

from databrowser import DataPage

DataPage("site/index.html", "Sweep 1", columns=2, max_image_width_px=0).write()
