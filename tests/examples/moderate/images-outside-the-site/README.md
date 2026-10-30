# Images kept outside the site directory

Level: moderate. A data page links images where an analysis wrote them, outside the
site: image paths are relative to the page, so they start with ../.

Input:    `python build.py`
Expected: expected/site/report/index.html with src="../../results/..." links that resolve
