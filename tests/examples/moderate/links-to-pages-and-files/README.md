# Rows linking pages, plain files and paths

Level: moderate. One table whose rows link a page object, a file given as text and a
file given as a pathlib.Path; text and Path links are relative to the table's page.

Input:    `python build.py`
Expected: expected/site/index.html with hrefs to a page, a PDF and a CSV, all resolving
