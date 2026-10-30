"""A page given the directory it should go in."""

import os

from databrowser import GroupPage

os.makedirs("site/runs")
GroupPage("site/runs", "Runs", ["Run"]).write()
