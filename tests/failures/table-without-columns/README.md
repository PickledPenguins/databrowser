# A table with no columns

Level: failure. A group page needs at least one column, the one its rows link from.

Input:    `python build.py`
Expected: stderr ends `ValueError: a table needs at least one column`; exit 1, no page written
