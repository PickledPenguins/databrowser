# A badge given as plain text

Level: failure. A row's badge must be a `Badge`, such as `Badge("1 missing", "warn")`; a string is caught when the row is added.

Input:    `python build.py`
Expected: stderr ends `TypeError: badge '1 missing' is not a Badge`; exit 1, no page written
