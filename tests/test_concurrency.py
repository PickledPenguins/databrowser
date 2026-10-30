"""Real processes writing pages at once: into one new directory tree, and over one page while
another process reads it, as a web server does while a site is rebuilt under it."""

import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from html_tree import parse

pytestmark = pytest.mark.long

ROOT = Path(__file__).resolve().parent.parent
WRITERS = 8


def start(script: str, cwd: Path, *args: str) -> subprocess.Popen:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    return subprocess.Popen([sys.executable, "-c", textwrap.dedent(script), *args], cwd=cwd, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def finish(process: subprocess.Popen) -> None:
    stdout, stderr = process.communicate(timeout=120)
    assert (process.returncode, stdout, stderr) == (0, "", "")


def test_writers_building_one_new_tree_at_once(tmp_path):
    """Each process makes the same missing parent directories while the others do."""
    script = """
        import sys
        from databrowser import DataPage, GroupPage
        writer = sys.argv[1]
        top = GroupPage("site/index.html", "Top", ["Name"])
        for run in range(20):
            page = DataPage(f"site/a/b/c/run-{run}/{writer}.html", f"{writer} {run}", columns=1, parent=top)
            page.add_row([(None, f"writer {writer} run {run}")])
            page.write()
    """
    processes = [start(script, tmp_path, str(writer)) for writer in range(WRITERS)]
    for process in processes:
        finish(process)
    for writer in range(WRITERS):
        for run in range(20):
            page = parse((tmp_path / f"site/a/b/c/run-{run}/{writer}.html").read_text(encoding="utf-8"))
            assert page.find("figcaption").text() == f"writer {writer} run {run}"
    assert sorted(path.name for path in (tmp_path / "site/a/b/c/run-0").iterdir()) == \
        [f"{writer}.html" for writer in range(WRITERS)]


def test_a_reader_never_sees_a_page_part_written(tmp_path):
    """A page rewritten over and over, with a large table, is read whole every time: never
    empty, never cut short. The writers write the same page, each its own rows."""
    script = """
        import sys
        from databrowser import GroupPage
        writer = sys.argv[1]
        for _ in range(400):
            page = GroupPage("site/index.html", "Top", ["Name", "Writer"])
            for row in range(2000):
                page.add_row(f"{row}.html", [f"row {row}", writer])
            page.write()
    """
    (tmp_path / "site").mkdir()
    writers = [start(script, tmp_path, str(writer)) for writer in range(2)]
    page = tmp_path / "site/index.html"
    reads = 0
    while any(writer.poll() is None for writer in writers):
        if page.exists():
            text = page.read_text(encoding="utf-8")
            rows = parse(text).find("tbody").find_all("tr")
            assert len(rows) == 2000
            assert len({row.find_all("td")[1].text() for row in rows}) == 1
            reads += 1
        time.sleep(0.001)
    for writer in writers:
        finish(writer)
    assert reads > 20
    assert [path.name for path in (tmp_path / "site").iterdir()] == ["index.html"]
