"""The same page in a light and a dark banner color."""

from databrowser import GroupPage, Theme

for name, color in [("light", "#f6c945"), ("dark", "#14325c")]:
    theme = Theme(banner="Hydrology Lab", bottom_banner="Hydrology Lab", banner_color=color)
    GroupPage(f"site/{name}.html", f"Banner color {color}", ["Catchment"], theme=theme).write()
