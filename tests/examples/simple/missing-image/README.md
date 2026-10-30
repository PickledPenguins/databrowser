# An image that is not there

Level: simple. A None image path shows a box marked "no image" with the text still under
it, and the box carries the alt text a screen reader announces.

Input:    `python build.py`
Expected: expected/site/index.html with one no-image box, aria-label="No image: ..."
