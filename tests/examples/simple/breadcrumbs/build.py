"""A year, a month and a day of an archive, each under the one before."""

from databrowser import GroupPage

archive = GroupPage("site/index.html", "Seismometer archive", ["Year"])
year = GroupPage("site/2026/index.html", "2026", ["Month"], parent=archive)
month = GroupPage("site/2026/oct/index.html", "October", ["Day"], parent=year)
archive.add_row(year, ["2026"])
year.add_row(month, ["October"])
for page in (archive, year, month):
    page.write()
