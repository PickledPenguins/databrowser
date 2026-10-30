"""Layouts that place widgets, as in Qt: a vertical or horizontal box and a grid. A Page is
the top-level vertical layout, and writes itself as an HTML file."""

from __future__ import annotations

import os
import posixpath
import tempfile
from importlib import resources
from pathlib import Path, PurePosixPath

from databrowser.widgets import Link, Widget, escape, href

STATIC_DIR = "_static"  # site-relative directory the stylesheet and script are copied to
STATIC_FILES = ("style.css", "browser.js")


def _check_spacing(spacing_px: int) -> None:
    if spacing_px < 0:
        raise ValueError(f"spacing must not be negative, got {spacing_px}")


class Layout(Widget):
    """Base of every layout. A layout is also a widget, so it can sit in a table cell."""


class BoxLayout(Layout):
    """Items in a line, in the order added, spacing_px apart. VBoxLayout stacks them top to
    bottom and HBoxLayout puts them left to right."""

    css_class = ""

    def __init__(self, spacing_px: int = 8):
        _check_spacing(spacing_px)
        self.spacing_px = spacing_px
        self.items: list[tuple[Widget, int]] = []  # widget, stretch

    def add_widget(self, widget: Widget, stretch: int = 0) -> Widget:
        """Append a widget and return it. A positive stretch shares out the spare room, in
        proportion to the other items' stretch."""
        if not isinstance(widget, Widget):
            raise TypeError(f"a layout holds widgets, not {type(widget).__name__}")
        if stretch < 0:
            raise ValueError(f"stretch must not be negative, got {stretch}")
        self.items.append((widget, stretch))
        return widget

    def add_layout(self, layout: Layout, stretch: int = 0) -> Layout:
        """Append a layout nested in this one and return it."""
        if not isinstance(layout, Layout):
            raise TypeError(f"add_layout takes a layout, not {type(layout).__name__}")
        return self.add_widget(layout, stretch)

    def html(self, page_dir: str) -> str:
        items = "".join(f'<div class="item"{_grow_style(stretch)}>{widget.html(page_dir)}</div>'
                        for widget, stretch in self.items)
        return f'<div class="{self.css_class}" style="gap:{self.spacing_px}px">{items}</div>'


def _grow_style(stretch: int) -> str:
    return f' style="flex-grow:{stretch}"' if stretch else ""


class VBoxLayout(BoxLayout):
    """Items stacked top to bottom."""

    css_class = "vbox"


class HBoxLayout(BoxLayout):
    """Items left to right. The row scrolls sideways when it is wider than the page."""

    css_class = "hbox"


class GridLayout(Layout):
    """Items placed in rows and columns, spacing_px apart. Each column is as wide as its
    widest item, so images of one width line up. An item may span several rows or columns."""

    def __init__(self, spacing_px: int = 2):
        _check_spacing(spacing_px)
        self.spacing_px = spacing_px
        self.items: list[tuple[Widget, int, int, int, int]] = []  # widget, row, column, row span, column span

    def add_widget(self, widget: Widget, row: int, column: int, row_span: int = 1, column_span: int = 1) -> Widget:
        """Place a widget with its top left in the cell at row and column, both from 0, and return it."""
        if not isinstance(widget, Widget):
            raise TypeError(f"a layout holds widgets, not {type(widget).__name__}")
        if row < 0 or column < 0:
            raise ValueError(f"grid cell ({row}, {column}) is negative")
        if row_span < 1 or column_span < 1:
            raise ValueError(f"grid spans must be at least 1, got {row_span} by {column_span}")
        self.items.append((widget, row, column, row_span, column_span))
        return widget

    def add_layout(self, layout: Layout, row: int, column: int, row_span: int = 1, column_span: int = 1) -> Layout:
        """Place a layout nested in this one, as add_widget does, and return it."""
        if not isinstance(layout, Layout):
            raise TypeError(f"add_layout takes a layout, not {type(layout).__name__}")
        return self.add_widget(layout, row, column, row_span, column_span)

    def html(self, page_dir: str) -> str:
        n_columns = max((column + span for _, _, column, _, span in self.items), default=0)
        items = "".join(f'<div class="item" style="grid-area:{row + 1}/{column + 1}/span {row_span}/span {column_span}">'
                        f"{widget.html(page_dir)}</div>"
                        for widget, row, column, row_span, column_span in self.items)
        style = f"gap:{self.spacing_px}px;grid-template-columns:repeat({n_columns},max-content)"
        return f'<div class="grid" style="{style}">{items}</div>'


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


class Page(VBoxLayout):
    """One HTML page at a site-relative path: the top-level layout, stacking its widgets top to bottom.

    Above the body sits a bar with the breadcrumb trail (crumbs, then the title) and the nav
    layout at its right, for links such as previous and next. The header and footer are
    layouts too, shown above and below the body when they hold anything.
    """

    def __init__(self, path: str, title: str, crumbs: list[Link] = (), spacing_px: int = 12):
        super().__init__(spacing_px)
        _check_page_path(path)
        self.path = path
        self.title = title
        self.crumbs = list(crumbs)  # links to the pages above this one, top first
        self.nav = HBoxLayout(spacing_px=12)
        self.header = VBoxLayout(spacing_px=4)
        self.footer = VBoxLayout(spacing_px=4)

    def child(self, path: str, title: str, spacing_px: int = 12) -> Page:
        """A new page below this one: its crumbs are this page's, then a link to this page."""
        return Page(path, title, crumbs=self.crumbs + [Link(self.title, self.path)], spacing_px=spacing_px)

    def render(self) -> str:
        """The whole page as HTML text."""
        page_dir = posixpath.dirname(self.path)
        crumbs = "".join(f'{link.html(page_dir)}<span class="sep">/</span>' for link in self.crumbs)
        header = f'<header class="pageheader">{self.header.html(page_dir)}</header>' if self.header.items else ""
        footer = f'<footer class="pagefooter">{self.footer.html(page_dir)}</footer>' if self.footer.items else ""
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(self.title)}</title>
<link rel="stylesheet" href="{href(f"{STATIC_DIR}/style.css", page_dir)}">
<script src="{href(f"{STATIC_DIR}/browser.js", page_dir)}" defer></script>
</head>
<body>
<div class="topbar">
<nav class="crumbs">{crumbs}<span class="here">{escape(self.title)}</span></nav>
<nav class="links">{self.nav.html(page_dir)}</nav>
</div>
{header}
<main>
{self.html(page_dir)}
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
