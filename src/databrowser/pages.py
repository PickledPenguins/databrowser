"""Write static HTML pages for browsing data.

A GroupPage holds a table whose rows link to other pages. A DataPage holds a grid of images,
a fixed number per row, with text under each. Both take optional header and footer text, and
a Theme that gives every page of a site the same banner, title image and accent color. A
page made with a parent shows a breadcrumb trail back to the top page. A Badge marks a
status in a table cell or above a row of images.
Paths given to a page as text (links, images) are relative to the page file itself.

The pages aim at WCAG 2.2 AA: text contrast of at least 4.5:1, a visible keyboard focus,
alt text on every image, headings and landmarks a screen reader can jump between, and no
meaning carried by color alone.
"""

import html
import os
from dataclasses import dataclass
from pathlib import Path

STYLE = """
:root {
  --accent: #2b6fd6; --bg: #f3f4f7; --surface: #fff; --head: #f7f8fa; --stripe: #fafbfc; --hover: #eaf1fc;
  --border: #d5dae1; --rule: #e6e9ee; --text: #1b2130; --muted: #545d6e; --link: #1f5fbf; --bar: #111827;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #12151a; --surface: #1b1f26; --head: #21262f; --stripe: #1e232b; --hover: #252c38; --border: #39404d;
    --rule: #2a303b; --text: #e6e9ee; --muted: #a3acba; --link: #8cb8ff; --bar: #0b0e13;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh; display: flex; flex-direction: column; color: var(--text); background: var(--bg);
  font: 15px/1.55 "Inter", "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.skip { position: absolute; left: -9999px; }
.skip:focus { left: 16px; top: 8px; z-index: 10; padding: 6px 12px; background: var(--surface); color: var(--text); }
.wrap { width: 100%; max-width: 1280px; margin: 0 auto; padding: 0 32px; }
.topbar { background: var(--bar); color: #fff; border-bottom: 3px solid var(--accent); }
.topbar .wrap { height: 48px; display: flex; align-items: center; gap: 10px; font-weight: 650;
  letter-spacing: 0.02em; }
.topbar .wrap::before { content: ""; width: 10px; height: 10px; border-radius: 2px; background: var(--accent); }
.topbar a { color: inherit; text-decoration: none; }
.topbar a:hover { text-decoration: underline; text-underline-offset: 3px; }
.crumbs { background: var(--surface); border-bottom: 1px solid var(--border); font-size: 14px; }
.crumbs ol { list-style: none; margin: 0; padding-top: 10px; padding-bottom: 10px; display: flex; flex-wrap: wrap;
  gap: 4px 8px; }
.crumbs li + li::before { content: "/"; margin-right: 8px; color: var(--muted); }
.crumbs a { color: var(--link); text-underline-offset: 3px; }
.crumbs [aria-current] { font-weight: 600; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 1px 10px; border: 1px solid; border-radius: 999px;
  font-size: 12.5px; font-weight: 600; line-height: 1.6; white-space: nowrap; vertical-align: middle;
  text-transform: none; letter-spacing: 0; }
.badge::before { font-size: 11px; }
.badge-ok { color: #17663a; background: #e8f6ee; border-color: #a9dbbd; }
.badge-ok::before { content: "\\2713"; }
.badge-info { color: #1f5fbf; background: #eaf1fd; border-color: #b7cff3; }
.badge-info::before { content: "i"; font-weight: 800; font-family: Georgia, serif; }
.badge-warn { color: #8a4600; background: #fff3e0; border-color: #f0cd96; }
.badge-warn::before { content: "!"; font-weight: 800; }
.badge-error { color: #b42318; background: #fdeceb; border-color: #f2bdb8; }
.badge-error::before { content: "\\2715"; }
@media (prefers-color-scheme: dark) {
  .badge-ok { color: #7fd8a4; background: #13281c; border-color: #2a5a3d; }
  .badge-info { color: #8cb8ff; background: #15233a; border-color: #2f4a77; }
  .badge-warn { color: #ffc46b; background: #2e2110; border-color: #6a4a1c; }
  .badge-error { color: #ff9a90; background: #331614; border-color: #74302a; }
}
.hero { color: #fff; text-align: center; background-color: color-mix(in srgb, var(--accent) 50%, #0b1220);
  background-size: cover; background-position: center; }
.hero .wrap { padding-top: 44px; padding-bottom: 40px; }
.hero h1 { margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.015em;
  text-shadow: 0 1px 3px rgb(0 0 0 / 0.35); }
.hero p { margin: 10px auto 0; max-width: 70ch; font-size: 16px; color: rgb(255 255 255 / 0.9); }
main.wrap { flex: 1; padding-top: 28px; padding-bottom: 48px; }
footer { background: var(--surface); border-top: 1px solid var(--border); color: var(--muted); font-size: 13px; }
footer .wrap { padding-top: 18px; padding-bottom: 22px; text-align: center; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow-x: auto;
  box-shadow: 0 1px 2px rgb(0 0 0 / 0.04), 0 4px 16px rgb(0 0 0 / 0.04); }
table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { padding: 12px 20px; text-align: left; border-bottom: 1px solid var(--rule); }
th { background: var(--head); color: var(--muted); font-size: 12px; font-weight: 650; text-transform: uppercase;
  letter-spacing: 0.06em; border-bottom-color: var(--border); white-space: nowrap; }
.num { text-align: right; }
tbody tr:nth-child(even) { background: var(--stripe); }
tbody tr:last-child td { border-bottom: 0; }
tbody tr { position: relative; }
tbody tr:hover, tbody tr:focus-within { background: var(--hover); }
tbody tr:hover td:first-child, tbody tr:focus-within td:first-child { box-shadow: inset 4px 0 0 var(--accent); }
td:first-child a { font-weight: 600; color: var(--link); text-decoration: underline;
  text-decoration-color: transparent; text-underline-offset: 3px; }
tbody tr:hover td:first-child a { text-decoration-color: currentColor; }
td:first-child a::after { content: ""; position: absolute; inset: 0; }
td:first-child a:focus-visible { outline: none; }
tbody tr:focus-within { outline: 3px solid var(--accent); outline-offset: -3px; }
td:last-child::after { content: "\\203A"; float: right; margin-left: 12px; color: var(--muted); font-size: 18px;
  line-height: 1.2; }
.colheads { position: sticky; top: 0; z-index: 1; display: grid; gap: 2px; padding: 8px 2px;
  background: var(--bg); color: var(--muted); font-size: 12px; font-weight: 650; text-transform: uppercase;
  letter-spacing: 0.06em; text-align: center; border-bottom: 2px solid var(--border); margin-bottom: 14px; }
.set + .set { margin-top: 18px; }
.grid { margin: 0 auto; }
.set h2 { margin: 0 0 6px; font-size: 15px; font-weight: 650; display: flex; align-items: center; gap: 10px; }
.strip { display: grid; gap: 2px; padding: 2px; background: var(--border); border-radius: 8px;
  box-shadow: 0 1px 2px rgb(0 0 0 / 0.04), 0 4px 16px rgb(0 0 0 / 0.04); }
.strip figure { margin: 0; background: var(--surface); display: flex; flex-direction: column; }
.strip figure:first-child { border-radius: 6px 0 0 6px; }
.strip figure:last-child { border-radius: 0 6px 6px 0; }
.strip img { width: 100%; display: block; background: #fff; }
.strip a:focus-visible { outline-offset: -3px; }
.strip figcaption { padding: 6px 10px 8px; border-top: 1px solid var(--rule); color: var(--text);
  font: 13px/1.45 ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-variant-numeric: tabular-nums; }
.missing { aspect-ratio: 4 / 3; display: grid; place-items: center; color: var(--muted); font-size: 12px;
  letter-spacing: 0.06em; text-transform: uppercase;
  background: repeating-linear-gradient(-45deg, var(--head) 0 8px, var(--surface) 8px 16px); }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
@media print {
  body { background: #fff; color: #000; }
  .topbar, .skip, .crumbs { display: none; }
  .hero { background: none !important; color: #000; }
  .hero h1 { text-shadow: none; }
  .hero p { color: #333; }
  .card, .strip { box-shadow: none; }
  .colheads { position: static; }
  .set, tr { break-inside: avoid; }
}
"""


@dataclass(frozen=True)
class Theme:
    """Look shared by every page of a site. Make one and pass it to each page.

    banner is text in a dark bar across the top of the page, such as the lab or project name.
    It links to the top page of the site. title_image is a picture behind the page title. It
    is darkened so the title stays readable. Give its path relative to the current directory,
    not the page: each page links it by the right relative path. accent is a CSS color for the
    bars, highlights and the title band.
    """

    banner: str = ""
    title_image: str | None = None
    accent: str = "#2b6fd6"


BADGE_KINDS = ("ok", "info", "warn", "error")


@dataclass(frozen=True)
class Badge:
    """A short status shown as a colored pill with an icon, such as Badge("1 image missing", "warn").

    Use one as a value in a GroupPage row, or as the badge of a DataPage row. kind is one of
    ok, info, warn or error. The text and icon carry the meaning, the color only reinforces it.
    """

    text: str
    kind: str = "info"

    def __post_init__(self):
        if self.kind not in BADGE_KINDS:
            raise ValueError(f"badge kind {self.kind!r} is not one of {', '.join(BADGE_KINDS)}")

    def html(self) -> str:
        """The badge as an HTML span."""
        return f'<span class="badge badge-{self.kind}">{html.escape(self.text)}</span>'


def _text_html(text: str) -> str:
    """Text escaped for HTML, with each newline as a line break."""
    return "<br>".join(html.escape(line) for line in str(text).split("\n"))


def _is_number(value) -> bool:
    """Whether value is an int or float, which a table aligns to the right."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _cell_html(value) -> str:
    """A table value as HTML: a Badge as its pill, None as empty, anything else as escaped text."""
    if isinstance(value, Badge):
        return value.html()
    return "" if value is None else html.escape(str(value))


class _Page:
    """What both pages share: where the page is written, its title, header and footer text,
    theme, and the parent page it hangs under, which the breadcrumb trail is built from."""

    def __init__(self, path, title: str, header: str, footer: str, parent: "GroupPage | None", theme: Theme):
        self.path = Path(path)
        self.title = title
        self.header = header
        self.footer = footer
        self.parent = parent
        self.theme = theme

    def link_to(self, target) -> str:
        """The relative link from this page to target, a page or a path relative to the current directory."""
        target_path = target.path if isinstance(target, _Page) else target
        return Path(os.path.relpath(target_path, self.path.parent)).as_posix()

    def _breadcrumbs_html(self, trail: list["_Page"]) -> str:
        """A breadcrumb trail from the top page down to this one, or nothing for a page with no parent."""
        if len(trail) < 2:
            return ""
        items = [f'<li><a href="{html.escape(self.link_to(page))}">{html.escape(page.title)}</a></li>'
                 for page in trail[:-1]]
        items.append(f'<li><span aria-current="page">{html.escape(self.title)}</span></li>')
        return f'<nav class="crumbs" aria-label="Breadcrumb"><ol class="wrap">{"".join(items)}</ol></nav>'

    def _write(self, body: str) -> None:
        """Write the whole page: banner, breadcrumbs and title band above the body, the footer text below."""
        trail = [self]
        while trail[0].parent is not None:
            trail.insert(0, trail[0].parent)
        theme = self.theme
        banner_html = ""
        if theme.banner:
            home = html.escape(self.link_to(trail[0]))
            banner_html = f'<div class="topbar"><div class="wrap"><a href="{home}">{html.escape(theme.banner)}</a></div></div>'
        hero_style = ""
        if theme.title_image:
            shade = "linear-gradient(rgb(8 12 24 / 0.62), rgb(8 12 24 / 0.62))"
            image = html.escape(self.link_to(theme.title_image))
            hero_style = f' style="background-image: {shade}, url(&quot;{image}&quot;)"'
        header_html = f"<p>{_text_html(self.header)}</p>" if self.header else ""
        footer_html = f'<footer><div class="wrap">{_text_html(self.footer)}</div></footer>' if self.footer else ""
        page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(self.title)}</title>
<style>{STYLE}:root {{ --accent: {theme.accent}; }}</style>
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
{banner_html}
{self._breadcrumbs_html(trail)}
<header class="hero"{hero_style}><div class="wrap"><h1>{html.escape(self.title)}</h1>{header_html}</div></header>
<main class="wrap" id="content">
{body}
</main>
{footer_html}
</body>
</html>
"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(page, encoding="utf-8")


class GroupPage(_Page):
    """A page with a table. Each row links to a subgroup page or a data page.

        top = GroupPage("site/index.html", "Campaign 2026", ["Name", "Images", "Status"])
        series = GroupPage("site/series_A/index.html", "series_A", ["Sweep", "Status"], parent=top)
        top.add_row(series, ["series_A", 412, Badge("complete", "ok")])
        top.write()

    path is where write puts the page. A page with a parent shows a breadcrumb trail back up
    to the top page. A column whose values are all numbers (None aside) is aligned to the right.
    """

    def __init__(self, path, title: str, columns: list[str], header: str = "", footer: str = "",
                 parent: "GroupPage | None" = None, theme: Theme = Theme()):
        super().__init__(path, title, header, footer, parent, theme)
        self.columns = list(columns)
        self.rows: list[tuple[str, list]] = []

    def add_row(self, link, values: list) -> None:
        """Add a row linking to link: a page, or a path relative to this page. The first value
        shows as the link, and clicking anywhere on the row opens it. A value may be a Badge."""
        if len(values) != len(self.columns):
            raise ValueError(f"row has {len(values)} values, table has {len(self.columns)} columns")
        href = self.link_to(link) if isinstance(link, _Page) else link
        self.rows.append((href, list(values)))

    def write(self) -> None:
        """Write the page to its path."""
        align = []
        for index in range(len(self.columns)):
            present = [values[index] for _, values in self.rows if values[index] is not None]
            is_numeric = index > 0 and bool(present) and all(_is_number(value) for value in present)
            align.append(' class="num"' if is_numeric else "")
        head = "".join(f'<th scope="col"{align[i]}>{html.escape(column)}</th>' for i, column in enumerate(self.columns))
        rows = []
        for href, values in self.rows:
            first, *rest = [_cell_html(value) for value in values]
            cells = f'<td><a href="{html.escape(href)}">{first}</a></td>'
            cells += "".join(f"<td{align[i]}>{value}</td>" for i, value in enumerate(rest, start=1))
            rows.append(f"<tr>{cells}</tr>")
        self._write(f'<div class="card"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')



class DataPage(_Page):
    """A page with a grid of images: a fixed number of columns and any number of rows, with
    text under each image. Each row is a strip of images almost touching, rows are set apart,
    and images in a column line up. Optional column titles stay in view while scrolling.

        page = DataPage("site/series_A/sweep_03/index.html", "sweep_03", columns=3, parent=series,
                        column_titles=["Elevation", "Probe", "Spectrum"], max_image_width_px=320)
        page.add_row([("T0.8/elevation.png", "max 3.1 cm"), ("T0.8/probe.png", "rms 1.2 cm"),
                      (None, "probe offline")], label="T = 0.8 s", badge=Badge("1 missing", "warn"))
        page.write()

    Images fill the page width unless max_image_width_px caps them, which centers the grid.
    """

    def __init__(self, path, title: str, columns: int, header: str = "", footer: str = "",
                 column_titles: list[str] | None = None, max_image_width_px: int | None = None,
                 parent: GroupPage | None = None, theme: Theme = Theme()):
        if columns < 1:
            raise ValueError(f"a grid needs at least one column, got {columns}")
        if column_titles is not None and len(column_titles) != columns:
            raise ValueError(f"{len(column_titles)} column titles for {columns} columns")
        if max_image_width_px is not None and max_image_width_px < 1:
            raise ValueError(f"max_image_width_px must be positive, got {max_image_width_px}")
        super().__init__(path, title, header, footer, parent, theme)
        self.columns = columns
        self.column_titles = column_titles
        self.max_image_width_px = max_image_width_px
        self.rows: list[tuple[str, Badge | None, list[tuple[str | None, str]]]] = []

    def add_row(self, images: list[tuple[str | None, str]], label: str = "", badge: Badge | None = None) -> None:
        """Add a row of (image path, text) pairs, one per column, with an optional label and badge
        shown above it. A None path shows an empty box marked "no image" with the text under it."""
        if len(images) != self.columns:
            raise ValueError(f"row has {len(images)} images, grid has {self.columns} columns")
        self.rows.append((label, badge, list(images)))

    def write(self) -> None:
        """Write the page to its path. Image paths are relative to it. Each image's alt text is its
        column title, row label and text, for screen readers and for an image that fails to load."""
        columns_style = f'style="grid-template-columns: repeat({self.columns}, minmax(0, 1fr))"'
        column_titles = self.column_titles or [""] * self.columns
        parts = []
        if self.column_titles:
            titles = "".join(f"<div>{html.escape(title)}</div>" for title in self.column_titles)
            parts.append(f'<div class="colheads" aria-hidden="true" {columns_style}>{titles}</div>')
        for label, badge, images in self.rows:
            figures = []
            for column_title, (image, text) in zip(column_titles, images):
                alt = html.escape(", ".join(filter(None, [column_title, label, *str(text).split("\n")])))
                if image is None:
                    picture = f'<div class="missing" role="img" aria-label="No image: {alt}">no image</div>'
                else:
                    src = html.escape(image)
                    picture = f'<a href="{src}"><img src="{src}" alt="{alt}" loading="lazy"></a>'
                figures.append(f"<figure>{picture}<figcaption>{_text_html(text)}</figcaption></figure>")
            heading = ""
            if label or badge:
                heading = f"<h2>{html.escape(label)}{badge.html() if badge else ''}</h2>"
            strip = f'<div class="strip" {columns_style}>{"".join(figures)}</div>'
            parts.append(f'<section class="set">{heading}{strip}</section>')
        grid_style = ""
        if self.max_image_width_px:
            # Images plus the 2 px gaps between them and the 2 px strip padding on each side.
            width_px = self.columns * self.max_image_width_px + (self.columns - 1) * 2 + 4
            grid_style = f' style="max-width: {width_px}px"'
        self._write(f'<div class="grid"{grid_style}>\n' + "\n".join(parts) + "\n</div>")
