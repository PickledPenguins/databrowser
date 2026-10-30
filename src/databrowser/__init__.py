"""Write static HTML pages for browsing data: group pages with a table of links, and data
pages with a grid of images, all sharing one Theme and one set of editable CSS files."""

from databrowser.pages import Badge, DataPage, GroupPage, Theme, copy_style

__all__ = ["Badge", "DataPage", "GroupPage", "Theme", "copy_style"]
