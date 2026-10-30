# A custom style with no CSS file

Level: failure. A custom style needs its file, NN-PART-NAME.css, in the style directory.

Input:    `python build.py`
Expected: stderr ends `FileNotFoundError: no file named NN-table-compact.css in <STYLE_DIR>`; exit 1, no page written
