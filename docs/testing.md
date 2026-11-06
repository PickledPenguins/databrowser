# Testing

How the suite is split, how to run each part, and what it measured when it was written. The
runner is `tests/run-tests.sh`; everything it generates goes under `.build/`, except the
`mutants/` tree mutmut makes and cannot be told to put elsewhere.

## Suites

| Command | Runs | Tests | Time |
|---|---|---|---|
| `tests/run-tests.sh` | fast: unit, interface, documentation, smoke. Before a push | 284 | 2 s |
| `tests/run-tests.sh long` | long: catalogs, properties, faults, concurrency, scaling, visual, packaging. Before a release | 137 | 35 s |
| `tests/run-tests.sh all` | both | 421 | 36 s |
| `tests/run-tests.sh cov` | fast suite under coverage, failing under 100% | 284 | 2 s |
| `tests/run-tests.sh perf` | timing against this machine's baseline, then memory, in two processes | 5 | 6 s |
| `tests/run-tests.sh mutation` | every mutant of the package against the fast suite but the documentation test | 535 mutants | 1 min |

`PYTHON=/path/to/python` picks the interpreter. The fast suite needs pytest; the long suite
also hypothesis and Pillow, and Firefox for the visual tests, which are skipped without it;
`cov` needs coverage and `mutation` mutmut. The package itself needs none of them.

Times and every figure below were measured on 2026-11-06, on the commit that last changed
this paragraph, on an Intel Core i5-4260U at 1.4 GHz, 4 threads, 7 GB, Python 3.12.15.

## Where each test lives

| File | Covers |
|---|---|
| `tests/test_pages_unit.py` | every function and class of `src/databrowser/pages.py`, its branches and errors |
| `tests/test_interface.py` | the exports, signatures and style files callers rely on; the demo script; UTF-8 under an ASCII locale |
| `tests/test_examples.py` | the example catalog [tests/examples/](../tests/examples) and the failure catalog [tests/failures/](../tests/failures) |
| `tests/test_properties.py` | generated text, values, colors and paths against the rules every page keeps |
| `tests/test_faults.py` | a disk filling mid-page, style files changing or broken, leftovers of a killed run |
| `tests/test_concurrency.py` | processes writing one new tree at once, and a reader during rewrites |
| `tests/test_scaling.py` | time per row and per page as rows and depth grow |
| `tests/test_visual.py` | screenshots in headless Firefox against goldens in [tests/visual/](../tests/visual) |
| `tests/test_packaging.py` | the wheel holding the module and every style file |
| `tests/test_perf.py` | the timing and memory gates |
| `tests/test_docs.py` | the documents against the code: every public name, parameter and error message documented, the README's examples, links and cross-references |
| `tests/html_tree.py` | the element tree the tests read pages with, which fails on markup not well formed |

A unit test goes in the file of the module it covers, `tests/test_pages_unit.py` for
`pages.py`, in a class named for what it protects. Everything else goes in the file of its
subject in the table above, marked `long` unless it runs in well under a second. Each test
asserts the output, message or state it expects, never only that the code ran: break the
code and watch the test fail before trusting it. A bug fixed gets a test named for the bug.
## Catalogs

[tests/examples/](../tests/examples) holds 20 simple, 15 moderate and 5 complex cases,
[tests/failures/](../tests/failures) 16.
Each case is a directory with a README saying what it shows and a `build.py` run as a reader
runs a script: `python build.py` in a fresh copy of the directory. An example must write
exactly the pages in its `expected/` directory and leave no link pointing at a missing file.
A failure must exit 1 with its `expected-error.txt` as the last line of stderr and write no
page.

Expected pages hold the names of the style files a page inlines, not their text, so an edit
to the CSS changes no expected page. `tests/run-tests.sh examples-update` rewrites them;
review the diff before committing it.

Every run of the catalog runs each `build.py` under cProfile and prints the package's own
functions by cumulative time after the tests, with the whole profile in
`.build/profile/combined.pstats`. The pytest process itself is not profiled. When written,
the 40 builds spent 0.9 s in all, most of it in `_style_html` reading the style files
for each page.

## Coverage

The fast suite covers [src/databrowser/](../src/databrowser) completely: 223 of 223 statements and 70 of 70
branches. The floor in `tests/run-tests.sh` is 100%, line and branch together.

## Mutation

535 mutants: 524 killed, 1 timed out, 10 survived. None of the 10 is a missing test:

- 7 are equivalent: `encoding="UTF-8"` for `"utf-8"` twice; `c < 0.04045` for `<=`, which
  no 8-bit channel value meets exactly; `on_white > on_black` for `>=`, which differ only
  on a tie no `#rrggbb` color produces (all 16,777,216 checked); `X` added to the
  characters `_url` leaves unencoded in a URL, where letters are never encoded; and
  `rsplit("/")` or `rsplit("/", 2)` for `rsplit("/", 1)` in the file name an image's alt
  text falls back to, where `[-1]` takes the same last piece.
- 3 drop the `encoding="utf-8"` of the style read and the page write.
  `test_pages_are_utf8_under_an_ascii_locale` kills all three, but it runs the package in a
  subprocess, which mutmut cannot trace to the function, so it never runs that test on them.

## Performance

`tests/run-tests.sh perf-baseline` records the median of 9 runs of each workload in
`.build/perf-baseline.json`; `tests/run-tests.sh perf` fails a workload whose median is over
1.25 times its baseline. Medians across 10 separate runs of unchanged code spanned at most
3% from lowest to highest, so 1.25 is well clear of noise.

| Workload | Median |
|---|---|
| 200 small pages of a three-level site | 146 ms |
| one table of 20,000 rows | 174 ms |
| one grid of 2,000 rows of 4 images | 44 ms |

Memory peaks, traced in their own run: 1,103 bytes per table row and 4,411 per grid row,
mostly the finished page held whole before it is written. The ceilings are 1,400 and 5,500.

## Visual

Seven shots of three cases, at 1280 px in light and dark and at 420 px, compared pixel for
pixel. Firefox runs with a fresh profile, a software renderer and one device pixel per CSS
pixel. The pages use the system fonts, so the goldens hold for this machine's fonts and
Firefox 153.5.1esr: when either changes, look at the diffs in `.build/visual/` and update
with `tests/run-tests.sh visual-update` if only the rendering moved.
