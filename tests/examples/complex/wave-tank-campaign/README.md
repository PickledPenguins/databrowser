# A wave tank campaign, every feature at once

Level: complex. Three levels (campaign, series, sweep), a theme with banner color, banner
image, title image and bottom banner, one series in the user-page banner style, missing
probe images flagged by badges on their rows and rolled up into the series and campaign
tables, numeric columns with gaps, column titles and a width cap on every sweep page.

Input:    `python build.py`
Expected: expected/site/... 9 pages; the missing counts on the campaign page match the
          no-image boxes on the sweep pages; every link resolves
Why:      the badges, counts and links only agree if every level is built from the same
          data and every relative path is resolved per page.
