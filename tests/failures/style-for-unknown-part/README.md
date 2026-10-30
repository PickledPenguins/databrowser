# A custom style for a part that takes none

Level: failure. Only the style parts take a custom style; badges are not one.

Input:    `python build.py`
Expected: stderr ends `ValueError: no part 'badges' to style, parts are top-banner, breadcrumbs, title, table, image-grid, footer, bottom-banner`; exit 1, no page written
