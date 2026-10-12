"""Render portrait.png as a digit mosaic SVG (numbers as photo)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).parent
SRC = ROOT / "assets" / "portrait.png"
OUT = ROOT / "assets" / "portrait-digits.svg"

COLS = 70
# bright photo pixels → denser / higher digits
DIGITS = "1234567890"


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def color_for(t: float) -> str:
    """t=0 dark → deep slate; t=1 bright → cool cyan-white."""
    r = int(lerp(28, 190, t))
    g = int(lerp(40, 230, t))
    b = int(lerp(58, 255, t))
    return f"#{r:02x}{g:02x}{b:02x}"


def main() -> None:
    img = Image.open(SRC).convert("L")
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.25)

    w, h = img.size
    aspect = 0.52
    rows = max(8, int(COLS * (h / w) * aspect))
    img = img.resize((COLS, rows), Image.Resampling.LANCZOS)
    px = img.load()

    cell_w, cell_h = 9, 13
    pad = 10
    svg_w = COLS * cell_w + pad * 2
    svg_h = rows * cell_h + pad * 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">',
        '<rect width="100%" height="100%" fill="#0d1117" rx="8"/>',
        '<g font-family="Consolas, ui-monospace, Menlo, monospace" font-size="11" font-weight="700">',
    ]

    for y in range(rows):
        for x in range(COLS):
            v = px[x, y] / 255.0
            # drop blown-out outdoor background
            if v > 0.92:
                continue
            # drop near-black so silhouette isn't a solid brick
            if v < 0.08:
                continue
            idx = min(len(DIGITS) - 1, int(v * (len(DIGITS) - 1)))
            ch = DIGITS[idx]
            fill = color_for(v)
            cx = pad + x * cell_w
            cy = pad + 10 + y * cell_h
            parts.append(f'<text x="{cx}" y="{cy}" fill="{fill}">{ch}</text>')

    parts.append("</g></svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUT} ({COLS}x{rows})")


if __name__ == "__main__":
    main()
