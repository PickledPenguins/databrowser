# Folders and files named with spaces, # and %

Level: moderate. Paths are written into the pages as URLs, so a space, a # or a % in a
folder or file name is percent-encoded and the link still opens the file.

Input:    `python build.py`
Expected: expected/site/... with hrefs like sample%20%233/ and 50%25.svg that resolve
