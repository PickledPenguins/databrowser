# Building a site, then building it again changed

Level: complex. A site built once, then rebuilt from changed data: a run renamed, rows
added, the theme's banner color changed. Rewritten pages hold only the new version; a page
the second build no longer writes is left as it was, since pages are only ever written.

Input:    `python build.py`
Expected: expected/site/... the second build's pages, plus site/run-02/index.html from
          the first build, unlinked from the new top page
Why:      shows what a rebuild leaves behind, which a nightly job must clear itself.
