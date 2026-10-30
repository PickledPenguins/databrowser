"""A learning-rate and batch-size sweep: a table of runs and a page of curves for each."""

from pathlib import Path

from databrowser import Badge, DataPage, GroupPage, Theme


def plot(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>', encoding="utf-8")


theme = Theme(banner="Vision team experiments")
sweep = GroupPage("site/index.html", "Sweep 2026-10-28: lr x batch", ["Run", "lr", "Batch", "Best val acc", "Status"],
                  header="ResNet-50 on the internal parts dataset, 3 seeds each", theme=theme)
runs = [(3e-4, 128, 0.912, Badge("done", "ok")), (3e-4, 256, 0.907, Badge("done", "ok")),
        (1e-3, 128, 0.884, Badge("early stop", "warn")), (1e-2, 128, None, Badge("diverged", "error"))]
for lr, batch, accuracy, status in runs:
    name = f"lr{lr:g}-b{batch}"
    page = DataPage(f"site/{name}/index.html", name, columns=3, column_titles=["Loss", "Accuracy", "LR schedule"],
                    parent=sweep, theme=theme)
    for seed in (0, 1, 2):
        row = []
        for curve in ("loss", "accuracy", "lr"):
            plot(f"site/{name}/seed{seed}/{curve}.svg")
            row.append((f"seed{seed}/{curve}.svg", f"seed {seed}"))
        page.add_row(row, label=f"Seed {seed}")
    page.write()
    sweep.add_row(page, [name, lr, batch, accuracy, status])
sweep.write()
