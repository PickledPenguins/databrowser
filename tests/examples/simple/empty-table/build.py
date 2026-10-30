"""The page of a campaign that has no results yet."""

from databrowser import GroupPage

GroupPage("site/index.html", "Campaign 2027", ["Series", "Runs", "Status"],
          header="Planned: tank B, March 2027").write()
