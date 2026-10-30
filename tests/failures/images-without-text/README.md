# Image paths given without their text

Level: failure. A row is a list of (image, text) pairs; a bare list of paths is caught when the row is added.

Input:    `python build.py`
Expected: stderr ends `ValueError: row item 'elevation.png' is not an (image, text) pair`; exit 1, no page written
