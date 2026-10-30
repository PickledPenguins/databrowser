"""Faults from outside the code: a disk that fills mid-page, style files that change or break
between making a Theme and writing a page, and leftovers of a run that was killed."""

import os
import resource
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from databrowser import GroupPage, Theme

pytestmark = pytest.mark.long

ROOT = Path(__file__).resolve().parent.parent


def limit_file_size():
    """In the child: files may not grow past 4 KiB, and growing one fails the write with
    EFBIG instead of killing the process, as a full disk or quota fails it."""
    signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    resource.setrlimit(resource.RLIMIT_FSIZE, (4096, resource.getrlimit(resource.RLIMIT_FSIZE)[1]))


def test_a_write_cut_short_keeps_the_old_page(tmp_path):
    (tmp_path / "site").mkdir()
    (tmp_path / "site/index.html").write_text("old page", encoding="utf-8")
    script = textwrap.dedent("""
        from databrowser import GroupPage
        GroupPage("site/index.html", "Top", ["Name"]).write()
    """)
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, capture_output=True, text=True,
                            env=dict(os.environ, PYTHONPATH=str(ROOT / "src")), preexec_fn=limit_file_size)
    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr.splitlines()[-1] == "OSError: [Errno 27] File too large"
    assert sorted(path.name for path in (tmp_path / "site").iterdir()) == ["index.html"]
    assert (tmp_path / "site/index.html").read_text(encoding="utf-8") == "old page"


def test_a_partial_page_left_by_a_killed_run_is_written_over(site):
    """A run killed mid-write leaves its partial page behind. A later run with the same
    process id writes over it rather than failing."""
    Path(f".index.html.{os.getpid()}.tmp").write_text("partial", encoding="utf-8")
    GroupPage("index.html", "Top", ["Name"]).write()
    assert sorted(path.name for path in site.iterdir()) == ["index.html"]
    assert "<h1>Top</h1>" in Path("index.html").read_text(encoding="utf-8")


def test_a_custom_style_file_removed_after_the_theme_was_made(site, style_dir):
    (style_dir / "03-top-banner-lab.css").write_text(".top-banner-lab {}\n", encoding="utf-8")
    page = GroupPage("index.html", "Top", ["Name"], theme=Theme(banner="Lab", styles={"top-banner": "lab"}))
    (style_dir / "03-top-banner-lab.css").unlink()
    with pytest.raises(FileNotFoundError, match=rf"^no file named NN-top-banner-lab\.css in {style_dir}$"):
        page.write()
    assert list(site.glob("*.html")) == []


def test_a_style_file_that_is_not_utf8(site, style_dir):
    (style_dir / "06-table.css").write_bytes(b"/* \xe9t\xe9 in Latin-1 */\n")
    with pytest.raises(UnicodeDecodeError, match="^'utf-8' codec can't decode byte 0xe9 in position 3"):
        GroupPage("index.html", "Top", ["Name"]).write()
    assert list(site.glob("*.html")) == []


def test_a_style_file_edited_between_two_pages_shows_in_the_second(site, style_dir):
    GroupPage("a.html", "A", ["Name"]).write()
    (style_dir / "06-table.css").write_text("/* edited */\n", encoding="utf-8")
    GroupPage("b.html", "B", ["Name"]).write()
    assert "/* edited */" not in Path("a.html").read_text(encoding="utf-8")
    assert "/* edited */\n" in Path("b.html").read_text(encoding="utf-8")
