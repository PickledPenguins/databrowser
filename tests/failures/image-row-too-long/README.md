# A row with more images than columns

Level: failure. Each row of a data page has exactly one (image, text) pair per column.

Input:    `python build.py`
Expected: stderr ends `ValueError: row has 4 images, grid has 3 columns`; exit 1, no page written
