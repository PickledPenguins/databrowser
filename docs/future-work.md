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
