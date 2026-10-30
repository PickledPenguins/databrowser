"""A regional weather network: regions, their stations, each station's plots."""

from pathlib import Path

from databrowser import DataPage, GroupPage, Theme


def plot(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>', encoding="utf-8")


theme = Theme(banner="Upland Weather Network", banner_color="#1e5631",
              bottom_banner="Data under CC BY 4.0\nQuality-controlled hourly values")
network = GroupPage("site/index.html", "Stations by region", ["Region", "Stations"], theme=theme)
regions = {"north": [("Ben Alder", 1148, 7.2), ("Loch Ericht", 351, None)],
           "south": [("Moffat", 160, 9.8), ("Eskdalemuir", 236, 8.9)]}
for region, stations in regions.items():
    region_page = GroupPage(f"site/{region}/index.html", region.title(), ["Station", "Altitude (m)", "Mean T (C)"],
                            parent=network, theme=theme)
    for station, altitude, mean in stations:
        slug = station.lower().replace(" ", "-")
        page = DataPage(f"site/{region}/{slug}/index.html", station, columns=2,
                        column_titles=["Temperature", "Wind"], parent=region_page, theme=theme)
        for month in ("2026-09", "2026-10"):
            plot(f"site/{region}/{slug}/{month}-temp.svg")
            plot(f"site/{region}/{slug}/{month}-wind.svg")
            page.add_row([(f"{month}-temp.svg", month), (f"{month}-wind.svg", month)], label=month)
        page.write()
        region_page.add_row(page, [station, altitude, mean])
    region_page.write()
    network.add_row(region_page, [region.title(), len(stations)])
network.write()
