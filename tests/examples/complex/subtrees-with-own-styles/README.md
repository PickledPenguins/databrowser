# Subtrees with their own looks, four levels deep, linking across

Level: complex. A site whose subtrees each carry a different theme copy (banner color,
custom banner style, no banner image), four parent levels, pages written leaves first,
rows linking sideways into another subtree, and images kept outside the site.

Input:    `python build.py`
Expected: expected/site/... each page with its own subtree's style files and colors,
          breadcrumbs four deep, every cross-subtree and outside link resolving
Why:      a page's look comes from its own theme while its links come from where the
          other pages are; the two must not leak into each other.
