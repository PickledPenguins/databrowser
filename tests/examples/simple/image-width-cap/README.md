# Images no wider than a set width

Level: simple. max_image_width_px= caps each image's width and centers the grid, rather
than stretching small plots across a wide screen.

Input:    `python build.py`
Expected: expected/site/index.html with style="max-width: 646px" on the grid: two 320 px
          images, the 2 px gap between them and 2 px of padding each side
