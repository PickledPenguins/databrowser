# Column titles that do not match the columns

Level: failure. column_titles needs one title per column.

Input:    `python build.py`
Expected: stderr ends `ValueError: 2 column titles for 3 columns`; exit 1, no page written
