# Interfaces

The whole public surface is four names imported from `databrowser`: `GroupPage`,
`DataPage`, `Theme` and `Badge`, with the parameters, methods and attributes below.
Everything else in `src/databrowser/pages.py` is private and may change. The version is in the README header;
until 1.0 any release may change the interface, and no old form is kept alongside a new one.

## Paths

Three kinds of path, read three ways:

- A page's own `path` is where `write` puts it, relative to the current directory.
- A path given as text to a page, a `GroupPage.add_row` link or a `DataPage.add_row` image,
  is written into the page as given, so it is relative to the page file, not to the
  current directory. An absolute path stays absolute.
- `Theme.banner_image` and `Theme.title_image` are relative to the current directory, as a
  page's path is. Each page links them by the right relative path from where it is, so one
  theme serves pages at every depth.

A page given as a link (`top.add_row(run, ...)`) is linked by the relative path between the
two pages. Every link and image source is URL-encoded, with `/` between its parts, so a file
name with `#`, `?`, `%`, a space or a quote opens the file it names.

A URL, text starting with a scheme and `//` such as `https://` or `file://`, is linked as
given: its `?`, `#`, `&` and `%` keep their meaning, and only characters a URL cannot hold,
such as a space or a quote, are encoded. Any other text with a colon, `c:/data` or
`sweep:3`, is a path.

## GroupPage

```python
GroupPage(path, title, columns, header="", footer="", parent=None, theme=Theme())
```

A page with a table, each row linking to another page or file.

- `path`: a `str` or `Path`, where the page is written.
- `title`: shown as the page heading and the browser tab title.
- `columns`: the column headings, at least one.
- `header`: text under the title. `footer`: text at the foot of the page. A newline in
  either starts a new line.
- `parent`: the `GroupPage` this page hangs under. A page with a parent shows a breadcrumb
  trail of links back up to the top page.
- `theme`: the `Theme` of the site.

`add_row(link, values)` adds a row. `link` is a page, or a path relative to this page.
`values` has one value per column: the first shows as the link, and a click anywhere on
the row opens it. A value may be a `Badge`; `None` shows as an empty cell; anything else
shows as its `str()`. The link may not be empty, nor may the first value show as empty
text (`""`, blanks or `None`), since the row would have no link to click. `columns` and
`values` are lists; a bare string is rejected rather than split into characters. A column
after the first whose values are all numbers (any `numbers.Number` but `bool`, `None`
aside) is aligned to the right.

`write()` writes the page. Rows show in the order they were added.

`path` and `theme`, on both page kinds, are where the page is written, as a `Path`, and its
theme: what a child page made from it is likely to want.

## DataPage

```python
DataPage(path, title, columns, header="", footer="", column_titles=None,
         max_image_width_px=None, parent=None, theme=Theme())
```

A page with a grid of images: a fixed number of columns, any number of rows, text under each
image. Each row is a strip of images almost touching; rows are set apart; images in a column
line up.

- `path`, `title`, `header`, `footer`, `parent`, `theme`: as for `GroupPage`.
- `columns`: images per row, at least 1.
- `column_titles`: one title per column, shown above the grid and kept in view while the
  page scrolls.
- `max_image_width_px`: caps each image's width and centers the grid. Without it the
  images share the page width.

`add_row(images, label="", badge=None)` adds a row. `images` is a list of
`(image path, text)` pairs, one per column. The image path is relative to this page; `None`
shows an empty box marked "no image" with the text under it. The text may hold newlines; a
`None` text shows as no text, in the caption and the alt text alike. `label` and `badge`
show above the row. `badge` is a `Badge` or `None`; anything else is rejected here. Each item
of `images` must be a pair, a tuple or a list of two; a bare path is rejected here.

`write()` writes the page. Each image links to its file and has alt text made of its column
title, row label and text, joined by commas; an image with none of the three takes its file
name, since an empty alt text would mark it decorative to a screen reader. Images load lazily
(`loading="lazy"`): the browser fetches one only as it scrolls near, so a page printed or
captured before scrolling may lack the images below the first screen.

## Theme

```python
Theme(banner="", bottom_banner="", banner_color=None, banner_image=None, title_image=None,
      styles={})
```

The look shared by every page of a site. It is frozen: give a page its own look with its own
theme, `dataclasses.replace(theme, styles={...})`.

- `banner`: text in a bar across the top of the page, linking to the top page of the site.
  Empty, no bar.
- `bottom_banner`: text in a matching bar across the bottom, below the footer. A newline
  starts a new line. Empty, no bar.
- `banner_color`: `#rgb` or `#rrggbb`, the color of both bars. Their text turns white or
  black, whichever contrasts more with it, at least 4.58:1 for any color. Without it the
  bars take `--banner-bg` from `01-colors.css`.
- `banner_image`: a picture behind both bars. `title_image`: a picture behind the page
  title. Both are darkened so the text on them stays readable, and the banner text is white
  over a picture whatever `banner_color` is.
- `styles`: custom styles for parts of the page, part to style name, such as
  `{"top-banner": "user-page"}`. See [Custom styles](#custom-styles). The theme keeps a
  read-only copy: changing it raises `TypeError`.

Every page made without a `theme` shares one default `Theme()`.

## Badge

```python
Badge(text, kind="info")
```

A short status shown as a colored pill with an icon, in a `GroupPage` cell or above a
`DataPage` row. `text` is what the pill says; `kind` is one of `ok`, `info`, `warn` or
`error`. The text and the icon carry the meaning; the color only reinforces it.

## Style parts

The parts of a page that can take a custom style, in page order: `top-banner`,
`breadcrumbs`, `title`, `table`, `image-grid`, `footer`, `bottom-banner`. Each is the class
of the part's outer element.

## Style files

The look of every page comes from the CSS files in
[src/databrowser/style/](../src/databrowser/style), each commented with the HTML it styles and its common edits. When a page is written, the default files are
read and copied into it in name order, so an edit shows in every page written after it and
in none written before.

| File | Styles |
|---|---|
| `01-colors.css` | every color the pages use, as named variables the other files read |
| `02-page.css` | the font, the page background, the width of the content |
| `03-top-banner.css` | the bar across the top |
| `04-breadcrumbs.css` | the trail of links back up to the top page |
| `05-title.css` | the band with the page title and header text |
| `06-table.css` | the table of a group page |
| `07-badges.css` | the status badges |
| `08-image-grid.css` | the rows of images of a data page |
| `09-footer.css` | the page's footer text |
| `10-bottom-banner.css` | the bar across the bottom |
| `11-print.css` | the page printed or saved as PDF |

### Custom styles

A custom style for one part is a file `NN-PART-NAME.css` in the same directory, where `PART`
is one of the [style parts](#style-parts), `NAME` the style's name and `NN` any number. It is copied only into
pages whose theme names it, `Theme(styles={"PART": "NAME"})`, after the default files, so its
rules override theirs. That part's element gets the class `PART-NAME` as well as `PART`.
`03-top-banner-user-page.css` is an example, used by the demo's `series_B` pages.

Any other `.css` file in the directory is a default file and is copied into every page.

## Writing a page

`write()` creates the page's directory and any missing parents, then writes the whole page,
UTF-8 whatever the locale, to a hidden file beside it, `.NAME.PID.tmp`, and renames that
over the page. A browser or web server reading the page during a rebuild sees the old page or
the new one, never part of one. If the write fails, the old page is left as it was and the
hidden file is removed; the error from the operating system names the hidden file. A process
killed during the write leaves the hidden file behind.

Pages are only ever written, never removed: a page a rebuild no longer writes stays where it
was. Nothing is copied: images and linked files stay where the caller put them.

The pages aim at WCAG 2.2 AA: text contrast of at least 4.5:1, a visible keyboard focus, a
skip link to the content, headings and landmarks a screen reader can move between, and no
meaning carried by color alone.

## Errors

Each is raised when the object is made or the row added, before anything is written, except
where noted.

| Message | Raised by |
|---|---|
| `ValueError: a table needs at least one column` | `GroupPage` with no columns |
| `TypeError: columns 'Run' is a string, not a list of column names` | `GroupPage` |
| `TypeError: values 'abc' is a string, not a list of values` | `GroupPage.add_row` |
| `ValueError: row has 2 values, table has 3 columns` | `GroupPage.add_row` |
| `ValueError: row link is empty` | `GroupPage.add_row` |
| `ValueError: first value '' shows as empty text, leaving the row no link` | `GroupPage.add_row` |
| `ValueError: a grid needs at least one column, got 0` | `DataPage` |
| `ValueError: 2 column titles for 3 columns` | `DataPage` |
| `ValueError: max_image_width_px must be positive, got 0` | `DataPage` |
| `ValueError: row has 2 images, grid has 3 columns` | `DataPage.add_row` |
| `ValueError: row item 'elevation.png' is not an (image, text) pair` | `DataPage.add_row` with an item that is not a pair |
| `TypeError: badge '1 missing' is not a Badge` | `DataPage.add_row` |
| `ValueError: banner_color must be #rgb or #rrggbb, got 'teal'` | `Theme` |
| `ValueError: no part 'header' to style, parts are top-banner, breadcrumbs, title, table, image-grid, footer, bottom-banner` | `Theme` with a part not among the [style parts](#style-parts) |
| `FileNotFoundError: no file named NN-top-banner-lab.css in <style directory>` | `Theme` naming a style with no file; `write` if the file went since |
| `FileNotFoundError: 2 files named NN-top-banner-lab.css in <style directory>` | the same, with two files for one style |
| `ValueError: badge kind 'warning' is not one of ok, info, warn, error` | `Badge` |
| `FileNotFoundError: no style files in <style directory>` | `write`, when the style directory is missing or holds no default file |
| `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 3: invalid continuation byte in <style file>` | `write`, for a style file that is not UTF-8 |

`write` also lets through what the operating system raises: `PermissionError`,
`NotADirectoryError` or `IsADirectoryError` for a path that cannot be written, and an
`OSError` such as `OSError: [Errno 27] File too large` for a full disk or quota.
