"""The package as pip installs it: a wheel built from the project holds the module and every
style file, without which each page would be written with no styling at all."""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.long

ROOT = Path(__file__).resolve().parent.parent


def test_wheel_holds_the_module_and_every_style_file(tmp_path):
    project = tmp_path / "project"
    shutil.copytree(ROOT / "src", project / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(ROOT / "pyproject.toml", project)
    result = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-build-isolation", "--no-deps", "--no-index",
                             "-w", str(tmp_path / "dist"), str(project)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    [wheel] = (tmp_path / "dist").glob("databrowser-*.whl")
    names = {name for name in zipfile.ZipFile(wheel).namelist() if not name.startswith("databrowser-")}
    styles = {f"databrowser/style/{file.name}" for file in (ROOT / "src/databrowser/style").glob("*.css")}
    assert names == {"databrowser/__init__.py", "databrowser/pages.py"} | styles
