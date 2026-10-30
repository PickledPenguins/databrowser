# Image paths given without their text

Level: failure. A row is a list of (image, text) pairs; a bare list of paths is caught only when the page is written.

Input:    `python build.py`
Expected: stderr ends `ValueError: too many values to unpack (expected 2)`; exit 1, no page written
