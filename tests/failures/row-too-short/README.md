# A table row with a value missing

Level: failure. A row must have one value per column; use None for an empty cell.

Input:    `python build.py`
Expected: stderr ends `ValueError: row has 2 values, table has 3 columns`; exit 1, no page written
