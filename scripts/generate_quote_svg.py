"""Pick a random coding quote and render a README SVG card."""
from __future__ import annotations

import json
import random
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUOTES = json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))
OUT = ROOT / "assets" / "dev-quote.svg"

# Card colors (match reference vibe)
BG = "#161b22"
BORDER = "#30363d"
QUOTE = "#79c0ff"
AUTHOR = "#ff7b72"
WIDTH = 860
PAD_X = 36
PAD_Y = 28


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> None:
    item = random.choice(QUOTES)
    quote = item["q"].strip()
    author = item["a"].strip()

    # wrap for SVG text lines
    lines = textwrap.wrap(quote, width=68) or [quote]
    line_h = 28
    text_block_h = len(lines) * line_h
    height = PAD_Y * 2 + text_block_h + 40

    text_nodes = []
    y = PAD_Y + 22
    for i, line in enumerate(lines):
        prefix = '"' if i == 0 else ""
        suffix = '"' if i == len(lines) - 1 else ""
        text_nodes.append(
            f'<text x="{PAD_X}" y="{y}" fill="{QUOTE}" font-size="18" '
            f'font-family="Georgia, \'Times New Roman\', serif" font-style="italic">'
            f"{esc(prefix + line + suffix)}</text>"
        )
        y += line_h

    author_y = height - 18
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Dev quote">\n'
        f'  <rect width="100%" height="100%" rx="14" ry="14" fill="{BG}" '
        f'stroke="{BORDER}" stroke-width="2"/>\n'
        f'  {chr(10).join(text_nodes)}\n'
        f'  <text x="{WIDTH - PAD_X}" y="{author_y}" fill="{AUTHOR}" font-size="15" '
        f'font-family="ui-sans-serif, Segoe UI, Helvetica, Arial, sans-serif" '
        f'text-anchor="end">- {esc(author)}</text>\n'
        f"</svg>\n"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8", newline="\n")
    print(f"Wrote {OUT} ({len(lines)} lines) — {author}")


if __name__ == "__main__":
    main()
