# Visual cases

Each directory holds a build.py writing a small site and the golden screenshots of its pages,
one PNG per shot listed in tests/test_visual.py: `PAGE-WIDTH-SCHEME.png`, the page's
directory name, the window width in pixels and the color scheme, light or dark. svg.py draws
the plots the cases show.

The goldens were taken with Firefox 153.5.1esr and this machine's system fonts. A different
Firefox or font set can change every shot: look at the diffs in .build/visual/ and, when
only the rendering moved, update.

    tests/run-tests.sh visual            compare every shot with its golden
    tests/run-tests.sh visual-update     rewrite the goldens; review each changed image
