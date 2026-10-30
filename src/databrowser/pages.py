"""Objects that build static HTML pages: tables whose rows open other pages, grids of
images with text under each, and an optional header and footer on every page.

Every path handed to these objects (a page, a link target, an image) is relative to the
site root. A page turns each into a link relative to itself when it is rendered, so the
site works opened from disk and can be moved or copied as a whole.
"""

from __future__ import annotations

import html
import numbers
import os
import posixpath
import tempfile
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit

STATIC_DIR = "_static"  # site-relative directory the stylesheet and script are copied to
STATIC_FILES = ("style.css", "browser.js")
STATUS_LEVELS = ("ok", "warn", "bad")
FLOAT_FORMAT = ".6g"  # numbers in tables and key/value grids. Pass a str to choose another
SLIDER_MAX_PX = 600


def _escape(value) -> str:
    return html.escape(str(value))


def _lines_html(text: str | list[str]) -> str:
    """Text as HTML lines: a list gives one line per item, a string breaks at newlines."""
    lines = text if isinstance(text, (list, tuple)) else str(text).split("\n")
    return "<br>".join(_escape(line) for line in lines)


def _href(target: str, page_dir: str) -> str:
    """The href from a page in page_dir to target, escaped for an attribute.

    A site-relative target becomes relative to the page and is percent-encoded, keeping any
    #fragment: "a/b c.html#x" from "a" gives "b%20c.html#x". A URL with a scheme
    ("https://...", "mailto:...") or a bare "#fragment" is kept as is.
    """
    if target.startswith("#") or urlsplit(target).scheme:
        return _escape(target)
    path, hash_mark, fragment = target.partition("#")
    relative = posixpath.relpath(path, page_dir or ".")
    return _escape(quote(relative) + hash_mark + fragment)


# ----------------------------------------------------------------------
# Values: what goes in a table cell, a key/value grid or an image grid
# ----------------------------------------------------------------------

@dataclass
class Link:
    """Text that links to a target: a site-relative path, or a URL kept as is."""

    text: str
    target: str


@dataclass
class Image:
    """An image file at a site-relative path. In a grid, the caption shows under it."""

    src: str
    caption: str | list[str] = ""  # a list gives one line per item
    alt: str = ""


@dataclass
class Missing:
    """A grid cell standing in for an image that does not exist."""

    caption: str | list[str] = ""
    label: str = "no image"  # shown in the empty box


@dataclass
class Status:
    """A colored dot followed by text, for a table cell."""

    text: str
    level: str = "ok"  # ok, warn or bad

    def __post_init__(self):
        if self.level not in STATUS_LEVELS:
            raise ValueError(f"status level {self.level!r} is not one of {', '.join(STATUS_LEVELS)}")


CELL_TYPES = (str, numbers.Real, Link, Status, Image)


def _check_cell(value) -> None:
    """Raise TypeError unless value can be shown in a table cell or a key/value grid."""
    items = value if isinstance(value, (list, tuple)) else [value]
    for item in items:
        if item is not None and not isinstance(item, CELL_TYPES):
            raise TypeError(f"cannot show a {type(item).__name__} in a cell: {item!r}")


def _cell_html(value, page_dir: str) -> str:
    """The HTML for one cell value. A list or tuple shows its items side by side."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return '<div class="cellgroup">' + "".join(_cell_html(v, page_dir) for v in value) + "</div>"
    if isinstance(value, bool):
        return _escape(value)
    if isinstance(value, numbers.Integral):
        return _escape(int(value))
    if isinstance(value, numbers.Real):
        return _escape(format(float(value), FLOAT_FORMAT))
    if isinstance(value, Link):
        return f'<a href="{_href(value.target, page_dir)}">{_escape(value.text)}</a>'
    if isinstance(value, Status):
        return f'<span class="dot {value.level}"></span>{_escape(value.text)}'
    if isinstance(value, Image):
        return f'<img class="thumb" src="{_href(value.src, page_dir)}" alt="{_escape(value.alt)}" loading="lazy">'
    return _escape(value)


def _td_html(value, page_dir: str) -> str:
    """A table cell. A number is right-aligned and sorts by its full value, not its text."""
    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        return f'<td class="num" data-sort="{float(value)!r}">{_cell_html(value, page_dir)}</td>'
    return f"<td>{_cell_html(value, page_dir)}</td>"


def _meta_html(items: dict, page_dir: str) -> str:
    """A key/value grid, or nothing for an empty dict."""
    if not items:
        return ""
    pairs = "".join(f"<div><dt>{_escape(key)}</dt><dd>{_cell_html(value, page_dir)}</dd></div>"
                    for key, value in items.items())
    return f'<dl class="meta">{pairs}</dl>'


# ----------------------------------------------------------------------
# Blocks: what a page holds, top to bottom
# ----------------------------------------------------------------------

@dataclass
class Text:
    """A paragraph. A list gives one line per item, a string breaks at newlines."""

    text: str | list[str]

    def html(self, page_dir: str) -> str:
        return f'<p class="text">{_lines_html(self.text)}</p>'


@dataclass
class Meta:
    """Key/value pairs laid out as a compact grid. Values take anything a table cell does."""

    items: dict

    def __post_init__(self):
        for value in self.items.values():
            _check_cell(value)

    def html(self, page_dir: str) -> str:
        return _meta_html(self.items, page_dir)


class Table:
    """Rows of cells under column headings. A row given a target opens it when clicked.

    A cell holds a str, a number, None (empty), a Link, a Status, an Image (shown as a
    thumbnail), or a list of those shown side by side. Clicking a heading sorts the rows.
    """

    def __init__(self, columns: list[str]):
        if not columns:
            raise ValueError("a table needs at least one column")
        self.columns = list(columns)
        self.rows: list[tuple[list, str | None]] = []

    def add_row(self, cells: list, target: str | None = None) -> None:
        """Append a row. Target is the site-relative page the whole row opens."""
        if len(cells) != len(self.columns):
            raise ValueError(f"row has {len(cells)} cells, table has {len(self.columns)} columns")
        for value in cells:
            _check_cell(value)
        self.rows.append((list(cells), target))

    def html(self, page_dir: str) -> str:
        head = "".join(f"<th>{_escape(column)}</th>" for column in self.columns)
        rows = []
        for cells, target in self.rows:
            attribute = "" if target is None else f' data-href="{_href(target, page_dir)}"'
            rows.append(f"<tr{attribute}>" + "".join(_td_html(v, page_dir) for v in cells) + "</tr>")
        return (f'<div class="tablewrap"><table class="groups"><thead><tr>{head}</tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div>')


def _row_label_html(label: str | list[str]) -> str:
    """A grid row label: the first line bold, any others below it in small type."""
    lines = label if isinstance(label, (list, tuple)) else str(label).split("\n")
    if not lines or lines == [""]:
        return ""
    first, *rest = lines
    return f"<b>{_escape(first)}</b>" + "".join(f"<span>{_escape(line)}</span>" for line in rest)


def _figure_html(cell: Image | Missing, page_dir: str) -> str:
    """One image grid cell: the image, or an empty box for a Missing one, and its caption."""
    caption = f"<figcaption>{_lines_html(cell.caption)}</figcaption>" if cell.caption else ""
    if isinstance(cell, Missing):
        return f'<figure class="cell missing"><div class="placeholder">{_escape(cell.label)}</div>{caption}</figure>'
    return (f'<figure class="cell"><img src="{_href(cell.src, page_dir)}" alt="{_escape(cell.alt)}" '
            f'loading="lazy">{caption}</figure>')


class ImageGrid:
    """Rows of images aligned in columns, with minimal gap, text under each image and an
    optional label at the left of each row.

    Columns are given headings, or are as many as the longest row. A shorter row leaves its
    last columns empty. The page shows a slider for the image width and a switch to hide the
    captions, and clicking an image enlarges it.
    """

    def __init__(self, columns: list[str] | None = None, image_width_px: int = 220):
        if image_width_px <= 0:
            raise ValueError(f"image width must be positive, got {image_width_px}")
        self.columns = list(columns or [])
        self.image_width_px = image_width_px
        self.rows: list[tuple[str | list[str], list[Image | Missing]]] = []

    def add_row(self, cells: list[Image | Missing], label: str | list[str] = "") -> None:
        """Append a row of images. The label shows at its left, first line bold."""
        if self.columns and len(cells) > len(self.columns):
            raise ValueError(f"row has {len(cells)} images, grid has {len(self.columns)} columns")
        for cell in cells:
            if not isinstance(cell, (Image, Missing)):
                raise TypeError(f"an image grid holds Image or Missing, not {type(cell).__name__}")
        self.rows.append((label, list(cells)))

    def html(self, page_dir: str) -> str:
        n_columns = len(self.columns) or max((len(cells) for _, cells in self.rows), default=0)
        parts = []
        if self.columns:
            parts.append("<div></div>")
            parts.extend(f'<div class="colhead">{_escape(column)}</div>' for column in self.columns)
        for label, cells in self.rows:
            parts.append(f'<div class="rowhead">{_row_label_html(label)}</div>')
            parts.extend(_figure_html(cell, page_dir) for cell in cells)
            parts.extend("<div></div>" for _ in range(n_columns - len(cells)))
        slider_max = max(SLIDER_MAX_PX, self.image_width_px)
        controls = (f'<div class="gridctl"><label>Image width <input class="imgwidth" type="range" '
                    f'min="60" max="{slider_max}" value="{self.image_width_px}"></label>'
                    '<label><input class="captions" type="checkbox" checked> Captions</label></div>')
        style = f"--columns:{n_columns};--imgw:{self.image_width_px}px"
        return f'<section class="gridblock">{controls}<div class="imggrid" style="{style}">{"".join(parts)}</div></section>'


BLOCK_TYPES = (Text, Meta, Table, ImageGrid)


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------

@dataclass
class Section:
    """A page header or footer: an optional title, text and key/value grid."""

    title: str = ""
    text: str | list[str] = ""
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        for value in self.meta.values():
            _check_cell(value)

    def html(self, tag: str, page_dir: str) -> str:
        """The section as a <header> or <footer> element, named by tag."""
        title = f'<div class="title">{_escape(self.title)}</div>' if self.title else ""
        text = f"<p>{_lines_html(self.text)}</p>" if self.text else ""
        return f'<{tag} class="page{tag}">{title}{text}{_meta_html(self.meta, page_dir)}</{tag}>'


def _check_page_path(path: str) -> None:
    """Raise ValueError unless path is a relative .html path that stays inside the site."""
    parts = PurePosixPath(path)
    if parts.is_absolute() or ".." in parts.parts or parts.suffix != ".html":
        raise ValueError(f"page path must be a relative .html path inside the site: {path!r}")


def _write_atomic(path: Path, text: str) -> None:
    """Write text to path through a temporary file, so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(text)
        # mkstemp makes the file readable by its owner only, and a web server needs to read it.
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except BaseException:
        os.unlink(temporary)
        raise


def _install_static(root: Path) -> None:
    """Copy the stylesheet and script into the site, unless the copies there are current."""
    for name in STATIC_FILES:
        text = resources.files("databrowser").joinpath("static", name).read_text(encoding="utf-8")
        destination = root / STATIC_DIR / name
        if not destination.exists() or destination.read_text(encoding="utf-8") != text:
            _write_atomic(destination, text)


class Page:
    """One HTML page at a site-relative path.

    Top to bottom: a bar with the breadcrumb trail (crumbs, then the title) and the nav
    links, the header, the blocks in the order added, and the footer. A page with a table
    also gets a box that filters its rows.
    """

    def __init__(self, path: str, title: str, crumbs: list[Link] = (), nav: list[Link] = (),
                 header: Section | None = None, footer: Section | None = None):
        _check_page_path(path)
        self.path = path
        self.title = title
        self.crumbs = list(crumbs)  # links to the pages above this one, top first
        self.nav = list(nav)  # links at the right of the bar, such as previous and next
        self.header = header
        self.footer = footer
        self.blocks: list[Text | Meta | Table | ImageGrid] = []

    def add(self, block):
        """Append a block (Text, Meta, Table or ImageGrid) and return it."""
        if not isinstance(block, BLOCK_TYPES):
            raise TypeError(f"a page holds Text, Meta, Table or ImageGrid, not {type(block).__name__}")
        self.blocks.append(block)
        return block

    def render(self) -> str:
        """The whole page as HTML text."""
        page_dir = posixpath.dirname(self.path)
        crumbs = "".join(f'<a href="{_href(link.target, page_dir)}">{_escape(link.text)}</a><span class="sep">/</span>'
                         for link in self.crumbs)
        nav = "".join(f'<a href="{_href(link.target, page_dir)}">{_escape(link.text)}</a>' for link in self.nav)
        has_table = any(isinstance(block, Table) for block in self.blocks)
        filter_box = '<input class="filter" type="search" placeholder="Filter rows">' if has_table else ""
        header = self.header.html("header", page_dir) if self.header else ""
        footer = self.footer.html("footer", page_dir) if self.footer else ""
        blocks = "\n".join(block.html(page_dir) for block in self.blocks)
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escape(self.title)}</title>
<link rel="stylesheet" href="{_href(f"{STATIC_DIR}/style.css", page_dir)}">
<script src="{_href(f"{STATIC_DIR}/browser.js", page_dir)}" defer></script>
</head>
<body>
<div class="topbar">
<nav class="crumbs">{crumbs}<span class="here">{_escape(self.title)}</span></nav>
<nav class="links">{nav}</nav>
{filter_box}
</div>
<main>
{header}
{blocks}
</main>
{footer}
<div class="lightbox"><img alt=""><div></div></div>
</body>
</html>
"""

    def write(self, root: str | Path) -> Path:
        """Write the page under the site root and return the file's path.

        Also copies the shared stylesheet and script to the site's _static directory when
        they are missing or out of date. Each file is replaced whole, never left half written.
        """
        root = Path(root)
        _install_static(root)
        destination = root / self.path
        _write_atomic(destination, self.render())
        return destination
