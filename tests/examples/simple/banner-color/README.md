# A banner in the lab's color

Level: simple. Theme(banner_color=...) colors both banners. A light color gets black text
and a dark color white text, chosen for contrast. With a banner_image too, the picture
under its dark shade hides the color, so the text is white whatever the color.

Input:    `python build.py`
Expected: expected/site/light.html with --banner-text: #000000, dark.html with #ffffff,
          light-under-image.html with #ffffff and the shaded picture on both banners
