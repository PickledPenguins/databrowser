# A page path that names a directory

Level: failure. The page path is the HTML file to write, not the directory it goes in.

Input:    `python build.py`
Expected: stderr ends `IsADirectoryError: [Errno 21] Is a directory: 'site/.runs.<PID>.tmp' -> 'site/runs'`,
<PID> being the process id: the page is written beside its path and renamed into place; exit 1, no page written
