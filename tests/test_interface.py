"""The public contract: what the package exports, the signatures callers rely on, the style
files every part of a page needs, and the demo script running the way a reader runs it."""

import inspect
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import databrowser
from databrowser import STYLE_PARTS, Badge, DataPage, GroupPage, Theme, pages
from html_tree import broken_links, parse

ROOT = Path(__file__).resolve().parent.parent


def test_exports():
    assert databrowser.__all__ == ["STYLE_PARTS", "Badge", "DataPage", "GroupPage", "Theme"]


def test_style_parts():
    assert STYLE_PARTS == ("top-banner", "breadcrumbs", "title", "table", "image-grid", "footer", "bottom-banner")


@pytest.mark.parametrize("callable_, signature", [
    (GroupPage, "(path, title: str, columns: list[str], header: str = '', footer: str = '', "
                "parent: 'GroupPage | None' = None, theme: databrowser.pages.Theme = %s)"),
    (DataPage, "(path, title: str, columns: int, header: str = '', footer: str = '', "
               "column_titles: list[str] | None = None, max_image_width_px: int | None = None, "
               "parent: databrowser.pages.GroupPage | None = None, theme: databrowser.pages.Theme = %s)"),
    (GroupPage.add_row, "(self, link, values: list) -> None"),
    (DataPage.add_row, "(self, images: list[tuple[str | None, str]], label: str = '', "
                       "badge: databrowser.pages.Badge | None = None) -> None"),
    (Theme, "(banner: str = '', bottom_banner: str = '', banner_color: str | None = None, "
            "banner_image: str | None = None, title_image: str | None = None, "
            "styles: dict[str, str] = <factory>) -> None"),
    (Badge, "(text: str, kind: str = 'info') -> None"),
])
def test_signatures(callable_, signature):
    if "%s" in signature:
        signature %= repr(Theme())
    assert str(inspect.signature(callable_)) == signature


def test_every_page_writes_its_file_and_returns_nothing(site):
    assert GroupPage("g.html", "G", ["Name"]).write() is None
    assert DataPage("d.html", "D", columns=1).write() is None
    assert sorted(path.name for path in site.iterdir()) == ["d.html", "g.html"]


@pytest.mark.parametrize("part", STYLE_PARTS)
def test_each_part_has_one_default_style_file(part):
    files = [file.name for file in pages.STYLE_DIR.glob("*.css") if pages._file_part(file) == part]
    assert len(files) == 1, files


def test_each_part_is_the_class_of_an_element_on_a_page(site):
    theme = Theme(banner="Lab", bottom_banner="Contact")
    top = GroupPage("index.html", "Top", ["Name"], footer="f", theme=theme)
    data = DataPage("d/index.html", "D", columns=1, footer="f", parent=top, theme=theme)
    top.write()
    data.write()
    classes = set()
    for path in ("index.html", "d/index.html"):
        for element in parse(Path(path).read_text(encoding="utf-8")).iter():
            classes.update(element.classes)
    assert set(STYLE_PARTS) <= classes


def test_the_example_custom_style_is_shipped():
    assert (pages.STYLE_DIR / "03-top-banner-user-page.css").is_file()


def test_pages_are_utf8_under_an_ascii_locale(tmp_path):
    """A login node with LANG=C, and Python told not to switch to UTF-8 on its own: the style
    files are read and the page written as UTF-8 all the same."""
    shutil.copytree(pages.STYLE_DIR, tmp_path / "style")
    (tmp_path / "style/12-notes.css").write_text("/* Wellen été */\n", encoding="utf-8")
    script = ("from pathlib import Path\n"
              "from databrowser import GroupPage, pages\n"
              f"pages.STYLE_DIR = Path({str(tmp_path / 'style')!r})\n"
              f"GroupPage({str(tmp_path / 'index.html')!r}, 'Wellen \\u00e9t\\u00e9', ['Name']).write()\n")
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), LC_ALL="C", PYTHONCOERCECLOCALE="0", PYTHONUTF8="0")
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, cwd=ROOT)
    assert (result.returncode, result.stderr) == (0, "")
    page = (tmp_path / "index.html").read_bytes()
    assert "<h1>Wellen été</h1>".encode() in page
    assert "/* Wellen été */".encode() in page
def test_demo_site_writes_a_linked_site(tmp_path):
    """Smoke: the demo runs the way its docstring says and every link on every page resolves."""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    # Run from the project root, where a mutation run's mutated code finds its configuration.
    result = subprocess.run([sys.executable, str(ROOT / "examples/demo_site.py"), str(tmp_path / "out")],
                            capture_output=True, text=True, env=env, cwd=ROOT)
    assert (result.returncode, result.stderr) == (0, "")
    assert result.stdout == f"{tmp_path / 'out' / 'index.html'}\n"
    written = sorted(str(path.relative_to(tmp_path / "out")) for path in (tmp_path / "out").rglob("*.html"))
    assert written == ["index.html", "series_A/index.html", "series_A/sweep_01/index.html",
                       "series_A/sweep_02/index.html", "series_A/sweep_03/index.html", "series_B/index.html",
                       "series_B/sweep_01/index.html", "series_B/sweep_02/index.html", "series_B/sweep_03/index.html"]
    for page in written:
        assert broken_links(tmp_path / "out" / page) == [], page
