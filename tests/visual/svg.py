"""Plots for the visual cases: SVG files drawn from a few numbers, so every run draws the
same pixels and the cases need no image library."""

from pathlib import Path


def plot(path, hue: int, bars: list[int], width: int = 320, height: int = 200) -> None:
    """A bar chart in one hue: a light background and a bar per value, out of 10."""
    step = width / len(bars)
    rects = "".join(
        f'<rect x="{i * step + 4:.0f}" y="{height - value * height // 10}" width="{step - 8:.0f}" '
        f'height="{value * height // 10}" fill="hsl({hue} 60% 45%)"/>' for i, value in enumerate(bars))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="hsl({hue} 40% 92%)"/>{rects}</svg>\n', encoding="utf-8")
