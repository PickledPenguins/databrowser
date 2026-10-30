# databrowser

**Version 0.1**

A Python library that writes static HTML pages for browsing data: tables of links and grids
of images.

## What it does

A script that has produced data (runs of an experiment, sweeps of a simulation, plates of
a microscope) describes it as pages, and databrowser writes them as plain HTML files that
open from disk or from any web server. A group page holds a table whose rows link to other
pages; a data page holds a grid of images with text under each. Pages made with a parent
show a breadcrumb trail back to the top page, and a theme gives every page of a site the
same banners, colors and title image. The look comes from CSS files, one per part of the
page, which are copied into every page when it is written.

It is for people who already have the files and want a browsable index of them without
running a server. It does not read data, make plots, copy or resize images, search, or
serve pages: it writes the HTML that links to files the caller made. It needs nothing
outside the Python standard library.

## Install

Python 3.10 or later; no other packages. Either install it:

```sh
pip install /path/to/databrowser
```

or put its source directory on the module path without installing:

```sh
PYTHONPATH=/path/to/databrowser/src python3 build.py
```

## Quick start

Save this as `build.py` and run it with `python3 build.py`:

```python
from databrowser import Badge, DataPage, GroupPage, Theme

theme = Theme(banner="Wave Lab", banner_color="#0f3d3e")
top = GroupPage("site/index.html", "Campaign 2026", ["Run", "Images", "Status"], theme=theme)
run = DataPage("site/run_01/index.html", "run_01", columns=2, column_titles=["Elevation", "Spectrum"],
               parent=top, theme=theme)
run.add_row([("elevation.png", "max 3.1 cm"), ("spectrum.png", "peak 0.8 Hz")], label="T = 0.8 s")
top.add_row(run, ["run_01", 2, Badge("complete", "ok")])
for page in (run, top):
    page.write()
    print(page.path)
```

It prints the two pages it wrote:

```text
site/run_01/index.html
site/index.html
```

Open `site/index.html` in a browser. The image paths `elevation.png` and `spectrum.png` are
relative to the page that shows them, so they are looked for in `site/run_01/`.

A larger site, with made-up plots, a missing image, badges and a custom banner style:

```sh
PYTHONPATH=src python3 examples/demo_site.py
```

```text
.build/demo-site/index.html
```

## Documentation

- [docs/interfaces.md](docs/interfaces.md): every class and parameter, how paths are read,
  the style files and custom styles, what writing a page does, and every error message.
- [docs/architecture.md](docs/architecture.md): how the code is laid out, the decisions
  behind it, and how to change it.
- [docs/testing.md](docs/testing.md): the test suites, how to run them, and what they
  measured.
- [docs/future-work.md](docs/future-work.md): known gaps awaiting a decision, and what was
  decided against.
