# A 96-well plate: plates in a table, wells in a grid

Level: moderate. A data page per plate, a row per well column with four channels, wells
that failed to image shown as missing with a warn badge on their row, a width cap, and a
title image shared across pages.

Input:    `python build.py`
Expected: expected/site/index.html and plate pages; missing images as no-image boxes
