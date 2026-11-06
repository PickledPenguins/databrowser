"""The example and failure catalogs, end to end: each case's build.py runs the way a reader runs
a script, with python in a fresh directory, and what it writes is compared with the case.

An example case must exit 0 with no output, write exactly the pages in its expected/ directory,
each equal to the expected one, and leave no link on any page pointing at a missing file. A
failure case must exit 1 with its expected-error.txt as the last line of stderr, writing no page.

Expected pages hold the names of the style files inlined into a page rather than their text,
so editing the CSS changes no expected page, while which files a page includes, and in what
order, is still compared. UPDATE_EXPECTED=1 rewrites expected/ from what the cases write: review
the diff before committing it. In an expected error, <STYLE_DIR> stands for the style
directory, <WORK> for the case's directory and <PID> for the process id in a partly written
page's name.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from databrowser import pages
from html_tree import broken_links

pytestmark = pytest.mark.long

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
LEVELS = ("simple", "moderate", "complex")
EXAMPLES = sorted(build.parent for build in (TESTS / "examples").glob("*/*/build.py"))
FAILURES = sorted(build.parent for build in (TESTS / "failures").glob("*/build.py"))
CASE_FILES = ("README.md", "expected", "expected-error.txt")
PROFILE_DIR = ROOT / ".build" / "profile"


def normalize(page: str) -> str:
    """page with the text of each inlined style file replaced by a comment naming the file."""
    match = re.search(r"<style>\n(.*?)</style>", page, re.DOTALL)
    css = match.group(1)
    contents = {file.name: file.read_text(encoding="utf-8") for file in sorted(pages._STYLE_DIR.glob("*.css"))}
    names, position = [], 0
    while position < len(css):
        name = next((name for name, text in contents.items() if css.startswith(text, position)), None)
        assert name is not None, f"inlined CSS matches no style file at {css[position:position + 60]!r}"
        names.append(f"/* {name} */\n")
        position += len(contents[name]) + 1
    return page[:match.start(1)] + "".join(names) + page[match.end(1):]


def run_case(case: Path, tmp_path: Path, *python_args: str) -> tuple[Path, subprocess.CompletedProcess]:
    """Copy the case's inputs to a fresh directory and run its build.py there."""
    work = tmp_path / case.name
    shutil.copytree(case, work, ignore=shutil.ignore_patterns(*CASE_FILES))
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, *python_args, "build.py"], cwd=work, env=env, capture_output=True,
                            text=True, timeout=120, check=False)
    return work, result


def written_pages(work: Path) -> dict[str, str]:
    return {path.relative_to(work).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(work.rglob("*.html"))}


def case_id(case: Path) -> str:
    return f"{case.parent.name}/{case.name}"


@pytest.mark.parametrize("case", EXAMPLES, ids=case_id)
def test_example(case, tmp_path):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    profile = PROFILE_DIR / f"{case.parent.name}-{case.name}.prof"
    work, result = run_case(case, tmp_path, "-m", "cProfile", "-o", str(profile))
    assert (result.returncode, result.stderr, result.stdout) == (0, "", "")
    written = {name: normalize(text) for name, text in written_pages(work).items()}
    expected_dir = case / "expected"
    if os.environ.get("UPDATE_EXPECTED") == "1":
        shutil.rmtree(expected_dir, ignore_errors=True)
        for name, text in written.items():
            (expected_dir / name).parent.mkdir(parents=True, exist_ok=True)
            (expected_dir / name).write_text(text, encoding="utf-8")
    expected = {path.relative_to(expected_dir).as_posix(): path.read_text(encoding="utf-8")
                for path in sorted(expected_dir.rglob("*.html"))}
    assert sorted(written) == sorted(expected)
    for name, text in expected.items():
        assert written[name] == text, name
    assert {name: broken_links(work / name) for name in written if broken_links(work / name)} == {}


@pytest.mark.parametrize("case", FAILURES, ids=case_id)
def test_failure(case, tmp_path):
    work, result = run_case(case, tmp_path)
    last_line = result.stderr.strip().splitlines()[-1]
    last_line = last_line.replace(str(pages._STYLE_DIR), "<STYLE_DIR>").replace(str(work), "<WORK>")
    last_line = re.sub(r"\.\d+\.tmp'", ".<PID>.tmp'", last_line)
    expected = (case / "expected-error.txt").read_text(encoding="utf-8").strip()
    assert (result.returncode, result.stdout, last_line) == (1, "", expected)
    assert written_pages(work) == {}
    assert list(work.rglob("*.tmp")) == []


@pytest.mark.parametrize("case", EXAMPLES + FAILURES, ids=case_id)
def test_case_has_a_readme_naming_its_level(case):
    readme = (case / "README.md").read_text(encoding="utf-8")
    level = case.parent.name if case.parent.name in LEVELS else "failure"
    assert readme.startswith("# ")
    assert f"Level: {level}." in readme


def test_catalog_sizes():
    counts = {level: sum(case.parent.name == level for case in EXAMPLES) for level in LEVELS}
    assert counts["simple"] >= 15 and counts["moderate"] >= 10 and counts["complex"] >= 4, counts
    assert len(FAILURES) >= 10
