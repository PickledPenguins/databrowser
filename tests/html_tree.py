"""A small element tree of a written page, for tests: find elements by tag and class, read
their text and attributes. Parsing fails on a tag closed out of order or left open, so every
test that parses a page also checks that it is well formed."""

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

VOID_TAGS = {"meta", "br", "img", "link", "input", "hr"}


class Element:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]]):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children: list["Element | str"] = []

    @property
    def classes(self) -> list[str]:
        return (self.attrs.get("class") or "").split()

    def iter(self):
        """Every element below this one, in document order."""
        for child in self.children:
            if isinstance(child, Element):
                yield child
                yield from child.iter()

    def find_all(self, tag: str | None = None, cls: str | None = None) -> list["Element"]:
        return [element for element in self.iter()
                if (tag is None or element.tag == tag) and (cls is None or cls in element.classes)]

    def find(self, tag: str | None = None, cls: str | None = None) -> "Element":
        """The one element matching tag and class. Fails when there are none or several."""
        found = self.find_all(tag, cls)
        assert len(found) == 1, f"{len(found)} elements match tag={tag} class={cls}"
        return found[0]

    def text(self) -> str:
        """The text inside, with each <br> as a newline."""
        parts = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            elif child.tag == "br":
                parts.append("\n")
            else:
                parts.append(child.text())
        return "".join(parts)


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", [])
        self.open = [self.root]

    def handle_starttag(self, tag, attrs):
        element = Element(tag, attrs)
        self.open[-1].children.append(element)
        if tag not in VOID_TAGS:
            self.open.append(element)

    def handle_startendtag(self, tag, attrs):
        self.open[-1].children.append(Element(tag, attrs))

    def handle_endtag(self, tag):
        assert tag == self.open[-1].tag, f"</{tag}> closes <{self.open[-1].tag}>"
        self.open.pop()

    def handle_data(self, data):
        self.open[-1].children.append(data)


def links(root: Element) -> list[str]:
    """Every link a page makes: hrefs, image sources and url() in style attributes, in order."""
    found = []
    for element in root.iter():
        for name in ("href", "src"):
            if element.attrs.get(name) is not None:
                found.append(element.attrs[name])
        found += re.findall(r'url\("([^"]*)"\)', element.attrs.get("style") or "")
    return found


def broken_links(page: Path) -> list[str]:
    """The links of the page file that name no existing file, the in-page #content aside. A link
    is read the way a browser reads it: a URL, so '#' starts a fragment and %XX is a byte."""
    root = parse(page.read_text(encoding="utf-8"))
    return [link for link in links(root)
            if link != "#content" and not (page.parent / unquote(urlsplit(link).path)).exists()]


def parse(text: str) -> Element:
    """The document element of text, which must be well formed."""
    builder = _TreeBuilder()
    builder.feed(text)
    builder.close()
    assert len(builder.open) == 1, f"unclosed <{builder.open[-1].tag}>"
    return builder.root
