"""Write static HTML pages for browsing data.

A GroupPage holds a table whose rows link to other pages. A DataPage holds a grid of images,
a fixed number per row, with text under each. Both take optional header and footer text, and
a Theme that gives every page of a site the same banner, title image and accent color.
Paths given to a page (links, images) are relative to the page file itself.
"""

import html
import os
from dataclasses import dataclass
from pathlib import Path

STYLE = """
:root {
  --accent: #2b6fd6; --bg: #f3f4f7; --surface: #fff; --head: #f7f8fa; --hover: #eef3fb; --border: #dde1e7;
  --rule: #eceef2; --text: #1b2130; --muted: #5d6677; --link: #1f5fbf; --bar: #111827;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #12151a; --surface: #1b1f26; --head: #21262f; --hover: #252c38; --border: #323845; --rule: #292e38;
    --text: #e4e7ec; --muted: #9aa3b2; --link: #7fb0ff; --bar: #0b0e13;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh; display: flex; flex-direction: column; color: var(--text); background: var(--bg);
  font: 14px/1.5 "Inter", "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.wrap { width: 100%; max-width: 1280px; margin: 0 auto; padding: 0 32px; }
.topbar { background: var(--bar); color: #fff; border-bottom: 3px solid var(--accent); }
.topbar .wrap { height: 48px; display: flex; align-items: center; gap: 10px; font-weight: 650;
  letter-spacing: 0.02em; }
.topbar .wrap::before { content: ""; width: 10px; height: 10px; border-radius: 2px; background: var(--accent); }
.hero { color: #fff; background-color: color-mix(in srgb, var(--accent) 55%, #0b1220);
  background-size: cover; background-position: center; }
.hero .wrap { padding-top: 44px; padding-bottom: 40px; }
.hero h1 { margin: 0; font-size: 30px; font-weight: 700; letter-spacing: -0.015em;
  text-shadow: 0 1px 2px rgb(0 0 0 / 0.25); }
.hero p { margin: 10px 0 0; max-width: 80ch; font-size: 15px; color: rgb(255 255 255 / 0.85); }
main.wrap { flex: 1; padding-top: 28px; padding-bottom: 40px; }
footer { background: var(--surface); border-top: 1px solid var(--border); color: var(--muted); font-size: 12.5px; }
footer .wrap { padding-top: 18px; padding-bottom: 22px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden;
  box-shadow: 0 1px 2px rgb(0 0 0 / 0.04), 0 4px 16px rgb(0 0 0 / 0.04); }
table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { padding: 13px 20px; text-align: left; border-bottom: 1px solid var(--rule); }
th { background: var(--head); color: var(--muted); font-size: 11.5px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.06em; border-bottom-color: var(--border); }
tbody tr:last-child td { border-bottom: 0; }
tbody tr { position: relative; transition: background 0.12s; }
tbody tr:hover { background: var(--hover); }
tbody tr:hover td:first-child { box-shadow: inset 3px 0 0 var(--accent); }
td:first-child a { font-weight: 600; color: var(--link); text-decoration: none; }
td:first-child a::after { content: ""; position: absolute; inset: 0; }
td:last-child::after { content: "\\203A"; float: right; color: var(--muted); font-size: 18px; line-height: 1; }
.grid { display: grid; gap: 10px; align-items: start; }
.grid figure { margin: 0; transition: border-color 0.12s, transform 0.12s; }
.grid figure:hover { border-color: var(--accent); transform: translateY(-1px); }
.grid img { width: 100%; display: block; background: #fff; }
.grid figcaption { padding: 8px 12px 10px; border-top: 1px solid var(--rule); color: var(--muted);
  font: 12px/1.5 ui-monospace, "SF Mono", Menlo, Consolas, monospace; }
.missing { aspect-ratio: 4 / 3; display: grid; place-items: center; color: var(--muted); font-size: 12px;
  letter-spacing: 0.06em; text-transform: uppercase;
  background: repeating-linear-gradient(-45deg, var(--head) 0 8px, var(--surface) 8px 16px); }
"""


@dataclass(frozen=True)
class Theme:
    """Look shared by every page of a site. Make one and pass it to each page.

    banner is text in a dark bar across the top of the page, such as the lab or project name.
    title_image is a picture behind the page title. It is darkened so the title stays readable.
    Give its path relative to the current directory, not the page: each page links it by the
    right relative path. accent is a CSS color for the bars, highlights and the title band.
    """

    banner: str = ""
    title_image: str | None = None
    accent: str = "#2b6fd6"


def _text_html(text: str) -> str:
    """Text escaped for HTML, with each newline as a line break."""
    return "<br>".join(html.escape(line) for line in str(text).split("\n"))


def _write_page(path, title: str, header: str, footer: str, theme: Theme, body: str) -> None:
    """Write a whole page: banner and title band above the body, the footer text below."""
    path = Path(path)
    banner_html = f'<div class="topbar"><div class="wrap">{html.escape(theme.banner)}</div></div>' if theme.banner else ""
    hero_style = ""
    if theme.title_image:
        image = Path(os.path.relpath(theme.title_image, path.parent)).as_posix()
        shade = "linear-gradient(90deg, rgb(8 12 24 / 0.82), rgb(8 12 24 / 0.35))"
        hero_style = f' style="background-image: {shade}, url(&quot;{html.escape(image)}&quot;)"'
    header_html = f"<p>{_text_html(header)}</p>" if header else ""
    footer_html = f'<footer><div class="wrap">{_text_html(footer)}</div></footer>' if footer else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{STYLE}:root {{ --accent: {theme.accent}; }}</style>
</head>
<body>
{banner_html}
<header class="hero"{hero_style}><div class="wrap"><h1>{html.escape(title)}</h1>{header_html}</div></header>
<main class="wrap">
{body}
</main>
{footer_html}
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")


class GroupPage:
    """A page with a table. Each row links to a subgroup page or a data page.

        page = GroupPage("Campaign 2026", ["Name", "Images", "Status"], header="All test series")
        page.add_row("series_A/index.html", ["series_A", 412, "complete"])
        page.write("site/index.html")
    """

    def __init__(self, title: str, columns: list[str], header: str = "", footer: str = "", theme: Theme = Theme()):
        self.title = title
        self.columns = list(columns)
        self.header = header
        self.footer = footer
        self.theme = theme
        self.rows: list[tuple[str, list]] = []

    def add_row(self, link: str, values: list) -> None:
        """Add a row. The first value shows as a link to the page at link, and clicking anywhere on the row opens it."""
        if len(values) != len(self.columns):
            raise ValueError(f"row has {len(values)} values, table has {len(self.columns)} columns")
        self.rows.append((link, list(values)))

    def write(self, path) -> None:
        """Write the page to path. Links in the rows are relative to it."""
        head = "".join(f"<th>{html.escape(column)}</th>" for column in self.columns)
        rows = []
        for link, values in self.rows:
            first, *rest = ["" if value is None else html.escape(str(value)) for value in values]
            cells = f'<td><a href="{html.escape(link)}">{first}</a></td>' + "".join(f"<td>{v}</td>" for v in rest)
            rows.append(f"<tr>{cells}</tr>")
        body = f'<div class="card"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
        _write_page(path, self.title, self.header, self.footer, self.theme, body)


class DataPage:
    """A page with a grid of images: a fixed number of columns and any number of rows, with
    text under each image. Images in a column line up, and the grid fills the page width.

        page = DataPage("sweep_03", columns=3, header="Regular waves, H = 6 cm")
        page.add_row([("T0.8/elevation.png", "max 3.1 cm"), ("T0.8/probe.png", "rms 1.2 cm"),
                      (None, "probe offline")])
        page.write("site/series_A/sweep_03/index.html")
    """

    def __init__(self, title: str, columns: int, header: str = "", footer: str = "", theme: Theme = Theme()):
        if columns < 1:
            raise ValueError(f"a grid needs at least one column, got {columns}")
        self.title = title
        self.columns = columns
        self.header = header
        self.footer = footer
        self.theme = theme
        self.rows: list[list[tuple[str | None, str]]] = []

    def add_row(self, images: list[tuple[str | None, str]]) -> None:
        """Add a row of (image path, text) pairs, one per column. A None path shows an empty
        box marked "no image" with the text under it."""
        if len(images) != self.columns:
            raise ValueError(f"row has {len(images)} images, grid has {self.columns} columns")
        self.rows.append(list(images))

    def write(self, path) -> None:
        """Write the page to path. Image paths are relative to it."""
        cells = []
        for row in self.rows:
            for image, text in row:
                if image is None:
                    picture = '<div class="missing">no image</div>'
                else:
                    picture = f'<a href="{html.escape(image)}"><img src="{html.escape(image)}" loading="lazy"></a>'
                cells.append(f'<figure class="card">{picture}<figcaption>{_text_html(text)}</figcaption></figure>')
        style = f"grid-template-columns: repeat({self.columns}, minmax(0, 1fr))"
        body = f'<div class="grid" style="{style}">{"".join(cells)}</div>'
        _write_page(path, self.title, self.header, self.footer, self.theme, body)
