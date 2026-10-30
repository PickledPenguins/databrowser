"""A table of thermal chamber runs, each row linking to the run's page."""

from databrowser import GroupPage

runs = [("run_0412", "baseline, 20 C"), ("run_0413", "heater on, 35 C"), ("run_0414", "heater on, 50 C")]
index = GroupPage("site/index.html", "Thermal chamber runs", ["Run", "Conditions"])
for name, conditions in runs:
    run_page = GroupPage(f"site/{name}/index.html", name, ["File", "Size"])
    run_page.write()
    index.add_row(run_page, [name, conditions])
index.write()
