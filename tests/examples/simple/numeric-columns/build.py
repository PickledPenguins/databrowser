"""Training runs with their epoch count, final validation loss and accuracy."""

from pathlib import Path

from databrowser import GroupPage

runs = [("resnet18-lr3e-4", 90, 0.4123, 0.8871, "adamw"), ("resnet18-lr1e-3", 90, 0.4410, 0.8792, "adamw"),
        ("resnet50-lr3e-4", 120, 0.3517, 0.9104, "sgd + nesterov"), ("vit-s16", 300, 0.3302, 0.9188, "adamw")]
index = GroupPage("site/index.html", "Image classifier sweep", ["Run", "Epochs", "Val loss", "Accuracy", "Optimizer"])
for name, epochs, loss, accuracy, optimizer in runs:
    Path(f"site/{name}").mkdir(parents=True, exist_ok=True)
    Path(f"site/{name}/metrics.csv").write_text("epoch,loss\n", encoding="utf-8")
    index.add_row(f"{name}/metrics.csv", [name, epochs, loss, accuracy, optimizer])
index.write()
