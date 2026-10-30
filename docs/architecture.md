# Architecture

How databrowser is built and how to change it. What it does for a caller is in
[interfaces.md](interfaces.md).

## Shape

One module turns Python objects into HTML text. A caller makes pages, adds rows, and calls
`write`; each page renders its body, wraps it in the shared frame (banner, breadcrumbs,
title band, footer, bottom banner), copies the CSS files in, and writes the result as one
file. Nothing is kept between pages but the objects the caller holds, and nothing is read
but the style files.

## Layout

```text
src/databrowser/
  __init__.py      the public names, re-exported from pages.py
  pages.py         Theme, Badge, GroupPage, DataPage and the page frame they share
  style/           the CSS copied into every page, one file per part of the page
examples/
  demo_site.py     builds a three-level demo site with made-up plots
tests/             the suites, catalogs and goldens; see testing.md
docs/              these documents
.build/            everything generated: the demo site, coverage, profiles, perf baseline
```

| Name in pages.py | Responsibility |
|---|---|
| `Theme` | the look shared by a site's pages, checked when made |
| `Badge` | a status pill and its HTML |
| `_Page` | the frame every page shares, links between pages, and the write |
| `GroupPage` | the table of links |
| `DataPage` | the grid of images |
| `_url`, `_text_html`, `_cell_html` | text and paths made safe for HTML and URLs |
| `_luminance`, `_banner_text_color` | the banner text color with the higher contrast |
| `_file_part`, `_is_custom_style`, `_custom_style_file` | telling default style files from custom ones |

`__init__.py` depends on `pages.py`; `pages.py` depends on the standard library and the
files in `style/`. Nothing prints, parses arguments or exits: a caller's script owns all of
that, and errors propagate to it.

## Decisions

- **One self-contained file per page.** The CSS is copied into each page and there is no
  script, so a page opens from disk, from a copied or moved site, or from any server, and a
  page never mixes old and new styling. The cost is size: about 20 KB of CSS per page.
  Shared static files linked from each page were the earlier design, dropped with the
  widget and layout classes in 548e550.
- **Two page kinds, no layout system.** The library once placed widgets in layouts, the way a
  Qt window is built. Every site it was for is a tree of tables over grids of images, so the
  general system was replaced by `GroupPage` and `DataPage` (548e550).
- **Styling in editable CSS files, one per part.** Each opens with the HTML it styles and
  its common edits, so the look changes without touching Python (8e73766).
- **Custom styles live beside the defaults.** A second style directory per theme
  (`Theme.style_dir`) was removed in 3dcb8d9 as one more thing to keep track of. A custom
  style is a file named for its part, copied only into pages whose theme names it.<sup>[1](interfaces.md#custom-styles)</sup>
- **Images in style attributes, not CSS variables.** A `url()` in a variable resolves
  against the stylesheet, not the page, so banner and title images are set on the element
  where the relative path from the page holds (8e73766).
- **Written beside and renamed over.** A rebuild while someone browses must not show a
  truncated page; `tests/test_concurrency.py` caught that happening with a plain write.<sup>[2](interfaces.md#writing-a-page)</sup>
- **Standard library only.** The pages are built where the data is, often a cluster login
  node with only a system Python.

## Changing it

- A new page kind is a subclass of `_Page` with its own `write` that renders a body and
  calls `_write`, exported from `__init__.py`.
- A new part of the page that can take a custom style: add its name to `STYLE_PARTS`, give
  its outer element `self.theme.classes(part)` as its class, and add its default CSS file
  `NN-PART.css` in `style/`, opening with the HTML it styles.
- A behavior change updates `docs/interfaces.md` and, where the first ten minutes change,
  the README, in the same commit.

What stops a change:

| Gate | Fails when |
|---|---|
| `tests/run-tests.sh` | any fast test fails, the documentation test included |
| `tests/run-tests.sh cov` | line and branch coverage of the fast suite drops under 100% |
| `tests/run-tests.sh long` | an example or failure case, a property, a fault, a scaling ratio or a screenshot changes |
| `tests/run-tests.sh perf` | a workload is over 1.25 times its baseline, or memory over its ceiling |

The documentation test, `tests/test_docs.py`, fails when a public name, parameter, style
part, default style file or error message is missing from `docs/interfaces.md`, when the
README's examples print anything but what it shows, when a file in `docs/` is not linked
from the README, when an internal link or anchor is dead, when a cross-reference is out of
order, or when the README passes 200 lines or its version differs from `pyproject.toml`.
How to run and extend the suites is in [testing.md](testing.md).

Where a document uses something another document explains, it cites the section with a
superscript number linking to it, and ends with a References table, one row per number in
order of first citation. The documentation test checks both.

Commits are one change each, the subject an imperative sentence without a prefix:
`Fix links to odd paths, banner text contrast and half-written pages`.

## References

| # | Section | What it covers |
|---|---|---|
| 1 | [interfaces.md: Custom styles](interfaces.md#custom-styles) | naming and use of a custom style file |
| 2 | [interfaces.md: Writing a page](interfaces.md#writing-a-page) | what `write` does on disk |
