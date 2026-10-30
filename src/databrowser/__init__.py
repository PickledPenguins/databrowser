"""Build static HTML pages for browsing data the way a Qt window is built: widgets (tables,
images, labels) placed by layouts (boxes and grids), with a Page as the top-level layout."""

from databrowser.layouts import GridLayout, HBoxLayout, Layout, Page, VBoxLayout
from databrowser.widgets import (Image, ImageControls, KeyValue, Label, Link, Placeholder, Status, Table,
                                 Widget)

__all__ = ["GridLayout", "HBoxLayout", "Image", "ImageControls", "KeyValue", "Label", "Layout", "Link", "Page",
           "Placeholder", "Status", "Table", "VBoxLayout", "Widget"]
