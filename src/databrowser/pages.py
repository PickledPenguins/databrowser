"""Write static HTML pages for browsing data.

A GroupPage holds a table whose rows link to other pages. A DataPage holds a grid of images,
a fixed number per row, with text under each. Both take optional header and footer text, and
a Theme that gives every page of a site the same banners, banner color and title image. A
page made with a parent shows a breadcrumb trail back to the top page. A Badge marks a
status in a table cell or above a row of images.
Paths given to a page as text (links, images) are relative to the page file itself.

The look comes from the CSS files in the style directory beside this module, one per part
of the page (colors, top banner, table, image grid ...), each commented with the HTML it
styles and its common edits. Every page gets a copy of them when it is written, so an edit
shows once the pages are written again. A custom style for one part, such as
03-top-banner-user-page.css, goes in the same directory and applies only to pages whose
Theme names it: Theme(styles={"top-banner": "user-page"}).

The pages aim at WCAG 2.2 AA: text contrast of at least 4.5:1, a visible keyboard focus,
alt text on every image, headings and landmarks a screen reader can jump between, and no
meaning carried by color alone.
"""

import html
import numbers
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

STYLE_DIR = Path(__file__).parent / "style"

# Parts of a page that can take a custom style. Each is the class of the part's outer element.
STYLE_PARTS = ("top-banner", "breadcrumbs", "title", "table", "image-grid", "footer", "bottom-banner")


def _file_part(file: Path) -> str:
    """The part a CSS file styles: 03-top-banner-user-page.css gives top-banner-user-page."""
    return file.stem.split("-", 1)[-1]


def _is_custom_style(file: Path) -> bool:
    """Whether file is a custom style for one part, such as 03-top-banner-user-page.css."""
    return any(_file_part(file).startswith(part + "-") for part in STYLE_PARTS)


def _custom_style_file(part: str, name: str) -> Path:
    """The CSS file of custom style name for part, such as 03-top-banner-user-page.css."""
    if part not in STYLE_PARTS:
        raise ValueError(f"no part {part!r} to style, parts are {', '.join(STYLE_PARTS)}")
    files = [file for file in STYLE_DIR.glob("*.css") if _file_part(file) == f"{part}-{name}"]
    if len(files) != 1:
        found = f"{len(files)} files" if files else "no file"
        raise FileNotFoundError(f"{found} named NN-{part}-{name}.css in {STYLE_DIR}")
    return files[0]


def _luminance(color: str) -> float:
    """The relative luminance of a #rgb or #rrggbb color, as WCAG defines it."""
    digits = color[1:]
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    channels = [int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _banner_text_color(background: str) -> str:
    """White or near black, whichever contrasts more with background, a #rgb or #rrggbb color."""
    if not re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", background):
        raise ValueError(f"banner_color must be #rgb or #rrggbb, got {background!r}")
    luminance = _luminance(background)
    on_white = 1.05 / (luminance + 0.05)
    on_dark = (luminance + 0.05) / (_luminance("#111827") + 0.05)
    return "#ffffff" if on_white >= on_dark else "#111827"



@dataclass(frozen=True)
class Theme:
    """Look shared by every page of a site. Make one and pass it to each page.

    banner is text in a bar across the top of the page, such as the lab or project name. It
    links to the top page of the site. bottom_banner is text in a matching bar across the
    bottom, below the page's own footer, such as a contact or a notice. A newline in it starts
    a new line. banner_color, #rgb or #rrggbb, colors both bars, and their text turns white or
    black to stay readable. Without it the bars take --banner-bg from 01-colors.css.
    banner_image is a picture behind both bars and title_image one behind the page title, each
    darkened so the text stays readable. Give each path relative to the current directory,
    not the page: each page links it by the right relative path.

    styles picks custom styles for parts of the page, such as {"top-banner": "user-page"}:
    the part's element gets the class top-banner-user-page as well as top-banner, and the
    page includes 03-top-banner-user-page.css from the style directory after the default
    files, so its rules override theirs. Parts are listed in STYLE_PARTS. Give a page its
    own look with its own Theme, dataclasses.replace(theme, styles={...}).
    """

    banner: str = ""
    bottom_banner: str = ""
    banner_color: str | None = None
    banner_image: str | None = None
    title_image: str | None = None
    styles: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.banner_color is not None:
            _banner_text_color(self.banner_color)
        for part, name in self.styles.items():
            _custom_style_file(part, name)

    def classes(self, part: str) -> str:
        """The class attribute value for part's element: part, plus its custom style if any."""
        name = self.styles.get(part)
        return f"{part} {part}-{name}" if name else part


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
    """Whether value is a number, which a table aligns to the right: int, float, Decimal,
    Fraction or a NumPy number, but not a bool."""
    return isinstance(value, numbers.Number) and not isinstance(value, bool)


def _url(path) -> str:
    """path, a str or Path, as a relative URL: / between its parts, and every character a URL
    reads specially (# ? % space and the like) percent-encoded, so any file name opens."""
    return quote(os.fspath(path).replace(os.sep, "/"))


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
        """The relative URL from this page to target, a page or a path relative to the current directory."""
        target_path = target.path if isinstance(target, _Page) else target
        return _url(os.path.relpath(target_path, self.path.parent))

    def _breadcrumbs_html(self, trail: list["_Page"]) -> str:
        """A breadcrumb trail from the top page down to this one, or nothing for a page with no parent."""
        if len(trail) < 2:
            return ""
        items = [f'<li><a href="{self.link_to(page)}">{html.escape(page.title)}</a></li>'
                 for page in trail[:-1]]
        items.append(f'<li><span aria-current="page">{html.escape(self.title)}</span></li>')
        return f'<nav class="{self.theme.classes("breadcrumbs")}" aria-label="Breadcrumb"><ol class="page-width">{"".join(items)}</ol></nav>'

    def _style_html(self) -> str:
        """The page's CSS: the default files in name order, then the theme's custom styles,
        then its banner color, each overriding what came before."""
        theme = self.theme
        files = [file for file in sorted(STYLE_DIR.glob("*.css")) if not _is_custom_style(file)]
        files += [_custom_style_file(part, name) for part, name in theme.styles.items()]
        css = "\n".join(file.read_text(encoding="utf-8") for file in files)
        style = f"<style>\n{css}</style>"
        if theme.banner_color:
            text_color = _banner_text_color(theme.banner_color)
            style += f"\n<style>:root {{ --banner-bg: {theme.banner_color}; --banner-text: {text_color}; }}</style>"
        return style

    def _background_html(self, image: str | None) -> str:
        """A style attribute putting image, darkened, behind an element, or nothing for no image.
        It sits on the element, not in the CSS, so the link is relative to the page."""
        if not image:
            return ""
        shade = "linear-gradient(rgb(8 12 24 / 0.62), rgb(8 12 24 / 0.62))"
        return f' style="background-image: {shade}, url(&quot;{self.link_to(image)}&quot;)"'

    def _write(self, body: str) -> None:
        """Write the whole page: banner, breadcrumbs and title band above the body, the footer
        text and bottom banner below."""
        trail = [self]
        while trail[0].parent is not None:
            trail.insert(0, trail[0].parent)
        theme = self.theme
        banner_html = ""
        if theme.banner:
            home = self.link_to(trail[0])
            banner_html = (f'<div class="{theme.classes("top-banner")}"{self._background_html(theme.banner_image)}><div class="page-width">'
                           f'<a href="{home}">{html.escape(theme.banner)}</a></div></div>')
        header_html = f"<p>{_text_html(self.header)}</p>" if self.header else ""
        footer_html = ""
        if self.footer:
            footer_html = f'<footer class="{theme.classes("footer")}"><div class="page-width">{_text_html(self.footer)}</div></footer>'
        if theme.bottom_banner:
            footer_html += (f'\n<div class="{theme.classes("bottom-banner")}"{self._background_html(theme.banner_image)}><div class="page-width">'
                            f'{_text_html(theme.bottom_banner)}</div></div>')
        page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(self.title)}</title>
{self._style_html()}
</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
{banner_html}
{self._breadcrumbs_html(trail)}
<header class="{theme.classes("title")}"{self._background_html(theme.title_image)}><div class="page-width"><h1>{html.escape(self.title)}</h1>{header_html}</div></header>
<main class="page-width" id="content">
{body}
</main>
{footer_html}
</body>
</html>
"""
        # Written beside the page and renamed over it, so a browser or web server reading the
        # page while a site is rebuilt sees the old page or the new one, never part of one.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        partial = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        try:
            partial.write_text(page, encoding="utf-8")
            os.replace(partial, self.path)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise


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
        if not columns:
            raise ValueError("a table needs at least one column")
        super().__init__(path, title, header, footer, parent, theme)
        self.columns = list(columns)
        self.rows: list[tuple[str, list]] = []

    def add_row(self, link, values: list) -> None:
        """Add a row linking to link: a page, or a path relative to this page. The first value
        shows as the link, and clicking anywhere on the row opens it. A value may be a Badge."""
        if len(values) != len(self.columns):
            raise ValueError(f"row has {len(values)} values, table has {len(self.columns)} columns")
        href = self.link_to(link) if isinstance(link, _Page) else _url(link)
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
            cells = f'<td><a href="{href}">{first}</a></td>'
            cells += "".join(f"<td{align[i]}>{value}</td>" for i, value in enumerate(rest, start=1))
            rows.append(f"<tr>{cells}</tr>")
        self._write(f'<div class="{self.theme.classes("table")}"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')



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
            parts.append(f'<div class="column-titles" aria-hidden="true" {columns_style}>{titles}</div>')
        for label, badge, images in self.rows:
            figures = []
            for column_title, (image, text) in zip(column_titles, images):
                alt = html.escape(", ".join(filter(None, [column_title, label, *str(text).split("\n")])))
                if image is None:
                    picture = f'<div class="no-image" role="img" aria-label="No image: {alt}">no image</div>'
                else:
                    src = _url(image)
                    picture = f'<a href="{src}"><img src="{src}" alt="{alt}" loading="lazy"></a>'
                figures.append(f"<figure>{picture}<figcaption>{_text_html(text)}</figcaption></figure>")
            heading = ""
            if label or badge:
                heading = f"<h2>{html.escape(label)}{badge.html() if badge else ''}</h2>"
            strip = f'<div class="image-strip" {columns_style}>{"".join(figures)}</div>'
            parts.append(f'<section class="image-row">{heading}{strip}</section>')
        grid_style = ""
        if self.max_image_width_px:
            # Images plus the 2 px gaps between them and the 2 px strip padding on each side.
            width_px = self.columns * self.max_image_width_px + (self.columns - 1) * 2 + 4
            grid_style = f' style="max-width: {width_px}px"'
        self._write(f'<div class="{self.theme.classes("image-grid")}"{grid_style}>\n' + "\n".join(parts) + "\n</div>")
