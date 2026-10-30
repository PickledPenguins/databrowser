# A banner color given by name

Level: failure. banner_color takes #rgb or #rrggbb, not a CSS color name, so the text color can be worked out.

Input:    `python build.py`
Expected: stderr ends `ValueError: banner_color must be #rgb or #rrggbb, got 'navy'`; exit 1, no page written
