"""The same page in a light and a dark banner color, and in the light color under a picture."""

from pathlib import Path

from databrowser import GroupPage, Theme

for name, color in [("light", "#f6c945"), ("dark", "#14325c")]:
    theme = Theme(banner="Hydrology Lab", bottom_banner="Hydrology Lab", banner_color=color)
    GroupPage(f"site/{name}.html", f"Banner color {color}", ["Catchment"], theme=theme).write()
Path("site/river.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 1"/>', encoding="utf-8")
theme = Theme(banner="Hydrology Lab", bottom_banner="Hydrology Lab", banner_color="#f6c945",
              banner_image="site/river.svg")
GroupPage("site/light-under-image.html", "Banner color #f6c945 under a picture", ["Catchment"], theme=theme).write()
