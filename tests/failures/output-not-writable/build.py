"""A site directory left read-only by an earlier publish step."""

import os

from databrowser import GroupPage

os.mkdir("site", 0o555)
GroupPage("site/index.html", "Runs", ["Run"]).write()
