# A data page with no columns

Level: failure. A grid needs at least one column.

Input:    `python build.py`
Expected: stderr ends `ValueError: a grid needs at least one column, got 0`; exit 1, no page written
