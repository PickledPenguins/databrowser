# A picture behind the title

Level: simple. Theme(title_image=...) puts a picture, darkened, behind the page title. The
path is relative to the current directory; the page links it relative to itself.

Input:    `python build.py`
Expected: expected/site/index.html with url("../art/aurora.svg") on the title header
