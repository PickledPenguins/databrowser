# Column names given as a string

Level: failure. `columns` is a list of names; a bare string would be split into one column per character, so it is refused.

Input:    `python build.py`
Expected: stderr ends `ValueError: columns 'Run' is a string, not a list of column names`; exit 1, no page written
