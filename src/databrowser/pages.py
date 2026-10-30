"""Write static HTML pages for browsing data.

A GroupPage holds a table whose rows link to other pages. A DataPage holds a grid of images,
a fixed number per row, with text under each. Both take optional header and footer text.
Paths given to a page (links, images) are relative to the page file itself.
"""

import html
from pathlib import Path

STYLE = """
body { margin: 0; font: 14px/1.45 system-ui, sans-serif; color: #1c1c1a; background: #fafaf9; }
header, footer { padding: 12px 16px; color: #6b6b66; }
header h1 { margin: 0 0 4px; font-size: 22px; color: #1c1c1a; }
footer { border-top: 1px solid #e2e1dc; font-size: 12px; margin-top: 24px; }
main { padding: 0 16px; }
table { border-collapse: collapse; background: #fff; border: 1px solid #e2e1dc; }
th, td { padding: 6px 12px; text-align: left; border-bottom: 1px solid #e2e1dc; }
th { font-size: 12px; color: #6b6b66; text-transform: uppercase; }
tbody tr { position: relative; }
tbody tr:hover { background: #f1f0ea; }
td:first-child a { font-weight: 600; color: #2f5fa7; text-decoration: none; }
td:first-child a::after { content: ""; position: absolute; inset: 0; }
.grid { display: grid; gap: 2px; align-items: start; }
.grid figure { margin: 0; }
.grid img { width: 100%; display: block; background: #fff; }
.grid figcaption { font: 11px/1.3 monospace; color: #6b6b66; padding: 2px 2px 6px; }
.missing { aspect-ratio: 4 / 3; display: grid; place-items: center; border: 1px dashed #ccc; color: #999; }
"""


def _text_html(text: str) -> str:
    """Text escaped for HTML, with each newline as a line break."""
    return "<br>".join(html.escape(line) for line in str(text).split("\n"))


def _write_page(path, title: str, header: str, footer: str, body: str) -> None:
    """Write a whole page: the title and header text above the body, the footer text below."""
    header_html = f"<p>{_text_html(header)}</p>" if header else ""
    footer_html = f"<footer>{_text_html(footer)}</footer>" if footer else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<header><h1>{html.escape(title)}</h1>{header_html}</header>
<main>
{body}
</main>
{footer_html}
</body>
</html>
"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")


class GroupPage:
    """A page with a table. Each row links to a subgroup page or a data page.

        page = GroupPage("Campaign 2026", ["Name", "Images", "Status"], header="All test series")
        page.add_row("series_A/index.html", ["series_A", 412, "complete"])
        page.write("site/index.html")
    """

    def __init__(self, title: str, columns: list[str], header: str = "", footer: str = ""):
        self.title = title
        self.columns = list(columns)
        self.header = header
        self.footer = footer
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
        body = f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
        _write_page(path, self.title, self.header, self.footer, body)


class DataPage:
    """A page with a grid of images: a fixed number of columns and any number of rows, with
    text under each image. Images in a column line up.

        page = DataPage("sweep_03", columns=3, header="Regular waves, H = 6 cm")
        page.add_row([("T0.8/elevation.png", "max 3.1 cm"), ("T0.8/probe.png", "rms 1.2 cm"),
                      (None, "probe offline")])
        page.write("site/series_A/sweep_03/index.html")
    """

    def __init__(self, title: str, columns: int, header: str = "", footer: str = "", image_width_px: int = 240):
        if columns < 1:
            raise ValueError(f"a grid needs at least one column, got {columns}")
        self.title = title
        self.columns = columns
        self.header = header
        self.footer = footer
        self.image_width_px = image_width_px
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
                cells.append(f"<figure>{picture}<figcaption>{_text_html(text)}</figcaption></figure>")
        style = f"grid-template-columns: repeat({self.columns}, {self.image_width_px}px)"
        body = f'<div class="grid" style="{style}">{"".join(cells)}</div>'
        _write_page(path, self.title, self.header, self.footer, body)
