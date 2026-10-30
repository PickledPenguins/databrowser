# A badge kind that does not exist

Level: failure. Badge kinds are ok, info, warn and error; warning is a common slip.

Input:    `python build.py`
Expected: stderr ends `ValueError: badge kind 'warning' is not one of ok, info, warn, error`; exit 1, no page written
