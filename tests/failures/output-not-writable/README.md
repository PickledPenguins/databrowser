# A site directory that cannot be written

Level: failure. The directory the page goes in must be writable.

Input:    `python build.py`
Expected: stderr ends `PermissionError: [Errno 13] Permission denied: 'site/.index.html.<PID>.tmp'`,
<PID> being the process id: the page is written beside its path and renamed into place; exit 1, no page written
