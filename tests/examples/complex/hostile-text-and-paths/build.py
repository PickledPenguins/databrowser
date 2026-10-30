"""A site whose every name was typed by someone who never expected it to become a web page."""

from pathlib import Path

from databrowser import Badge, DataPage, GroupPage, Theme

NASTY = '<b>&amp; "x" \'y\'</b>'
Path("art").mkdir()
Path('art/"title".svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 1"/>', encoding="utf-8")
theme = Theme(banner=f"Lab {NASTY}", bottom_banner=f"line 1 {NASTY}\nline 2 </div>", title_image='art/"title".svg')
index = GroupPage("site/index.html", f"Top {NASTY}", [f"Name {NASTY}", "N <&>", "Status"],
                  header=f"Header\n{NASTY}", footer=f"Footer\n{NASTY}", theme=theme)
folder = "run #1 & 50% ?'q'"
page = DataPage(f"site/{folder}/index.html", f"Run {NASTY}", columns=2, column_titles=[NASTY, "</figure>"],
                parent=index, theme=theme, header="<script>alert(1)</script>", footer="-->")
row = []
for image in ('a "b".svg', "c#d?e%f.svg"):
    Path(f"site/{folder}/{image}").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/{folder}/{image}").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>',
                                              encoding="utf-8")
    row.append((image, f"{NASTY}\n</figcaption>"))
page.add_row(row, label=f"Label {NASTY}", badge=Badge(f"badge {NASTY}", "error"))
page.add_row([(None, NASTY), (None, "")], label="", badge=Badge("&nbsp;", "info"))
page.write()
index.add_row(page, [Badge(f"{NASTY}", "warn"), 3, Badge("<ok>", "ok")])
index.write()
