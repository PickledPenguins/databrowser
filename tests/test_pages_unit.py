"""Unit tests of src/databrowser/pages.py: each function and class, its branches and its errors."""

import dataclasses
import os
import re
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from databrowser import pages
from databrowser.pages import Badge, DataPage, GroupPage, Theme
from html_tree import parse

DEFAULT_CSS = ["01-colors.css", "02-page.css", "03-top-banner.css", "04-breadcrumbs.css", "05-title.css",
               "06-table.css", "07-badges.css", "08-image-grid.css", "09-footer.css", "10-bottom-banner.css",
               "11-print.css"]


def css_files_in(page_html: str, style_dir: Path) -> list[str]:
    """The style files whose text the page's first style block holds, in order."""
    css = re.search(r"<style>\n(.*?)</style>", page_html, re.S).group(1)
    names, position = [], 0
    files = sorted(style_dir.glob("*.css"))
    while position < len(css):
        file = next(file for file in files if css.startswith(file.read_text(encoding="utf-8"), position))
        names.append(file.name)
        position += len(file.read_text(encoding="utf-8")) + 1
    return names


def tree(path):
    """The page at path as an element tree."""
    return parse(Path(path).read_text(encoding="utf-8"))


def body(path) -> str:
    """The page at path from <body> on, without the inlined CSS."""
    text = Path(path).read_text(encoding="utf-8")
    return text[text.index("</head>\n<body>") + len("</head>\n"):]


class TestFilePart:
    def test_drops_the_number_prefix(self):
        assert pages._file_part(Path("03-top-banner-user-page.css")) == "top-banner-user-page"

    def test_name_without_a_dash_is_kept_whole(self):
        assert pages._file_part(Path("colors.css")) == "colors"


class TestIsCustomStyle:
    @pytest.mark.parametrize("name", ["03-top-banner-user-page.css", "08-image-grid-dense.css", "06-table-x.css"])
    def test_part_plus_a_name_is_custom(self, name):
        assert pages._is_custom_style(Path(name)) is True

    @pytest.mark.parametrize("name", DEFAULT_CSS)
    def test_default_files_are_not_custom(self, name):
        assert pages._is_custom_style(Path(name)) is False


class TestCustomStyleFile:
    def test_finds_the_file_for_part_and_name(self):
        assert pages._custom_style_file("top-banner", "user-page") == pages._STYLE_DIR / "03-top-banner-user-page.css"

    def test_unknown_part_is_refused_with_the_parts_listed(self):
        with pytest.raises(ValueError) as error:
            pages._custom_style_file("badges", "big")
        assert str(error.value) == ("no part 'badges' to style, parts are top-banner, breadcrumbs, title, table, "
                                    "image-grid, footer, bottom-banner")

    def test_missing_file_names_the_file_wanted_and_the_directory(self, style_dir):
        with pytest.raises(FileNotFoundError) as error:
            pages._custom_style_file("table", "wide")
        assert str(error.value) == f"no file named NN-table-wide.css in {style_dir}"

    def test_two_files_for_one_style_are_refused(self, style_dir):
        (style_dir / "06-table-wide.css").write_text("", encoding="utf-8")
        (style_dir / "12-table-wide.css").write_text("", encoding="utf-8")
        with pytest.raises(FileNotFoundError) as error:
            pages._custom_style_file("table", "wide")
        assert str(error.value) == f"2 files named NN-table-wide.css in {style_dir}"

    def test_a_name_only_prefixing_a_file_does_not_match_it(self, style_dir):
        (style_dir / "06-table-wide-dark.css").write_text("", encoding="utf-8")
        with pytest.raises(FileNotFoundError) as error:
            pages._custom_style_file("table", "wide")
        assert str(error.value) == f"no file named NN-table-wide.css in {style_dir}"


class TestBannerTextColor:
    @pytest.mark.parametrize("background, text", [
        ("#000000", "#ffffff"), ("#ffffff", "#000000"), ("#0f3d3e", "#ffffff"), ("#ffff00", "#000000"),
        ("#2b6fd6", "#ffffff"), ("#000", "#ffffff"), ("#FFF", "#000000"), ("#AbCdEf", "#000000"),
    ])
    def test_picks_the_text_color_that_contrasts_more(self, background, text):
        assert pages._banner_text_color(background) == text

    def test_mid_gray_boundary(self):
        # #757575 contrasts more with white, #767676 with black: pins the formula's constants.
        assert pages._banner_text_color("#757575") == "#ffffff"
        assert pages._banner_text_color("#767676") == "#000000"

    def test_dark_text_where_it_contrasts_more_than_white_near_the_boundary(self):
        assert pages._banner_text_color("#d0d") == "#000000"

    @pytest.mark.parametrize("background", ["#c34bb4", "#7b7b7b"])
    def test_contrast_reaches_wcag_aa_where_near_black_text_fell_short(self, background):
        # Regression: with #111827 as the dark text, these got white at 4.21:1 and 4.23:1.
        text = pages._banner_text_color(background)
        lighter, darker = sorted([pages._luminance(background), pages._luminance(text)], reverse=True)
        assert (lighter + 0.05) / (darker + 0.05) >= 4.5

    @pytest.mark.parametrize("color, luminance", [("#000", 0.0), ("#fff", 1.0), ("#111827", 0.00919),
                                                  ("#ff0000", 0.2126), ("#00ff00", 0.7152), ("#0000ff", 0.0722),
                                                  ("#0f0", 0.7152), ("#0a0a0a", 0.003035)])
    def test_luminance(self, color, luminance):
        assert pages._luminance(color) == pytest.approx(luminance, abs=5e-6)

    def test_short_form_doubles_each_digit(self):
        assert pages._banner_text_color("#888") == pages._banner_text_color("#888888") == "#000000"
        assert pages._banner_text_color("#666") == pages._banner_text_color("#666666") == "#ffffff"

    def test_channels_are_weighted_green_most(self):
        # Pure green is light enough for dark text, pure blue and red are not.
        assert pages._banner_text_color("#00ff00") == "#000000"
        assert pages._banner_text_color("#0000ff") == "#ffffff"
        assert pages._banner_text_color("#ff0000") == "#000000"
        assert pages._banner_text_color("#e00000") == "#ffffff"

    @pytest.mark.parametrize("color", ["red", "#12", "#1234", "#12345", "#1234567", "fff", "#ggg", "#fff ", " #fff",
                                       "", "rgb(0,0,0)"])
    def test_anything_but_rgb_or_rrggbb_is_refused(self, color):
        with pytest.raises(ValueError) as error:
            pages._banner_text_color(color)
        assert str(error.value) == f"banner_color must be #rgb or #rrggbb, got {color!r}"


class TestTheme:
    def test_defaults(self):
        theme = Theme()
        assert (theme.banner, theme.bottom_banner, theme.banner_color, theme.banner_image, theme.title_image,
                theme.styles) == ("", "", None, None, None, {})

    def test_bad_banner_color_is_refused_when_made(self):
        with pytest.raises(ValueError, match=r"^banner_color must be #rgb or #rrggbb, got 'navy'$"):
            Theme(banner_color="navy")

    def test_style_for_an_unknown_part_is_refused_when_made(self):
        with pytest.raises(ValueError, match=r"^no part 'colors' to style"):
            Theme(styles={"colors": "dark"})

    def test_style_without_a_file_is_refused_when_made(self):
        with pytest.raises(FileNotFoundError, match=r"^no file named NN-top-banner-nope\.css in "):
            Theme(styles={"top-banner": "nope"})

    def test_is_frozen(self):
        with pytest.raises(dataclasses.FrozenInstanceError):
            Theme().banner = "x"

    def test_styles_are_read_only(self):
        with pytest.raises(TypeError):
            Theme().styles["top-banner"] = "user-page"

    def test_equal_themes_hash_equal(self):
        # Regression: the read-only styles mapping made hash(Theme()) raise TypeError.
        first = Theme(banner="Lab", styles={"top-banner": "user-page"})
        second = Theme(banner="Lab", styles={"top-banner": "user-page"})
        assert hash(first) == hash(second)
        assert {first: 1}[second] == 1

    def test_pages_without_a_theme_share_one(self):
        assert GroupPage("a.html", "A", ["Name"]).theme is DataPage("b.html", "B", columns=1).theme

    def test_styles_are_a_copy_of_the_callers(self):
        styles = {"top-banner": "user-page"}
        theme = Theme(styles=styles)
        styles["top-banner"] = "nope"
        assert theme._classes("top-banner") == "top-banner top-banner-user-page"

    def test_replace_keeps_styles_read_only(self):
        theme = dataclasses.replace(Theme(styles={"top-banner": "user-page"}), banner="Lab")
        assert theme.styles == {"top-banner": "user-page"}
        with pytest.raises(TypeError):
            theme.styles["footer"] = "x"

    def test_classes_of_an_unstyled_part_is_the_part(self):
        assert Theme()._classes("table") == "table"

    def test_classes_of_a_styled_part_adds_the_custom_class(self):
        theme = Theme(styles={"top-banner": "user-page"})
        assert theme._classes("top-banner") == "top-banner top-banner-user-page"
        assert theme._classes("footer") == "footer"


class TestBadge:
    def test_default_kind_is_info(self):
        assert Badge("note").kind == "info"

    @pytest.mark.parametrize("kind", ["ok", "info", "warn", "error"])
    def test_html_carries_the_kind_class(self, kind):
        assert Badge("done", kind)._html() == f'<span class="badge badge-{kind}">done</span>'

    def test_text_is_escaped(self):
        assert Badge('<b>"A" & B</b>', "error")._html() == (
            '<span class="badge badge-error">&lt;b&gt;&quot;A&quot; &amp; B&lt;/b&gt;</span>')

    @pytest.mark.parametrize("kind", ["warning", "OK", "", "success"])
    def test_unknown_kind_is_refused(self, kind):
        with pytest.raises(ValueError) as error:
            Badge("x", kind)
        assert str(error.value) == f"badge kind {kind!r} is not one of ok, info, warn, error"


class TestTextHtml:
    def test_newlines_become_line_breaks(self):
        assert pages._text_html("one\ntwo\n") == "one<br>two<br>"

    def test_markup_is_escaped(self):
        assert pages._text_html("<a> & 'b'") == "&lt;a&gt; &amp; &#x27;b&#x27;"

    def test_non_text_is_shown_as_text(self):
        assert pages._text_html(3.5) == "3.5"

    def test_empty_stays_empty(self):
        assert pages._text_html("") == ""


class TestIsNumber:
    @pytest.mark.parametrize("value", [0, 1, -2, 1.5, float("nan"), 10**30])
    def test_ints_and_floats_are_numbers(self, value):
        assert pages._is_number(value) is True

    @pytest.mark.parametrize("value", [Decimal("2.50"), Fraction(1, 3), 1j])
    def test_other_number_types_are_numbers(self, value):
        assert pages._is_number(value) is True

    def test_numpy_numbers_are_numbers(self):
        # Regression: NumPy integers are not int, so a column of them was aligned left.
        numpy = pytest.importorskip("numpy")
        assert [pages._is_number(value) for value in (numpy.int64(3), numpy.uint8(1), numpy.float32(0.5))] == [
            True, True, True]
        assert pages._is_number(numpy.bool_(True)) is False

    @pytest.mark.parametrize("value", [True, False, "1", None, Badge("1"), [1]])
    def test_bools_text_and_others_are_not(self, value):
        assert pages._is_number(value) is False


class TestUrl:
    @pytest.mark.parametrize("path, url", [
        ("runs/a.png", "runs/a.png"), ("run #3/plot.png", "run%20%233/plot.png"), ("a?b.png", "a%3Fb.png"),
        ("100%.png", "100%25.png"), ("Wellen/été.png", "Wellen/%C3%A9t%C3%A9.png"),
        ("../up/x_y-z~1.png", "../up/x_y-z~1.png"), ('a"<b>&c.png', "a%22%3Cb%3E%26c.png"),
    ])
    def test_characters_a_url_reads_specially_are_encoded(self, path, url):
        assert pages._url(path) == url

    def test_path_objects_are_accepted(self):
        assert pages._url(Path("runs") / "a b.png") == "runs/a%20b.png"

    @pytest.mark.parametrize("url, shown", [
        ("https://grafana.example/d/abc?var=1&x=2#top", "https://grafana.example/d/abc?var=1&amp;x=2#top"),
        ("file:///data/run 1/x.png", "file:///data/run%201/x.png"),
        ("HTTPS://CDN.example/X.png?w=2", "HTTPS://CDN.example/X.png?w=2"),
        ("https://cdn.example/a%20b.png", "https://cdn.example/a%20b.png"),
        ('https://cdn.example/a b"<c>.png', "https://cdn.example/a%20b%22%3Cc%3E.png"),
    ])
    def test_a_url_with_a_scheme_is_kept(self, url, shown):
        # Regression: a URL was quoted as a file path, https:// becoming a relative https%3A//
        assert pages._url(url) == shown

    @pytest.mark.parametrize("path, url", [("c:/data/x.png", "c%3A/data/x.png"), ("sweep:3/x.png", "sweep%3A3/x.png")])
    def test_a_colon_without_slashes_is_a_path(self, path, url):
        assert pages._url(path) == url

    def test_link_to_is_a_url(self, site):
        # Regression: a # in a directory name cut the link short, the browser reading a fragment.
        page = GroupPage("index.html", "Top", ["Name"])
        assert page._link_to(DataPage("sample #3/index.html", "s", columns=1)) == "sample%20%233/index.html"


class TestCellHtml:
    def test_badge_is_its_pill(self):
        assert pages._cell_html(Badge("ok", "ok")) == '<span class="badge badge-ok">ok</span>'

    def test_none_is_empty(self):
        assert pages._cell_html(None) == ""

    @pytest.mark.parametrize("value, shown", [(0, "0"), (False, "False"), (2.5, "2.5"), ("a<b", "a&lt;b"), ("", "")])
    def test_anything_else_is_escaped_text(self, value, shown):
        assert pages._cell_html(value) == shown


class TestLinkTo:
    def test_page_in_a_subdirectory(self, site):
        top = GroupPage("index.html", "Top", ["Name"])
        child = GroupPage("a/b/index.html", "Child", ["Name"], parent=top)
        assert top._link_to(child) == "a/b/index.html"
        assert child._link_to(top) == "../../index.html"

    def test_sibling_directory(self, site):
        one = GroupPage("site/a/index.html", "A", ["Name"])
        assert one._link_to("site/b/plot.png") == "../b/plot.png"

    def test_same_directory(self, site):
        assert GroupPage("site/index.html", "A", ["Name"])._link_to("site/other.html") == "other.html"

    def test_absolute_and_relative_paths_mix(self, site):
        page = GroupPage("site/index.html", "A", ["Name"])
        assert page._link_to(site / "site" / "img" / "x.png") == "img/x.png"

    def test_a_url_is_linked_as_given(self, site):
        assert GroupPage("site/a/index.html", "A", ["Name"])._link_to("https://cdn.example/b.png?w=2") == (
            "https://cdn.example/b.png?w=2")


class TestBreadcrumbs:
    def test_a_page_without_parent_has_none(self, site):
        GroupPage("index.html", "Top", ["Name"]).write()
        assert "breadcrumbs" not in body("index.html")

    def test_trail_links_each_ancestor_and_marks_the_current_page(self, site):
        top = GroupPage("index.html", "Top & co", ["Name"])
        middle = GroupPage("a/index.html", "Middle", ["Name"], parent=top)
        leaf = DataPage("a/b/index.html", "Leaf <1>", columns=1, parent=middle)
        leaf.write()
        nav = tree("a/b/index.html").find("nav")
        assert nav.attrs == {"class": "breadcrumbs", "aria-label": "Breadcrumb"}
        links = [(a.attrs["href"], a.text()) for a in nav.find_all("a")]
        assert links == [("../../index.html", "Top & co"), ("../index.html", "Middle")]
        current = nav.find("span")
        assert (current.attrs, current.text()) == ({"aria-current": "page"}, "Leaf <1>")

    def test_custom_style_class(self, site, style_dir):
        (style_dir / "04-breadcrumbs-compact.css").write_text("", encoding="utf-8")
        top = GroupPage("index.html", "Top", ["Name"])
        theme = Theme(styles={"breadcrumbs": "compact"})
        GroupPage("a/index.html", "A", ["Name"], parent=top, theme=theme).write()
        assert '<nav class="breadcrumbs breadcrumbs-compact" aria-label="Breadcrumb">' in body("a/index.html")


class TestStyle:
    def test_default_files_inlined_in_name_order(self, site):
        GroupPage("index.html", "Top", ["Name"]).write()
        assert css_files_in(Path("index.html").read_text(encoding="utf-8"), pages._STYLE_DIR) == DEFAULT_CSS

    def test_custom_style_files_left_out_unless_named(self, site):
        GroupPage("index.html", "Top", ["Name"]).write()
        assert ".top-banner-user-page" not in Path("index.html").read_text(encoding="utf-8")

    def test_named_custom_styles_follow_the_defaults_in_theme_order(self, site, style_dir):
        (style_dir / "06-table-dense.css").write_text(".table-dense { padding: 0; }\n", encoding="utf-8")
        theme = Theme(banner="Lab", styles={"table": "dense", "top-banner": "user-page"})
        GroupPage("index.html", "Top", ["Name"], theme=theme).write()
        text = Path("index.html").read_text(encoding="utf-8")
        assert css_files_in(text, style_dir) == DEFAULT_CSS + ["06-table-dense.css", "03-top-banner-user-page.css"]
        assert '<div class="table table-dense">' in text
        assert '<div class="top-banner top-banner-user-page">' in text

    def test_no_banner_color_block_without_banner_color(self, site):
        GroupPage("index.html", "Top", ["Name"]).write()
        assert Path("index.html").read_text(encoding="utf-8").count("<style>") == 1

    def test_banner_color_block_sets_background_and_readable_text(self, site):
        GroupPage("index.html", "Top", ["Name"], theme=Theme(banner_color="#fde047")).write()
        assert ("</style>\n<style>:root { --banner-bg: #fde047; --banner-text: #000000; }</style>\n</head>"
                in Path("index.html").read_text(encoding="utf-8"))

    def test_banner_text_is_white_over_a_banner_image_whatever_the_color(self, site):
        # Regression: a light banner_color picked near-black text, written over the image's dark shade.
        theme = Theme(banner="Lab", banner_color="#e0f2f1", banner_image="b.png")
        GroupPage("index.html", "Top", ["Name"], theme=theme).write()
        assert ("<style>:root { --banner-bg: #e0f2f1; --banner-text: #ffffff; }</style>"
                in Path("index.html").read_text(encoding="utf-8"))

    def test_edited_css_shows_on_the_next_write(self, site, style_dir):
        page = GroupPage("index.html", "Top", ["Name"])
        (style_dir / "09-footer.css").write_text(".footer { color: red; }\n", encoding="utf-8")
        page.write()
        assert ".footer { color: red; }" in Path("index.html").read_text(encoding="utf-8")

    def test_an_empty_style_directory_is_an_error(self, site, style_dir):
        # Regression: a broken install with no style files wrote pages with no styling at all
        for file in style_dir.glob("*.css"):
            file.unlink()
        with pytest.raises(FileNotFoundError) as error:
            GroupPage("index.html", "Top", ["Name"]).write()
        assert str(error.value) == f"no style files in {style_dir}"
        assert list(site.glob("*.html")) == []

    def test_a_missing_style_directory_is_an_error(self, site, monkeypatch):
        monkeypatch.setattr(pages, "_STYLE_DIR", site / "style")
        with pytest.raises(FileNotFoundError) as error:
            GroupPage("index.html", "Top", ["Name"]).write()
        assert str(error.value) == f"no style files in {site / 'style'}"

    def test_a_style_file_not_in_utf8_is_named(self, site, style_dir):
        # Regression: the decode error did not say which of the style files it was in
        (style_dir / "06-table.css").write_bytes(b"/* \xe9t\xe9 */\n")
        with pytest.raises(UnicodeDecodeError) as error:
            GroupPage("index.html", "Top", ["Name"]).write()
        assert str(error.value) == ("'utf-8' codec can't decode byte 0xe9 in position 3: "
                                    f"invalid continuation byte in {style_dir / '06-table.css'}")


class TestBackground:
    def test_no_image_no_style(self, site):
        GroupPage("index.html", "Top", ["Name"], theme=Theme(banner="Lab")).write()
        assert '<header class="title"><div class="page-width">' in body("index.html")
        assert '<div class="top-banner"><div class="page-width">' in body("index.html")

    def test_title_image_relative_to_each_page(self, site):
        theme = Theme(title_image="art/wave.svg")
        top = GroupPage("index.html", "Top", ["Name"], theme=theme)
        GroupPage("runs/a/index.html", "A", ["Name"], parent=top, theme=theme).write()
        top.write()
        shade = "linear-gradient(rgb(8 12 24 / 0.62), rgb(8 12 24 / 0.62))"
        assert tree("index.html").find("header").attrs["style"] == (
            f'background-image: {shade}, url("art/wave.svg")')
        assert tree("runs/a/index.html").find("header").attrs["style"] == (
            f'background-image: {shade}, url("../../art/wave.svg")')

    def test_banner_image_behind_both_banners(self, site):
        theme = Theme(banner="Lab", bottom_banner="Contact", banner_image="img/b.png")
        GroupPage("site/index.html", "Top", ["Name"], theme=theme).write()
        page = tree("site/index.html")
        for cls in ("top-banner", "bottom-banner"):
            assert page.find("div", cls).attrs["style"].endswith(', url("../img/b.png")')

    def test_quote_in_image_path_cannot_end_the_css_string(self, site):
        # Regression: a " in the path, escaped only for HTML, closed the url("...") string.
        GroupPage("index.html", "Top", ["Name"], theme=Theme(title_image='a"b\\c.png')).write()
        assert 'url(&quot;a%22b%5Cc.png&quot;)"' in body("index.html")


class TestWrite:
    def test_page_skeleton(self, site):
        GroupPage("index.html", "Runs", ["Name"]).write()
        text = Path("index.html").read_text(encoding="utf-8")
        assert text.startswith('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                               '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                               '<title>Runs</title>\n<style>\n')
        assert body("index.html") == (
            '<body>\n<a class="skip-link" href="#content">Skip to content</a>\n\n\n'
            '<header class="title"><div class="page-width"><h1>Runs</h1></div></header>\n'
            '<main class="page-width" id="content">\n'
            '<div class="table"><table><thead><tr><th scope="col">Name</th></tr></thead><tbody></tbody></table></div>\n'
            '</main>\n\n</body>\n</html>\n')

    def test_title_is_escaped_in_title_and_heading(self, site):
        GroupPage("index.html", "A<B> & C", ["Name"]).write()
        text = Path("index.html").read_text(encoding="utf-8")
        assert "<title>A&lt;B&gt; &amp; C</title>" in text
        assert "<h1>A&lt;B&gt; &amp; C</h1>" in text

    def test_banner_links_to_the_top_page(self, site):
        theme = Theme(banner="Lab <1>")
        top = GroupPage("index.html", "Top", ["Name"], theme=theme)
        GroupPage("x/y/index.html", "Y", ["Name"], parent=top, theme=theme).write()
        assert ('<div class="top-banner"><div class="page-width"><a href="../../index.html">Lab &lt;1&gt;</a></div></div>'
                in body("x/y/index.html"))

    def test_banner_on_the_top_page_links_to_itself(self, site):
        GroupPage("site/index.html", "Top", ["Name"], theme=Theme(banner="Lab")).write()
        assert '<a href="index.html">Lab</a>' in body("site/index.html")

    def test_header_text_under_the_title(self, site):
        GroupPage("index.html", "Top", ["Name"], header="Tank B\nDepth 0.8 m").write()
        assert "<h1>Top</h1><p>Tank B<br>Depth 0.8 m</p></div></header>" in body("index.html")

    def test_footer_and_bottom_banner(self, site):
        theme = Theme(bottom_banner="Lab\nInternal")
        GroupPage("index.html", "Top", ["Name"], footer="Built <today>", theme=theme).write()
        assert body("index.html").endswith(
            '</main>\n<footer class="footer"><div class="page-width">Built &lt;today&gt;</div></footer>\n'
            '<div class="bottom-banner"><div class="page-width">Lab<br>Internal</div></div>\n</body>\n</html>\n')

    def test_bottom_banner_without_footer(self, site):
        GroupPage("index.html", "Top", ["Name"], theme=Theme(bottom_banner="Lab")).write()
        assert "</main>\n\n" + '<div class="bottom-banner">' in body("index.html")
        assert "<footer" not in body("index.html")

    def test_makes_missing_directories(self, site):
        GroupPage("deep/er/still/index.html", "Top", ["Name"]).write()
        assert Path("deep/er/still/index.html").is_file()

    def test_overwrites_an_older_page(self, site):
        Path("index.html").write_text("old", encoding="utf-8")
        GroupPage("index.html", "New", ["Name"]).write()
        assert "<h1>New</h1>" in body("index.html")

    def test_written_as_utf8(self, site):
        GroupPage("index.html", "Wellen été 波", ["Name"]).write()
        assert "<h1>Wellen été 波</h1>".encode() in Path("index.html").read_bytes()

    def test_written_beside_the_page_then_renamed_over_it(self, site, monkeypatch):
        renames = []
        real_replace = pages.os.replace
        monkeypatch.setattr(pages.os, "replace", lambda source, target: renames.append(
            (str(source), str(target), Path(source).read_text(encoding="utf-8")[:15])) or real_replace(source, target))
        GroupPage("runs/index.html", "Top", ["Name"]).write()
        assert renames == [(f"runs/.index.html.{os.getpid()}.tmp", "runs/index.html", "<!doctype html>")]
        assert sorted(path.name for path in Path("runs").iterdir()) == ["index.html"]

    def test_a_failed_write_keeps_the_old_page_and_removes_the_partial_one(self, site, monkeypatch):
        Path("index.html").write_text("old", encoding="utf-8")

        def replace_fails(source, target):
            raise OSError(f"cannot rename {source}")

        monkeypatch.setattr(pages.os, "replace", replace_fails)
        with pytest.raises(OSError, match=rf"^cannot rename \.index\.html\.{os.getpid()}\.tmp$"):
            GroupPage("index.html", "New", ["Name"]).write()
        assert sorted(path.name for path in site.iterdir()) == ["index.html"]
        assert Path("index.html").read_text(encoding="utf-8") == "old"
    @pytest.mark.skipif(os.geteuid() == 0, reason="root writes into a read-only directory")
    def test_a_directory_that_cannot_be_written_raises_its_own_error(self, site):
        """The partial page that could not be made is not there to remove, and its absence
        must not hide the PermissionError behind a FileNotFoundError."""
        Path("site").mkdir(mode=0o555)
        with pytest.raises(PermissionError, match=rf"Permission denied: 'site/\.index\.html\.{os.getpid()}\.tmp'"):
            GroupPage("site/index.html", "Top", ["Name"]).write()
        assert list(Path("site").iterdir()) == []
    def test_page_is_well_formed(self, site):
        theme = Theme(banner="Lab", bottom_banner="b", banner_color="#123", title_image="t.png", banner_image="b.png")
        top = GroupPage("index.html", "Top", ["Name", "N", "Status"], header="h", footer="f", theme=theme)
        data = DataPage("a/index.html", "A", columns=2, column_titles=["x", "y"], parent=top, theme=theme)
        data.add_row([("p.png", "c\nd"), (None, "gone")], label="L", badge=Badge("b", "warn"))
        top.add_row(data, ["a", 1, Badge("ok", "ok")])
        top.write()
        data.write()
        for path in ("index.html", "a/index.html"):
            assert parse(Path(path).read_text(encoding="utf-8")).find("html").attrs == {"lang": "en"}


class TestBodyMarkup:
    """The body of small pages exactly, separators between elements included, which a parsed tree hides."""

    def test_group_page(self, site):
        top = GroupPage("index.html", "Top", ["Name"])
        middle = GroupPage("a/index.html", "A", ["Name"], parent=top)
        page = GroupPage("a/b/index.html", "B", ["Name", "N"], parent=middle)
        page.add_row("x.html", ["x", 1])
        page.add_row("y.html", ["y", 2])
        page.write()
        assert body("a/b/index.html") == (
            '<body>\n<a class="skip-link" href="#content">Skip to content</a>\n\n'
            '<nav class="breadcrumbs" aria-label="Breadcrumb"><ol class="page-width">'
            '<li><a href="../../index.html">Top</a></li><li><a href="../index.html">A</a></li>'
            '<li><span aria-current="page">B</span></li></ol></nav>\n'
            '<header class="title"><div class="page-width"><h1>B</h1></div></header>\n'
            '<main class="page-width" id="content">\n'
            '<div class="table"><table><thead><tr><th scope="col">Name</th><th scope="col" class="num">N</th></tr>'
            '</thead><tbody><tr><td><a href="x.html">x</a></td><td class="num">1</td></tr>'
            '<tr><td><a href="y.html">y</a></td><td class="num">2</td></tr></tbody></table></div>\n'
            '</main>\n\n</body>\n</html>\n')

    def test_data_page(self, site):
        page = DataPage("d.html", "D", columns=2, column_titles=["p", "q"], header="h", footer="f")
        page.add_row([("1.png", "one"), ("2.png", "two")])
        page.add_row([("3.png", "three"), (None, "four")])
        page.write()
        columns = 'style="grid-template-columns: repeat(2, minmax(0, 1fr))"'
        assert body("d.html") == (
            '<body>\n<a class="skip-link" href="#content">Skip to content</a>\n\n\n'
            '<header class="title"><div class="page-width"><h1>D</h1><p>h</p></div></header>\n'
            '<main class="page-width" id="content">\n<div class="image-grid">\n'
            f'<div class="column-titles" aria-hidden="true" {columns}><div>p</div><div>q</div></div>\n'
            f'<section class="image-row"><div class="image-strip" {columns}>'
            '<figure><a href="1.png"><img src="1.png" alt="p, one" loading="lazy"></a><figcaption>one</figcaption>'
            '</figure><figure><a href="2.png"><img src="2.png" alt="q, two" loading="lazy"></a>'
            '<figcaption>two</figcaption></figure></div></section>\n'
            f'<section class="image-row"><div class="image-strip" {columns}>'
            '<figure><a href="3.png"><img src="3.png" alt="p, three" loading="lazy"></a>'
            '<figcaption>three</figcaption></figure><figure><div class="no-image" role="img" '
            'aria-label="No image: q, four">no image</div><figcaption>four</figcaption></figure></div></section>\n'
            '</div>\n</main>\n<footer class="footer"><div class="page-width">f</div></footer>\n</body>\n</html>\n')

    def test_data_page_without_header_or_footer(self, site):
        DataPage("d.html", "D", columns=1).write()
        page = tree("d.html")
        assert page.find("header").find_all("p") == []
        assert page.find_all("footer") == []
class TestGroupPage:
    def test_columns_are_copied(self, site):
        columns = ["Name", "Size"]
        page = GroupPage("index.html", "Top", columns)
        columns.append("Extra")
        assert page._columns == ["Name", "Size"]

    def test_row_with_wrong_value_count_is_refused(self, site):
        page = GroupPage("index.html", "Top", ["Name", "Size", "Status"])
        with pytest.raises(ValueError) as error:
            page.add_row("a.html", ["a", 1])
        assert str(error.value) == "row has 2 values, table has 3 columns"
        assert page._rows == []

    def test_columns_given_as_a_string_are_refused(self):
        # Regression: columns="Run" made three columns R, u and n.
        with pytest.raises(ValueError) as error:
            GroupPage("index.html", "Top", "Run")
        assert str(error.value) == "columns 'Run' is a string, not a list of column names"

    def test_values_given_as_a_string_are_refused(self, site):
        # Regression: add_row(link, "abc") on three columns wrote the cells a, b and c.
        page = GroupPage("index.html", "Top", ["A", "B", "C"])
        with pytest.raises(ValueError) as error:
            page.add_row("a.html", "abc")
        assert str(error.value) == "values 'abc' is a string, not a list of values"
        assert page._rows == []

    def test_empty_link_is_refused(self, site):
        # Regression: href="" opened the page itself.
        page = GroupPage("index.html", "Top", ["Name"])
        with pytest.raises(ValueError) as error:
            page.add_row("", ["a"])
        assert str(error.value) == "row link is empty"
        assert page._rows == []

    @pytest.mark.parametrize("first", ["", " ", None])
    def test_first_value_showing_as_empty_is_refused(self, site, first):
        # Regression: an empty first cell left the row's only link with nothing to click.
        page = GroupPage("index.html", "Top", ["Name", "Size"])
        with pytest.raises(ValueError) as error:
            page.add_row("a.html", [first, 1])
        assert str(error.value) == f"first value {first!r} shows as empty text, leaving the row no link"
        assert page._rows == []

    def test_link_to_a_page_is_relative(self, site):
        top = GroupPage("site/index.html", "Top", ["Name"])
        top.add_row(DataPage("site/runs/r1/index.html", "r1", columns=1), ["r1"])
        assert top._rows == [("runs/r1/index.html", ["r1"])]

    def test_link_as_text_is_kept_as_given(self, site):
        top = GroupPage("site/index.html", "Top", ["Name"])
        top.add_row("../elsewhere/page.html", ["x"])
        assert top._rows == [("../elsewhere/page.html", ["x"])]

    def test_link_as_path_object(self, site):
        # Regression: a Path link reached html.escape at write and raised AttributeError.
        top = GroupPage("index.html", "Top", ["Name"])
        top.add_row(Path("runs") / "r 1.html", ["r1"])
        top.write()
        assert '<td><a href="runs/r%201.html">r1</a></td>' in body("index.html")

    def test_table_without_columns_is_refused(self):
        # Regression: a table with no columns failed at write, unpacking an empty row.
        with pytest.raises(ValueError) as error:
            GroupPage("index.html", "Top", [])
        assert str(error.value) == "a table needs at least one column"

    def test_values_are_copied(self, site):
        top = GroupPage("index.html", "Top", ["Name"])
        values = ["a"]
        top.add_row("a.html", values)
        values[0] = "changed"
        assert top._rows == [("a.html", ["a"])]

    def test_rows_link_from_the_first_cell(self, site):
        page = GroupPage("index.html", "Top", ["Name", "Note"])
        page.add_row("a&b.html", ["<a>", "n & m"])
        page.write()
        assert ('<tbody><tr><td><a href="a%26b.html">&lt;a&gt;</a></td><td>n &amp; m</td></tr></tbody>'
                in body("index.html"))

    def test_badge_and_none_cells(self, site):
        page = GroupPage("index.html", "Top", ["Name", "Status", "Note"])
        page.add_row("a.html", ["a", Badge("done", "ok"), None])
        page.write()
        assert '<td><span class="badge badge-ok">done</span></td><td></td></tr>' in body("index.html")

    def table_alignment(self, columns, rows):
        page = GroupPage("index.html", "Top", columns)
        for values in rows:
            page.add_row("a.html", values)
        page.write()
        page = tree("index.html")
        head = ["num" in th.classes for th in page.find_all("th")]
        cells = [["num" in td.classes for td in tr.find_all("td")] for tr in page.find("tbody").find_all("tr")]
        return head, cells

    def test_numeric_columns_align_right_in_head_and_body(self, site):
        head, cells = self.table_alignment(["Name", "Count", "Mean", "Note"], [["a", 3, 1.5, "x"], ["b", -4, 2, "y"]])
        assert head == [False, True, True, False]
        assert cells == [[False, True, True, False], [False, True, True, False]]

    def test_none_does_not_stop_a_column_being_numeric(self, site):
        head, _ = self.table_alignment(["Name", "Count"], [["a", None], ["b", 7]])
        assert head == [False, True]

    def test_column_of_only_none_is_not_numeric(self, site):
        head, _ = self.table_alignment(["Name", "Count"], [["a", None], ["b", None]])
        assert head == [False, False]

    def test_one_text_value_makes_a_column_text(self, site):
        head, _ = self.table_alignment(["Name", "Count"], [["a", 1], ["b", "n/a"]])
        assert head == [False, False]

    def test_bools_are_not_numbers(self, site):
        head, _ = self.table_alignment(["Name", "Done"], [["a", True], ["b", False]])
        assert head == [False, False]

    def test_first_column_is_never_numeric(self, site):
        head, cells = self.table_alignment(["Run", "N"], [[1, 2], [3, 4]])
        assert head == [False, True]
        assert cells == [[False, True], [False, True]]

    def test_empty_table_has_no_numeric_column(self, site):
        head, cells = self.table_alignment(["Name", "Count"], [])
        assert (head, cells) == ([False, False], [])

    def test_header_cells_are_escaped(self, site):
        GroupPage("index.html", "Top", ["Size <cm>"]).write()
        assert '<th scope="col">Size &lt;cm&gt;</th>' in body("index.html")


class TestDataPageValidation:
    @pytest.mark.parametrize("columns", [0, -1])
    def test_needs_a_column(self, columns):
        with pytest.raises(ValueError) as error:
            DataPage("p.html", "P", columns=columns)
        assert str(error.value) == f"a grid needs at least one column, got {columns}"

    def test_column_titles_must_match_columns(self):
        with pytest.raises(ValueError) as error:
            DataPage("p.html", "P", columns=3, column_titles=["a", "b"])
        assert str(error.value) == "2 column titles for 3 columns"

    @pytest.mark.parametrize("width", [0, -5])
    def test_image_width_must_be_positive(self, width):
        with pytest.raises(ValueError) as error:
            DataPage("p.html", "P", columns=1, max_image_width_px=width)
        assert str(error.value) == f"max_image_width_px must be positive, got {width}"

    def test_one_column_and_one_pixel_are_allowed(self):
        page = DataPage("p.html", "P", columns=1, max_image_width_px=1)
        assert (page._columns, page._max_image_width_px, page._rows) == (1, 1, [])

    def test_row_with_wrong_image_count_is_refused(self):
        page = DataPage("p.html", "P", columns=2)
        with pytest.raises(ValueError) as error:
            page.add_row([("a.png", "a")])
        assert str(error.value) == "row has 1 images, grid has 2 columns"
        assert page._rows == []

    def test_badge_that_is_not_a_badge_is_refused(self):
        # Regression: a str badge was taken and write raised AttributeError naming no row.
        page = DataPage("p.html", "P", columns=1)
        with pytest.raises(TypeError) as error:
            page.add_row([("a.png", "a")], badge="1 missing")
        assert str(error.value) == "badge '1 missing' is not a Badge"
        assert page._rows == []

    def test_add_row_keeps_label_badge_and_a_copy_of_images(self):
        page = DataPage("p.html", "P", columns=1)
        images = [("a.png", "a")]
        badge = Badge("x")
        page.add_row(images, label="L", badge=badge)
        images.append(("b.png", "b"))
        assert page._rows == [("L", badge, [("a.png", "a")])]

    @pytest.mark.parametrize("images, item", [
        (["elevation.png", "probe.png"], "'elevation.png'"), (["ab", "cd"], "'ab'"), ([("a.png",), ("b.png", "b")], "('a.png',)"),
    ])
    def test_row_items_must_be_image_text_pairs(self, images, item):
        # Regression: bare paths failed only at write, and a two-letter path was split into image and text
        page = DataPage("p.html", "P", columns=2)
        with pytest.raises(ValueError) as error:
            page.add_row(images)
        assert str(error.value) == f"row item {item} is not an (image, text) pair"
        assert page._rows == []

    def test_a_pair_may_be_a_list(self):
        page = DataPage("p.html", "P", columns=1)
        page.add_row([["a.png", "a"]])
        assert page._rows == [("", None, [["a.png", "a"]])]


class TestDataPageWrite:
    def grid(self, path="p.html"):
        return tree(path).find("div", "image-grid")

    def test_none_text_shows_as_no_text(self, site):
        # Regression: a None text showed as the word None in the caption and the alt text.
        page = DataPage("p.html", "P", columns=1, column_titles=["Probe"])
        page.add_row([("a.png", None)])
        page.write()
        figure = self.grid().find("figure")
        assert figure.find("figcaption").text() == ""
        assert figure.find("img").attrs["alt"] == "Probe"

    def test_figure_links_the_image_with_alt_text_and_caption(self, site):
        page = DataPage("p.html", "P", columns=2, column_titles=["Elevation", "Probe"])
        page.add_row([("T0.8/e.png", "max 2 cm\nrms 1 cm"), ("T0.8/p.png", "")], label="T = 0.8 s")
        page.write()
        figures = self.grid().find_all("figure")
        assert len(figures) == 2
        assert '<figure><a href="T0.8/e.png"><img src="T0.8/e.png" alt="Elevation, T = 0.8 s, max 2 cm, rms 1 cm" ' \
               'loading="lazy"></a><figcaption>max 2 cm<br>rms 1 cm</figcaption></figure>' in body("p.html")
        assert figures[1].find("img").attrs["alt"] == "Probe, T = 0.8 s"

    def test_alt_text_without_titles_or_label_is_the_caption(self, site):
        page = DataPage("p.html", "P", columns=1)
        page.add_row([("a.png", "run 3")])
        page.write()
        assert self.grid().find("img").attrs["alt"] == "run 3"

    def test_alt_text_with_nothing_else_is_the_file_name(self, site):
        page = DataPage("p.html", "P", columns=2)
        page.add_row([(Path("T 1") / "e.png", ""), ("https://cdn.example/plots/f.svg", "")])
        page.write()
        assert [img.attrs["alt"] for img in self.grid().find_all("img")] == ["e.png", "f.svg"]

    def test_missing_image_with_nothing_else_is_labeled_no_image(self, site):
        page = DataPage("p.html", "P", columns=1)
        page.add_row([(None, "")])
        page.write()
        assert self.grid().find("div", "no-image").attrs["aria-label"] == "No image"

    def test_missing_image_is_a_marked_box(self, site):
        page = DataPage("p.html", "P", columns=2, column_titles=["A", "B"])
        page.add_row([("a.png", "ok"), (None, "probe offline")], label="Row 1")
        page.write()
        assert ('<figure><div class="no-image" role="img" aria-label="No image: B, Row 1, probe offline">no image</div>'
                '<figcaption>probe offline</figcaption></figure>' in body("p.html"))

    def test_image_path_is_escaped(self, site):
        page = DataPage("p.html", "P", columns=1)
        page.add_row([('a&"b.png', "<c>")])
        page.write()
        assert ('<a href="a%26%22b.png"><img src="a%26%22b.png" alt="&lt;c&gt;" loading="lazy"></a>'
                '<figcaption>&lt;c&gt;</figcaption>' in body("p.html"))

    def test_image_as_path_object(self, site):
        page = DataPage("p.html", "P", columns=1)
        page.add_row([(Path("T 1") / "e#1.png", "e")])
        page.write()
        assert '<a href="T%201/e%231.png"><img src="T%201/e%231.png"' in body("p.html")

    def test_column_count_sets_both_grids(self, site):
        page = DataPage("p.html", "P", columns=4, column_titles=["a", "b", "c", "d"])
        page.add_row([("1.png", "")] * 4)
        page.write()
        grid = self.grid()
        style = "grid-template-columns: repeat(4, minmax(0, 1fr))"
        assert grid.find("div", "column-titles").attrs == {"class": "column-titles", "aria-hidden": "true",
                                                           "style": style}
        assert grid.find("div", "image-strip").attrs["style"] == style

    def test_no_column_titles_no_title_row(self, site):
        page = DataPage("p.html", "P", columns=1)
        page.add_row([("1.png", "")])
        page.write()
        assert self.grid().find_all("div", "column-titles") == []

    def test_column_titles_changed_after_the_page_is_made_do_not_reach_it(self, site):
        # Regression: the page kept the caller's list, so a title appended later skipped the length check.
        titles = ["a"]
        page = DataPage("p.html", "P", columns=1, column_titles=titles)
        titles.append("b")
        page.write()
        assert [div.text() for div in self.grid().find("div", "column-titles").find_all("div")] == ["a"]
    def test_column_titles_escaped(self, site):
        DataPage("p.html", "P", columns=1, column_titles=["<x>"]).write()
        assert self.grid().find("div", "column-titles").text() == "<x>"
        assert "<div>&lt;x&gt;</div>" in body("p.html")

    def test_row_heading_holds_label_and_badge(self, site):
        page = DataPage("p.html", "P", columns=1)
        page.add_row([("1.png", "")], label="T < 1 s", badge=Badge("1 missing", "warn"))
        page.write()
        assert ('<section class="image-row"><h2>T &lt; 1 s<span class="badge badge-warn">1 missing</span></h2>'
                in body("p.html"))

    def test_row_heading_with_only_a_badge(self, site):
        page = DataPage("p.html", "P", columns=1)
        page.add_row([("1.png", "")], badge=Badge("new"))
        page.write()
        assert '<h2><span class="badge badge-info">new</span></h2>' in body("p.html")

    def test_row_without_label_or_badge_has_no_heading(self, site):
        page = DataPage("p.html", "P", columns=1)
        page.add_row([("1.png", "")])
        page.write()
        assert '<section class="image-row"><div class="image-strip"' in body("p.html")

    def test_one_section_per_row_in_order(self, site):
        page = DataPage("p.html", "P", columns=1)
        for label in ("first", "second", "third"):
            page.add_row([(f"{label}.png", "")], label=label)
        page.write()
        assert [h2.text() for h2 in self.grid().find_all("h2")] == ["first", "second", "third"]

    @pytest.mark.parametrize("columns, width, max_width", [(1, 300, 304), (3, 300, 908), (4, 1, 14)])
    def test_image_width_caps_the_grid(self, site, columns, width, max_width):
        DataPage("p.html", "P", columns=columns, max_image_width_px=width).write()
        assert self.grid().attrs["style"] == f"max-width: {max_width}px"

    def test_no_cap_no_width(self, site):
        DataPage("p.html", "P", columns=2).write()
        assert self.grid().attrs == {"class": "image-grid"}

    def test_custom_grid_style_class(self, site, style_dir):
        (style_dir / "08-image-grid-dense.css").write_text("", encoding="utf-8")
        DataPage("p.html", "P", columns=2, theme=Theme(styles={"image-grid": "dense"})).write()
        assert self.grid().classes == ["image-grid", "image-grid-dense"]
