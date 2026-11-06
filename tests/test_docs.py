"""The documents against the code, both ways: every public name, parameter, style part, style
file and error message is in docs/interfaces.md, the README's examples print what it shows,
and every link, anchor and cross-reference resolves. Everything checked is read from the code
when the test runs, so a new parameter or message without its documentation fails here."""

import ast
import dataclasses
import inspect
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import databrowser
from databrowser import pages

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
INTERFACES = ROOT / "docs/interfaces.md"
DOCS = [README, *sorted((ROOT / "docs").glob("*.md"))]
README_MAX_LINES = 200


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """The body of the section with this heading, up to the next heading of the same or a higher level."""
    match = re.search(rf"^(#+) {re.escape(heading)}\n", text, re.M)
    assert match, f"no section {heading!r}"
    body = text[match.end():]
    end = re.search(rf"^#{{1,{len(match.group(1))}}} ", body, re.M)
    return body[:end.start()] if end else body


def code_spans(text: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", text)


def code_blocks(text: str) -> list[tuple[str, str]]:
    """Each fenced block as (language, content), in order."""
    return re.findall(r"^```(\w*)\n(.*?)^```$", text, re.M | re.S)


def github_anchor(heading: str) -> str:
    """The anchor GitHub gives a heading: lowercase, markup and punctuation but - and _ dropped, spaces as -."""
    text = re.sub(r"[`*]", "", heading).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    result = set()
    in_code = False
    for line in read(path).splitlines():
        if line.startswith("```"):
            in_code = not in_code
        elif not in_code and (match := re.match(r"#+ (.+)", line)):
            anchor = github_anchor(match.group(1))
            count = seen.get(anchor, 0)
            seen[anchor] = count + 1
            result.add(anchor if count == 0 else f"{anchor}-{count}")
    return result


def prose(path: Path) -> str:
    """The document without its fenced code blocks."""
    return re.sub(r"^```.*?^```$", "", read(path), flags=re.M | re.S)


# The surface: public names, signatures, parts, files, messages.

def render_default(param: inspect.Parameter, cls) -> str:
    default = param.default
    if dataclasses.is_dataclass(cls):
        field = {f.name: f for f in dataclasses.fields(cls)}[param.name]
        if field.default_factory is not dataclasses.MISSING:
            default = field.default_factory()
    if isinstance(default, str):
        return f'"{default}"'
    if isinstance(default, pages.Theme):
        return "Theme()"
    return repr(default)


def rendered_signature(cls) -> str:
    params = []
    for param in inspect.signature(cls).parameters.values():
        if param.default is inspect.Parameter.empty:
            params.append(param.name)
        else:
            params.append(f"{param.name}={render_default(param, cls)}")
    return f"{cls.__name__}({', '.join(params)})"


PUBLIC_CLASSES = [getattr(databrowser, name) for name in databrowser.__all__ if inspect.isclass(getattr(databrowser, name))]


def test_every_export_has_a_section():
    headings = re.findall(r"^## (.+)$", read(INTERFACES), re.M)
    assert [name for name in databrowser.__all__ if name not in headings] == []


@pytest.mark.parametrize("cls", PUBLIC_CLASSES, ids=lambda cls: cls.__name__)
def test_signature_shown_as_the_code_has_it(cls):
    blocks = [content for language, content in code_blocks(section(read(INTERFACES), cls.__name__))
              if language == "python"]
    assert [re.sub(r"\s+", "", block) for block in blocks] == [re.sub(r"\s+", "", rendered_signature(cls))]


@pytest.mark.parametrize("cls", PUBLIC_CLASSES, ids=lambda cls: cls.__name__)
def test_every_parameter_and_method_described(cls):
    spans = set(code_spans(section(read(INTERFACES), cls.__name__)))
    names = list(inspect.signature(cls).parameters)
    names += [name for name, _ in inspect.getmembers(cls, inspect.isfunction) if not name.startswith("_")]
    assert [name for name in names if name not in spans and not any(span.startswith(f"{name}(") for span in spans)] == []


def test_style_parts_listed_in_order():
    listed = ", ".join(f"`{part}`" for part in pages._STYLE_PARTS)
    assert listed in " ".join(section(read(INTERFACES), "Style parts").split())


def test_badge_kinds_listed():
    spans = code_spans(section(read(INTERFACES), "Badge"))
    assert [kind for kind in pages._BADGE_KINDS if kind not in spans] == []


def test_every_style_file_named():
    spans = set(code_spans(section(read(INTERFACES), "Style files")))
    files = [file.name for file in sorted(pages._STYLE_DIR.glob("*.css"))]
    assert [name for name in files if name not in spans] == []


def raised_messages() -> list[tuple[int, list[str]]]:
    """The literal pieces of each message the package raises, by line: an f-string's text between
    its fields, so "row has {n} values" gives ["row has ", " values"]."""
    messages = []
    for path in sorted((ROOT / "src/databrowser").glob("*.py")):
        for node in ast.walk(ast.parse(read(path))):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and node.exc.args:
                message = node.exc.args[0]
                if isinstance(message, ast.Constant):
                    messages.append((node.lineno, [message.value]))
                elif isinstance(message, ast.JoinedStr):
                    pieces = [part.value for part in message.values if isinstance(part, ast.Constant)]
                    messages.append((node.lineno, [piece for piece in pieces if piece.strip()]))
    return messages


def test_the_package_raises_messages():
    """The scan below finds what it looks for, so its passing means something."""
    assert len(raised_messages()) >= 10


@pytest.mark.parametrize("line, pieces", raised_messages(), ids=lambda value: str(value) if isinstance(value, int) else "")
def test_every_error_message_quoted(line, pieces):
    """Each message in one code span of the Errors section, its literal pieces in order."""
    pattern = ".*".join(re.escape(piece.strip()) for piece in pieces)
    spans = code_spans(section(read(INTERFACES), "Errors"))
    assert any(re.search(pattern, span) for span in spans), f"pages.py:{line} {pieces} not quoted"


# The README: examples, index, size, version.

def example_runs() -> list[tuple[str, str, str]]:
    """Each python block, and each sh block followed by a text block, with the output shown."""
    blocks = code_blocks(read(README))
    runs = []
    for (language, content), (next_language, output) in zip(blocks, blocks[1:]):
        if language in ("python", "sh") and next_language == "text":
            runs.append((language, content, output))
    return runs


def test_readme_has_examples():
    assert [language for language, _, _ in example_runs()] == ["python", "sh"]


@pytest.mark.parametrize("language, content, output", example_runs(), ids=["quick-start", "demo"])
def test_readme_example_prints_what_it_shows(tmp_path, language, content, output):
    """Run as a reader runs it: in a fresh directory holding the source and the examples, with
    python3 the interpreter running the tests."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").symlink_to(sys.executable)
    work = tmp_path / "work"
    shutil.copytree(ROOT / "examples", work / "examples")
    (work / "src").symlink_to(ROOT / "src")
    env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}", PYTHONPATH=str(ROOT / "src"))
    if language == "python":
        (work / "build.py").write_text(content, encoding="utf-8")
        command = ["python3", "build.py"]
    else:
        command = ["sh", "-c", content]
    result = subprocess.run(command, cwd=work, env=env, capture_output=True, text=True)
    assert (result.returncode, result.stderr, result.stdout) == (0, "", output)


def test_readme_size_capped():
    assert len(read(README).splitlines()) <= README_MAX_LINES


def test_readme_version_is_the_package_version():
    version = tomllib.loads(read(ROOT / "pyproject.toml"))["project"]["version"]
    assert re.search(r"^\*\*Version (\S+)\*\*$", read(README), re.M).group(1) == version


def test_every_doc_linked_from_the_readme():
    linked = set(re.findall(r"\]\((docs/[^)#]+)", read(README)))
    assert sorted(f"docs/{path.name}" for path in (ROOT / "docs").glob("*.md")) == sorted(linked)


def test_every_test_file_in_the_testing_doc():
    spans = set(code_spans(read(ROOT / "docs/testing.md")))
    files = [f"tests/{path.name}" for path in sorted((ROOT / "tests").glob("*.py")) if path.name != "conftest.py"]
    assert [name for name in files if name not in spans] == []


# Links and cross-references.

@pytest.mark.parametrize("doc", DOCS, ids=lambda path: path.name)
def test_internal_links_resolve(doc):
    dead = []
    for target in re.findall(r"\]\(([^)\s]+)\)", prose(doc)):
        if re.match(r"\w+://", target):
            continue
        file, _, anchor = target.partition("#")
        path = (doc.parent / file).resolve() if file else doc
        if not path.exists() or (anchor and anchor not in anchors(path)):
            dead.append(target)
    assert dead == []


@pytest.mark.parametrize("doc", DOCS, ids=lambda path: path.name)
def test_cross_references_match_their_table(doc):
    text = prose(doc)
    citations = re.findall(r"<sup>\[(\d+)\]\(([^)]+)\)</sup>", text)
    if not citations:
        assert "## References" not in text
        return
    first_seen: dict[int, str] = {}
    for number, target in citations:
        assert first_seen.setdefault(int(number), target) == target, f"{number} cites two places"
    assert list(first_seen) == list(range(1, len(first_seen) + 1)), "numbered out of order"
    assert len(set(first_seen.values())) == len(first_seen), "two numbers cite one place"
    last_heading = re.findall(r"^## (.+)$", text, re.M)[-1]
    assert last_heading == "References"
    rows = re.findall(r"^\| (\d+) \| \[[^\]]+\]\(([^)]+)\) \|", section(text, "References"), re.M)
    assert [(int(number), target) for number, target in rows] == list(first_seen.items())


# Figures the documents state.

def glob_counts() -> list[dict]:
    """The [tool.doc-counts] entries of pyproject.toml counted from files alone. Test counts
    need the suite collected, which a test inside it cannot do. The doc-counts tool checks those."""
    entries = tomllib.loads(read(ROOT / "pyproject.toml"))["tool"]["doc-counts"]["count"]
    return [entry for entry in entries if all("glob" in source for source in entry.get("sources", [entry.get("source", {})]))]


def test_some_figures_are_counted_from_files():
    assert glob_counts()


@pytest.mark.parametrize("entry", glob_counts(), ids=lambda entry: entry["file"])
def test_stated_file_counts_match(entry):
    match = re.search(entry["pattern"], read(ROOT / entry["file"]))
    assert match, f"{entry['file']}: {entry['pattern']} not found"
    sources = entry.get("sources", [entry.get("source")])
    assert [int(group.replace(",", "")) for group in match.groups()] == [len(list(ROOT.glob(source["glob"]))) for source in sources]
