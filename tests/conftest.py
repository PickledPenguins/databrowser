"""Fixtures shared by the whole suite."""

import os
import pstats
import shutil
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / ".build" / "profile"
SESSION_START = time.time()
# Hypothesis has no setting for its example database other than this, read at import.
os.environ.setdefault("HYPOTHESIS_STORAGE_DIRECTORY", str(ROOT / ".build" / "hypothesis"))

from databrowser import pages  # noqa: E402


def pytest_terminal_summary(terminalreporter):
    """After a run of the example catalog, where the time went in the package's own functions,
    added up over every case's build.py, which test_examples runs under cProfile."""
    profiles = [path for path in PROFILE_DIR.glob("*.prof") if path.stat().st_mtime >= SESSION_START]
    if not profiles:
        return
    stats = pstats.Stats(*map(str, profiles))
    stats.dump_stats(PROFILE_DIR / "combined.pstats")
    own = sorted(((timing[3], timing[1], f"{Path(file).name}:{line} {name}")
                  for (file, line, name), timing in stats.stats.items() if f"{os.sep}databrowser{os.sep}" in file),
                 reverse=True)
    terminalreporter.write_sep("-", f"profile of {len(profiles)} example builds: databrowser by cumulative time")
    terminalreporter.write_line(f"{'cumulative s':>12} {'calls':>7}  function")
    for cumulative, calls, where in own[:12]:
        terminalreporter.write_line(f"{cumulative:12.4f} {calls:7d}  {where}")
    terminalreporter.write_line(f"total over the builds: {stats.total_tt:.3f} s. Each build.py is profiled in its "
                                "own process; the pytest process is not. Full profile: "
                                f"{(PROFILE_DIR / 'combined.pstats').relative_to(ROOT)}")


@pytest.fixture
def site(tmp_path, monkeypatch) -> Path:
    """An empty directory made the current one, since page paths are relative to it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def style_dir(tmp_path, monkeypatch) -> Path:
    """A copy of the style directory that the pages read instead, free to add files to."""
    copy = tmp_path / "style"
    shutil.copytree(pages.STYLE_DIR, copy)
    monkeypatch.setattr(pages, "STYLE_DIR", copy)
    return copy
