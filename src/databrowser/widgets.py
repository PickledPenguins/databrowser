"""Widgets: the pieces a page is built from, each rendering itself as HTML. Layouts (layouts.py) place them, as in Qt.

Every path handed to a widget (a link target, an image) is relative to the site root. A
widget renders it relative to the page it is on, which it is told as page_dir, so the site
works opened from disk and can be moved or copied as a whole.
"""

from __future__ import annotations

import html
import numbers
import posixpath
from urllib.parse import quote, urlsplit

LABEL_STYLES = ("text", "title", "heading", "muted", "mono")
STATUS_LEVELS = ("ok", "warn", "bad")
FLOAT_FORMAT = ".6g"  # plain numbers in tables and key/value grids. Pass a Label to choose another


def escape(value) -> str:
    return html.escape(str(value))


def href(target: str, page_dir: str) -> str:
    """The href from a page in page_dir to target, escaped for an attribute.

    A site-relative target becomes relative to the page and is percent-encoded, keeping any
    #fragment: "a/b c.html#x" from "a" gives "b%20c.html#x". A URL with a scheme
    ("https://...", "mailto:...") or a bare "#fragment" is kept as is.
    """
    if target.startswith("#") or urlsplit(target).scheme:
        return escape(target)
    path, hash_mark, fragment = target.partition("#")
    relative = posixpath.relpath(path, page_dir or ".")
    return escape(quote(relative) + hash_mark + fragment)


def lines_html(text: str | list[str]) -> str:
    """Text as HTML lines: a list gives one line per item, a string breaks at newlines."""
    lines = text if isinstance(text, (list, tuple)) else str(text).split("\n")
    return "<br>".join(escape(line) for line in lines)


class Widget:
    """Something a layout can hold, a layout included. A subclass renders itself with html()."""

    def html(self, page_dir: str) -> str:
        """The widget as HTML, for a page in the site-relative directory page_dir."""
        raise NotImplementedError(f"{type(self).__name__} does not define html()")


class Label(Widget):
    """Text, in one of the styles: text, title, heading, muted or mono. A list gives one
    line per item, a string breaks at newlines."""

    def __init__(self, text: str | list[str], style: str = "text"):
        if style not in LABEL_STYLES:
            raise ValueError(f"label style {style!r} is not one of {', '.join(LABEL_STYLES)}")
        self.text = text
        self.style = style

    def html(self, page_dir: str) -> str:
        return f'<div class="label {self.style}">{lines_html(self.text)}</div>'


class Link(Widget):
    """Text that links to a target: a site-relative path, or a URL kept as is."""

    def __init__(self, text: str, target: str):
        self.text = text
        self.target = target

    def html(self, page_dir: str) -> str:
        return f'<a href="{href(self.target, page_dir)}">{escape(self.text)}</a>'


class Status(Widget):
    """A colored dot followed by text. The level, ok, warn or bad, sets the color."""

    def __init__(self, text: str, level: str = "ok"):
        if level not in STATUS_LEVELS:
            raise ValueError(f"status level {level!r} is not one of {', '.join(STATUS_LEVELS)}")
        self.text = text
        self.level = level

    def html(self, page_dir: str) -> str:
        return f'<span class="status"><span class="dot {self.level}"></span>{escape(self.text)}</span>'


class Image(Widget):
    """An image file at a site-relative path, with an optional caption under it.

    Without a size it takes the page's image width, which ImageControls lets the reader
    change. Clicking it shows it enlarged.
    """

    def __init__(self, src: str, caption: str | list[str] = "", alt: str = "",
                 width_px: int | None = None, height_px: int | None = None):
        self.src = src
        self.caption = caption
        self.alt = alt
        self.width_px = width_px
        self.height_px = height_px

    def html(self, page_dir: str) -> str:
        figure_style, img_style = _size_styles(self.width_px, self.height_px)
        caption = f"<figcaption>{lines_html(self.caption)}</figcaption>" if self.caption else ""
        return (f'<figure class="image"{figure_style}><img src="{href(self.src, page_dir)}"{img_style} '
                f'alt="{escape(self.alt)}" loading="lazy">{caption}</figure>')


class Placeholder(Widget):
    """An empty box where an image would be, with an optional caption under it."""

    def __init__(self, caption: str | list[str] = "", text: str = "no image"):
        self.caption = caption
        self.text = text

    def html(self, page_dir: str) -> str:
        caption = f"<figcaption>{lines_html(self.caption)}</figcaption>" if self.caption else ""
        return f'<figure class="image missing"><div class="placeholder">{escape(self.text)}</div>{caption}</figure>'


def _size_styles(width_px: int | None, height_px: int | None) -> tuple[str, str]:
    """Style attributes for an image's figure and img: a fixed width, a fixed height with the
    width following, or nothing for the page's image width."""
    if width_px is not None and height_px is not None:
        return f' style="width:{int(width_px)}px"', f' style="height:{int(height_px)}px;object-fit:contain"'
    if width_px is not None:
        return f' style="width:{int(width_px)}px"', ""
    if height_px is not None:
        return ' style="width:auto"', f' style="height:{int(height_px)}px;width:auto"'
    return "", ""


class ImageControls(Widget):
    """A slider for the width of every image on the page without a fixed size, and a switch that hides the captions."""

    def __init__(self, width_px: int = 220, max_width_px: int = 600):
        if not 0 < width_px <= max_width_px:
            raise ValueError(f"image width {width_px} is not between 1 and {max_width_px}")
        self.width_px = width_px
        self.max_width_px = max_width_px

    def html(self, page_dir: str) -> str:
        return (f'<div class="imagecontrols"><label>Image width <input class="imagewidth" type="range" '
                f'min="40" max="{self.max_width_px}" value="{self.width_px}"></label>'
                '<label><input class="captions" type="checkbox" checked> Captions</label></div>')


def as_widget(value) -> Widget:
    """A widget for value: a widget or layout as is, None as an empty label, a str or number
    as a label. A float shows with FLOAT_FORMAT."""
    if isinstance(value, Widget):
        return value
    if value is None:
        return Label("")
    if isinstance(value, str) or isinstance(value, bool):
        return Label(str(value))
    if isinstance(value, numbers.Integral):
        return Label(str(int(value)))
    if isinstance(value, numbers.Real):
        return Label(format(float(value), FLOAT_FORMAT))
    raise TypeError(f"cannot show a {type(value).__name__}: {value!r}")


class KeyValue(Widget):
    """Key/value pairs laid out as a compact grid. A value is anything as_widget takes."""

    def __init__(self, items: dict):
        self.items = {key: as_widget(value) for key, value in items.items()}

    def html(self, page_dir: str) -> str:
        pairs = "".join(f"<div><dt>{escape(key)}</dt><dd>{value.html(page_dir)}</dd></div>"
                        for key, value in self.items.items())
        return f'<dl class="keyvalue">{pairs}</dl>'


class Table(Widget):
    """Rows of cells under column headings, like a QTableWidget.

    A cell is anything as_widget takes, so a layout can sit in a cell too. A row given a
    target opens it when clicked anywhere. Clicking a heading sorts the rows, and a
    filterable table has a box above it that hides rows not containing the text typed.
    """

    def __init__(self, columns: list[str], filterable: bool = True):
        if not columns:
            raise ValueError("a table needs at least one column")
        self.columns = list(columns)
        self.filterable = filterable
        self.rows: list[tuple[list, list[Widget], str | None]] = []  # values as given, their widgets, target

    def add_row(self, cells: list, target: str | None = None) -> None:
        """Append a row. Target is the site-relative page the whole row opens."""
        if len(cells) != len(self.columns):
            raise ValueError(f"row has {len(cells)} cells, table has {len(self.columns)} columns")
        self.rows.append((list(cells), [as_widget(value) for value in cells], target))

    def html(self, page_dir: str) -> str:
        head = "".join(f"<th>{escape(column)}</th>" for column in self.columns)
        rows = []
        for values, widgets, target in self.rows:
            attribute = "" if target is None else f' data-href="{href(target, page_dir)}"'
            cells = "".join(_td_html(value, widget, page_dir) for value, widget in zip(values, widgets))
            rows.append(f"<tr{attribute}>{cells}</tr>")
        filter_box = '<input class="filter" type="search" placeholder="Filter rows">' if self.filterable else ""
        return (f'<div class="table">{filter_box}<div class="tablewrap"><table><thead><tr>{head}</tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div></div>')


def _td_html(value, widget: Widget, page_dir: str) -> str:
    """A table cell. A plain number is right-aligned and sorts by its full value, not its text."""
    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        return f'<td class="num" data-sort="{float(value)!r}">{widget.html(page_dir)}</td>'
    return f"<td>{widget.html(page_dir)}</td>"
