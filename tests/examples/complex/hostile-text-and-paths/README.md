# Markup, quotes, newlines and URL characters everywhere at once

Level: complex. Every text a page shows (title, header, footer, banners, columns, cells,
badges, labels, captions, column titles) carries < > & and both quotes, some with
newlines; folder and image names carry spaces, #, %, ?, & and quotes; one theme picture
has a quote in its name.

Input:    `python build.py`
Expected: expected/site/...; every page well formed, every text escaped, every link
          percent-encoded and resolving
Why:      escaping for HTML and encoding for URLs are separate steps, and a path that
          reaches a page through a CSS url("...") needs both.
