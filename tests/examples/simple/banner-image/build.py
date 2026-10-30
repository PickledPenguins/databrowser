"""Banners with a texture behind them."""

from pathlib import Path

from databrowser import GroupPage, Theme

Path("site").mkdir(exist_ok=True)
Path("site/texture.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 1"/>', encoding="utf-8")
theme = Theme(banner="Geology Field School", bottom_banner="Field School 2026", banner_image="site/texture.svg")
GroupPage("site/index.html", "Outcrop photos", ["Outcrop", "Photos"], theme=theme).write()
