"""Pages as a browser draws them, against committed golden screenshots.

Each case in tests/visual/ is a build.py writing a small site. Each shot below opens one of
its pages in headless Firefox at a fixed window size and color scheme, and the screenshot
must equal the case's golden PNG pixel for pixel. Firefox runs with a fresh profile, a
software renderer and one device pixel per CSS pixel. The pages use the system's fonts, so
the goldens hold for this machine's fonts and Firefox: a change to either can fail every
shot, which is the cue to look at the diffs and, if only the rendering moved, update.

UPDATE_GOLDENS=1 rewrites the goldens of the shots run. Look at every changed image before
committing it. On a mismatch the actual, golden and diff images go to .build/visual/.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

Image = pytest.importorskip("PIL.Image")
ImageChops = pytest.importorskip("PIL.ImageChops")

pytestmark = [pytest.mark.long,
              pytest.mark.skipif(shutil.which("firefox") is None, reason="needs firefox for the screenshots")]

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
CASES = TESTS / "visual"
ARTIFACTS = ROOT / ".build" / "visual"
# Firefox preferences: pages follow the color scheme the system is said to use, which each
# shot sets, and everything else that could vary between runs is pinned.
PREFS = {
    "layout.css.prefers-color-scheme.content-override": "2",
    "layout.css.devPixelsPerPx": '"1.0"',
    "gfx.webrender.software": "true",
    "browser.startup.homepage_override.mstone": '"ignore"',
    "toolkit.telemetry.reportingpolicy.firstRun": "false",
    "datareporting.policy.dataSubmissionEnabled": "false",
    "general.smoothScroll": "false",
    "ui.prefersReducedMotion": "1",
}
SHOTS = [
    # Each shot: the case, its page, the window width and height, the color scheme.
    ("group-page", "site/series_A/index.html", 1280, 860, "light"),
    ("group-page", "site/series_A/index.html", 1280, 860, "dark"),
    ("group-page", "site/series_A/index.html", 420, 1200, "light"),
    ("data-page", "site/sweep_03/index.html", 1280, 980, "light"),
    ("data-page", "site/sweep_03/index.html", 1280, 980, "dark"),
    ("custom-style", "site/index.html", 1280, 520, "light"),
    ("custom-style", "site/users/ana/index.html", 1280, 520, "light"),
]


def shot_id(shot) -> str:
    case, page, width, _height, scheme = shot
    return f"{case}-{Path(page).parent.name}-{width}-{scheme}"


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> dict[str, Path]:
    """Each case's site, written once for all its shots, with lazy image loading turned off:
    a headless screenshot is taken before lazy images load."""
    sites = {}
    for case in sorted({shot[0] for shot in SHOTS}):
        work = tmp_path_factory.mktemp(case)
        shutil.copy(CASES / "svg.py", work)
        shutil.copy(CASES / case / "build.py", work)
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "build.py"], cwd=work, env=env, capture_output=True, text=True,
                                check=False)
        assert (result.returncode, result.stderr) == (0, "")
        for page in work.rglob("*.html"):
            page.write_text(page.read_text(encoding="utf-8").replace(' loading="lazy"', ""), encoding="utf-8")
        sites[case] = work
    return sites


def screenshot(page: Path, width: int, height: int, scheme: str, profile: Path, out: Path) -> None:
    profile.mkdir()
    prefs = dict(PREFS, **{"ui.systemUsesDarkTheme": "1" if scheme == "dark" else "0"})
    (profile / "user.js").write_text("".join(f'user_pref("{key}", {value});\n' for key, value in prefs.items()))
    result = subprocess.run(["firefox", "--headless", "--no-remote", "--profile", str(profile),
                             f"--window-size={width},{height}", "--screenshot", str(out), page.as_uri()],
                            capture_output=True, text=True, timeout=120, check=False)
    assert result.returncode == 0 and out.is_file(), result.stderr


@pytest.mark.parametrize("shot", SHOTS, ids=shot_id)
def test_page_looks_as_it_did(shot, built, tmp_path):
    case, page, width, height, scheme = shot
    actual_path = tmp_path / "actual.png"
    screenshot(built[case] / page, width, height, scheme, tmp_path / "profile", actual_path)
    golden_path = CASES / case / f"{shot_id(shot).removeprefix(case + '-')}.png"
    if os.environ.get("UPDATE_GOLDENS") == "1":
        shutil.copy(actual_path, golden_path)
    actual = Image.open(actual_path).convert("RGB")
    golden = Image.open(golden_path).convert("RGB")
    assert actual.size == golden.size == (width, height)
    diff = ImageChops.difference(actual, golden)
    box = diff.getbbox()
    if box is None:
        return
    changed = sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0))
    out = ARTIFACTS / shot_id(shot)
    out.mkdir(parents=True, exist_ok=True)
    actual.save(out / "actual.png")
    golden.save(out / "golden.png")
    diff.point(lambda level: 255 if level else 0).save(out / "diff.png")
    pytest.fail(f"{changed} pixels differ within {box}: {out}/actual.png, golden.png, diff.png")
