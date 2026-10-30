"""A fourth plot added to the row but not to the page's columns."""

from databrowser import DataPage

page = DataPage("site/index.html", "Sweep 1", columns=3)
page.add_row([("a.png", "a"), ("b.png", "b"), ("c.png", "c"), ("d.png", "d")])
page.write()
