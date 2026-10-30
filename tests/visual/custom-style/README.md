# The shipped custom banner style beside a banner color

Level: moderate. The top page's banners take the Theme's banner_color, a light yellow, so
their text turns near black. Ana's page uses a copy of the Theme naming the shipped
03-top-banner-user-page.css: a taller, centered purple top banner, while its bottom banner
keeps the yellow.

Input:    `python build.py`, then site/index.html and site/users/ana/index.html in Firefox
Expected: site-1280-light.png, ana-1280-light.png
