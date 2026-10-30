# A survey with hundreds of rows

Level: complex. A top table of 120 stations with numbers, gaps and badges, three data
pages of 40 rows by 4 columns with scattered missing images and labels on every row,
breadcrumbs from each.

Input:    `python build.py`
Expected: expected/site/... 4 pages; numeric columns right-aligned despite gaps;
          missing images where the pattern puts them
Why:      the size real surveys have, so alignment, badges and missing images are
          checked across many rows, not one.
