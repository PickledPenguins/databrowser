"""An inventory of samples whose columns hold a mix of types."""

from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from databrowser import Badge, GroupPage

rows = [("S-001", 12, Decimal("0.250"), Fraction(1, 3), "B7", True, Badge("ok", "ok")),
        ("S-002", None, Decimal("1.125"), 0.5, "B7", False, None),
        ("S-003", 7, None, 2, "n/a", None, Badge("recheck", "warn"))]
index = GroupPage("site/index.html", "Sample inventory",
                  ["Sample", "Count", "Mass (g)", "Ratio", "Batch", "Dried", "Status"])
for row in rows:
    Path(f"site/{row[0]}.txt").parent.mkdir(parents=True, exist_ok=True)
    Path(f"site/{row[0]}.txt").write_text("sample\n", encoding="utf-8")
    index.add_row(f"{row[0]}.txt", list(row))
index.write()
