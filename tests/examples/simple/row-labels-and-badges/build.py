"""Loss curves per learning rate, one rate flagged as diverged."""

from pathlib import Path

from databrowser import Badge, DataPage


def plot(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 3"/>', encoding="utf-8")


page = DataPage("site/index.html", "Learning rate sweep", columns=2, column_titles=["Train loss", "Val loss"])
for rate, label, badge in [("1e-4", "lr = 1e-4", None), ("1e-2", "lr = 1e-2", Badge("diverged", "error")),
                           ("3e-4", "", None)]:
    for curve in ("train", "val"):
        plot(f"site/lr{rate}/{curve}.svg")
    page.add_row([(f"lr{rate}/train.svg", f"lr {rate}"), (f"lr{rate}/val.svg", f"lr {rate}")], label=label, badge=badge)
page.write()
