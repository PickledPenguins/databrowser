"""Generated inputs against the rules every page keeps, whatever text, values and paths it is
given: it is well formed, shows each text exactly as given, aligns a column to the right only
when every value in it is a number, picks the more readable banner text color, and links
every relative path to the file it names."""

import posixpath
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from urllib.parse import unquote

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from databrowser import Badge, DataPage, GroupPage
from databrowser import pages
from html_tree import parse

pytestmark = pytest.mark.long

SETTINGS = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])

# Any text a file can hold: no lone surrogates, which UTF-8 cannot encode. Carriage returns
# are left out because HTML reads a CR, or CR LF, as one LF, so a CR does not survive.
text = st.text(st.characters(exclude_categories=["Cs"], exclude_characters="\r"), max_size=40)
one_line = st.text(st.characters(exclude_categories=["Cs"], exclude_characters="\r\n"), max_size=40)
number = st.one_of(st.integers(), st.floats(allow_nan=False), st.decimals(allow_nan=False), st.fractions())
badge = st.builds(Badge, one_line, st.sampled_from(pages._BADGE_KINDS))
value = st.one_of(st.none(), number, one_line, st.booleans(), badge)
# A file or directory name: anything but / and NUL, and not . or .., which name no file.
name = st.text(st.characters(exclude_categories=["Cs"], exclude_characters="/\0"), min_size=1, max_size=12).filter(
    lambda part: part not in (".", ".."))
relative_path = st.lists(name, min_size=1, max_size=4).map("/".join)


def shown(value) -> str:
    """The text a table cell shows for value."""
    if value is None:
        return ""
    return value.text if isinstance(value, Badge) else str(value)


def contrast(first: float, second: float) -> float:
    """The WCAG contrast ratio of two relative luminances."""
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)


def luminance(color: str) -> float:
    digits = color[1:] if len(color) == 7 else "".join(digit * 2 for digit in color[1:])
    linear = []
    for i in (0, 2, 4):
        channel = int(digits[i:i + 2], 16) / 255
        linear.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


@SETTINGS
@given(text)
def test_text_shows_as_given_with_each_newline_a_line_break(value):
    assert parse(f"<p>{pages._text_html(value)}</p>").find("p").text() == value


@SETTINGS
@given(title=one_line, header=text, footer=text, columns=st.lists(one_line, min_size=1, max_size=4), data=st.data())
def test_group_page_shows_every_text_as_given(site, title, header, footer, columns, data):
    rows = data.draw(st.lists(st.lists(value, min_size=len(columns), max_size=len(columns)), max_size=5))
    page = GroupPage("index.html", title, columns, header=header, footer=footer)
    for index, values in enumerate(rows):
        page.add_row(f"{index}.html", values)
    page.write()
    root = parse(Path("index.html").read_text(encoding="utf-8"))
    assert root.find("title").text() == title
    assert root.find("h1").text() == title
    if header:
        assert root.find("header").find("p").text() == header
    if footer:
        assert root.find("footer").text() == footer
    assert [cell.text() for cell in root.find("thead").find_all("th")] == columns
    assert [[cell.text() for cell in row.find_all("td")] for row in root.find("tbody").find_all("tr")] == \
        [[shown(cell) for cell in values] for values in rows]


@SETTINGS
@given(columns=st.integers(1, 4), data=st.data())
def test_column_aligned_right_only_when_every_value_is_a_number(site, columns, data):
    rows = data.draw(st.lists(st.lists(value, min_size=columns, max_size=columns), min_size=1, max_size=6))
    page = GroupPage("index.html", "T", [f"c{i}" for i in range(columns)])
    for values in rows:
        page.add_row("x.html", values)
    page.write()
    root = parse(Path("index.html").read_text(encoding="utf-8"))
    for index, cell in enumerate(root.find("thead").find_all("th")):
        present = [values[index] for values in rows if values[index] is not None]
        numeric = (index > 0 and bool(present)
                   and all(isinstance(item, (int, float, Decimal, Fraction)) and not isinstance(item, bool)
                           for item in present))
        assert ("num" in cell.classes) == numeric
        for row in root.find("tbody").find_all("tr"):
            assert ("num" in row.find_all("td")[index].classes) == numeric


@SETTINGS
@given(st.from_regex(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", fullmatch=True))
def test_banner_text_color_is_the_more_readable_one(background):
    chosen = pages._banner_text_color(background)
    other = "#111827" if chosen == "#ffffff" else "#ffffff"
    assert contrast(luminance(background), luminance(chosen)) >= contrast(luminance(background), luminance(other))


@SETTINGS
@given(page=relative_path, target=relative_path)
def test_link_to_names_the_target_from_the_page(page, target):
    link = GroupPage(page + ".html", "T", ["Name"])._link_to(target)
    assert "#" not in link and "?" not in link and " " not in link
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(page + ".html"), unquote(link)))
    assert resolved == posixpath.normpath(target)


@SETTINGS
@given(columns=st.integers(1, 4), data=st.data())
def test_data_page_shows_every_caption_and_names_every_image(site, columns, data):
    rows = data.draw(st.lists(st.tuples(
        st.lists(st.tuples(st.one_of(st.none(), relative_path), text), min_size=columns, max_size=columns),
        one_line), max_size=4))
    titles = data.draw(st.one_of(st.none(), st.lists(one_line, min_size=columns, max_size=columns)))
    page = DataPage("index.html", "T", columns=columns, column_titles=titles)
    for images, label in rows:
        page.add_row(images, label=label)
    page.write()
    root = parse(Path("index.html").read_text(encoding="utf-8"))
    figures = root.find_all("figure")
    expected = [pair for images, _ in rows for pair in images]
    assert [figure.find("figcaption").text() for figure in figures] == [caption for _, caption in expected]
    images = [(figure.find_all("img") or [None])[0] for figure in figures]
    assert [unquote(image.attrs["src"]) if image else None for image in images] == [path for path, _ in expected]
    for (images_in_row, label), section in zip(rows, root.find_all("section", "image-row")):
        for column, ((path, caption), figure) in enumerate(zip(images_in_row, section.find_all("figure"))):
            parts = [(titles or [""] * columns)[column], label, *caption.split("\n")]
            alt = ", ".join(part for part in parts if part)
            if path is None:
                no_image = f"No image: {alt}" if alt else "No image"
                assert figure.find("div", "no-image").attrs["aria-label"] == no_image
            else:
                assert figure.find("img").attrs["alt"] == (alt or path.rsplit("/", 1)[-1])

