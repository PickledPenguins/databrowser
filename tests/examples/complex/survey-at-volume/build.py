"""A soil moisture survey: 120 stations in one table, three detailed station pages."""

from pathlib import Path

from databrowser import Badge, DataPage, GroupPage, Theme

theme = Theme(banner="Soil Moisture Network", bottom_banner="Network operations")
index = GroupPage("site/index.html", "Station overview", ["Station", "Depth (cm)", "Mean VWC", "Gaps", "Status"],
                  theme=theme)
detailed = {7: "north", 42: "central", 99: "south"}
for number in range(1, 121):
    name = f"SM{number:03d}"
    mean = None if number % 17 == 0 else round(0.12 + (number % 23) / 100, 3)
    gaps = number % 5
    status = Badge("offline", "error") if mean is None else Badge(f"{gaps} gaps", "warn") if gaps else Badge("ok", "ok")
    if number in detailed:
        page = DataPage(f"site/{name}/index.html", f"{name}, {detailed[number]}", columns=4,
                        column_titles=["5 cm", "10 cm", "20 cm", "50 cm"], max_image_width_px=220, parent=index,
                        theme=theme)
        for week in range(1, 41):
            row = []
            for depth in (5, 10, 20, 50):
                if (week * depth + number) % 13 == 0:
                    row.append((None, f"week {week}, {depth} cm"))
                    continue
                image = f"w{week:02d}/d{depth}.svg"
                Path(f"site/{name}/{image}").parent.mkdir(parents=True, exist_ok=True)
                Path(f"site/{name}/{image}").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>',
                                                        encoding="utf-8")
                row.append((image, f"week {week}\n{depth} cm"))
            missing = sum(image is None for image, _ in row)
            page.add_row(row, label=f"Week {week}", badge=Badge(f"{missing} missing", "warn") if missing else None)
        page.write()
        link = page
    else:
        Path(f"site/{name}.csv").parent.mkdir(parents=True, exist_ok=True)
        Path(f"site/{name}.csv").write_text("t,vwc\n", encoding="utf-8")
        link = f"{name}.csv"
    index.add_row(link, [name, 5 * (1 + number % 4), mean, gaps, status])
index.write()
