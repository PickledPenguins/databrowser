# Future work

Known gaps that need a decision before they are built, and things decided against, with
the evidence. Nothing here is scheduled.

## Open

**F.3 `GroupPage.add_row` accepts an empty link and an empty first value.**
`add_row("", ["", 1])` writes a row whose link, `href=""`, opens the page itself, and whose
first cell, the only visible link, is empty, so the row can only be opened by clicking
elsewhere on it. Not fixed silently: it rejects input accepted today. The fix would raise
`ValueError` for an empty link and for a first value that shows as empty text. From the
code review of 2026-10-30.

**F.5 A table wider than a 420 px screen scrolls sideways with no visible cue.**
`06-table.css` gives the table its own horizontal scroll on a narrow screen; nothing shows
that more columns lie to the right. Not fixed silently: the cue (a shadow at the edge, a
note) is a design choice that changes every group page's look and the visual goldens. From
the testing review of 2026-10-30.

**F.7 A `None` text under an image shows as the word "None".**
`DataPage.add_row([("a.png", None)])` writes `<figcaption>None</figcaption>` and
`alt="None"`: `DataPage.write` (`src/databrowser/pages.py:395`, `:404`) passes the text
through `str()`. `GroupPage` shows a `None` value as an empty cell, so a caller passing
`captions.get(name)` to both page kinds gets an empty cell in one and the word in the other.
Not fixed silently: it changes what a page shows for input accepted today. The fix would
treat a `None` text as empty in the caption and the alt text, say so under DataPage in
[interfaces.md](interfaces.md), add a unit test, and add `st.none()` to the caption strategy
of `tests/test_properties.py`. From the code review of 2026-11-06.

**F.8 `GroupPage` splits a string given as `columns` or `values` into characters.**
`GroupPage(..., columns="Run")` makes three columns `R`, `u`, `n`, and `add_row(link, "abc")`
on a three-column table writes the cells `a`, `b`, `c` (`src/databrowser/pages.py:312`,
`:321`). Where the lengths differ, the error, "row has 6 values, table has 1 columns", names
the wrong cause. `DataPage.add_row` already rejects a bare string where a pair is meant. Not
fixed silently: it rejects input accepted today. The fix would raise `ValueError` for a `str`
given as `columns` or `values`, with a unit test and a case in `tests/failures/`. From the
code review of 2026-11-06.

**F.9 A string given as `badge` to `DataPage.add_row` fails only at `write()`.**
`add_row(images, badge="1 missing")` is accepted, and `write()` then raises
`AttributeError: 'str' object has no attribute '_html'` (`src/databrowser/pages.py:407`),
with nothing naming the row. `GroupPage` shows a string value as text, so the mistake is an
easy one. Not fixed silently: checking at `add_row`, or showing a string as an `info` badge,
are two shapes with different results for the caller. The fix would raise `TypeError` naming
the value in `add_row`, with a unit test and a case in `tests/failures/`. From the testing
review of 2026-11-06.

**F.10 No test checks the figures `docs/testing.md` states.**
`[tool.doc-counts]` in `pyproject.toml` describes the test and catalog counts the document
gives, but only the `doc-counts` tool reads it, outside the project, so the counts drifted
from 258 to 264 tests unnoticed. Not fixed silently: running it from `tests/test_docs.py`
means collecting the suite inside the suite, and running it from the runner makes the runner
depend on a tool the project does not ship. The fix would be one of the two, or a count check
of the catalogs alone in `tests/test_docs.py`, which needs no collection. From the
documentation review of 2026-11-06.

## Declined

**D.1 A style directory outside the package.** A second directory per theme,
`Theme.style_dir`, existed and was removed in 3dcb8d9 as one more thing to keep track of.
Custom styles live beside the defaults, named for their part
([interfaces.md](interfaces.md#custom-styles)).

**D.2 Only listed files as default styles.** A `.css` file in the style directory that is
not named for a part, such as `07-badges-big.css`, is copied into every page. That is the
intended way to add a default style: drop a file in. Documented under Custom styles in
[interfaces.md](interfaces.md#custom-styles), and relied on by
`test_pages_are_utf8_under_an_ascii_locale`.

**D.3 Breadcrumbs built in linear time.** Writing a page walks its parents and computes a
relative link to each, quadratic in depth: 0.7 ms at depth 10, 12.6 ms at depth 320. Real
sites are a few levels deep, and `tests/test_scaling.py` fails if depth 40 costs more than
its ratio over depth 10 allows.
