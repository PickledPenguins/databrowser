"""An institute site: departments with their own looks, projects, experiments, results."""

import dataclasses
import os
from pathlib import Path

from databrowser import Badge, DataPage, GroupPage, Theme

for name in ("banner", "physics-title", "fig1", "fig2"):
    Path(f"shared/{name}.svg").parent.mkdir(parents=True, exist_ok=True)
    Path(f"shared/{name}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>',
                                          encoding="utf-8")
base = Theme(banner="Institute of Applied Science", banner_image="shared/banner.svg", bottom_banner="Institute")
physics = dataclasses.replace(base, banner_color="#3b0764", title_image="shared/physics-title.svg",
                              styles={"top-banner": "user-page"})
biology = dataclasses.replace(base, banner_color="#a7f3d0", banner_image=None)
institute = GroupPage("site/index.html", "Departments", ["Department", "Projects"], theme=base)
departments = {}
for department, theme in [("physics", physics), ("biology", biology)]:
    departments[department] = GroupPage(f"site/{department}/index.html", department.title(), ["Project", "Status"],
                                        parent=institute, theme=theme)
leaves = []
for department, project, experiment in [("physics", "lasers", "pulse-shaping"), ("biology", "imaging", "light-sheet")]:
    project_page = GroupPage(f"site/{department}/{project}/index.html", project, ["Experiment", "Figures"],
                             parent=departments[department], theme=departments[department].theme)
    result = DataPage(f"site/{department}/{project}/{experiment}/results/index.html", f"{experiment} results",
                      columns=2, column_titles=["Figure 1", "Figure 2"], parent=project_page,
                      theme=project_page.theme)
    # Figures stay in shared/, outside the site. Image paths are relative to the page.
    result.add_row([(os.path.relpath(f"shared/{fig}.svg", result.path.parent), fig) for fig in ("fig1", "fig2")],
                   label=experiment, badge=Badge("published", "ok"))
    project_page.add_row(result, [experiment, 2])
    departments[department].add_row(project_page, [project, Badge("active", "info")])
    leaves.append((result, project_page))
# A row in the biology lasers-free project linking sideways to the physics results.
leaves[1][1].add_row(leaves[0][0], ["pulse-shaping (physics)", 2])
for result, project_page in leaves:
    result.write()
    project_page.write()
for department, page in departments.items():
    page.write()
    institute.add_row(page, [department.title(), 1])
institute.write()
