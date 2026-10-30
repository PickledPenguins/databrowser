# A file where the site directory should be

Level: failure. Every directory on the page's path must be a directory, not a file.

Input:    `python build.py`
Expected: stderr ends `NotADirectoryError: [Errno 20] Not a directory: 'site/runs'`; exit 1, no page written
