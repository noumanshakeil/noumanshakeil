"""High-likeness digit portrait for the GitHub profile hero.

Uses rembg for a clean subject cutout, then a dense photo-colored digit
mosaic so the face is recognizable and still clearly made of numbers.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageFilter
from rembg import remove

ROOT = Path(__file__).parent
SRC = ROOT / "assets" / "portrait.png"
OUT_HERO = ROOT / "assets" / "hero.png"
OUT_MOBILE = ROOT / "assets" / "hero-mobile.png"
OUT_PORTRAIT = ROOT / "assets" / "portrait-digits.png"
OUT_CUTOUT = ROOT / "assets" / "portrait-cutout.png"

BG = (13, 17, 23)
PANEL_BG = (22, 27, 34)
BORDER = (48, 54, 61)
CYAN = (88, 166, 255)
MUTED = (139, 148, 158)
WHITE = (230, 237, 243)
GREEN = (63, 185, 80)

COLS = 140
DIGITS = "9876543210"

BLOCKS: list[tuple[str, list[str]]] = [
    ("$ whoami", ["Muhammad Nouman Shakeel"]),
    (
        "$ roles",
        [
            "Founder · PocketMind",
            "Co-founder · CodexBridge",
            "AI Engineer · Zindex",
            "BS AI · NUST Islamabad",
        ],
    ),
    (
        "$ focus",
        [
            "Local / offline AI · agents",
            "RAG · vision · hybrid apps",
        ],
    ),
    (
        "$ stack",
        [
            "Python · TypeScript · FastAPI",
            "Next.js · PyTorch · llama.cpp",
            "Ollama · YOLO · MediaPipe",
        ],
    ),
    (
        "$ shipped",
        [
            "PocketMind AI",
            "PocketMind AI: Offline AI Labs",
            "PULSE · Harborline · Cold Outreach",
        ],
    ),
    (
        "$ contact",
        [
            "nouman.shakeel555@gmail.com",
            "linkedin.com/in/noumanshakeil",
        ],
    ),
]


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/CascadiaMono.ttf",
        "C:/Windows/Fonts/courbd.ttf" if bold else "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/lucon.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def luma(r: int, g: int, b: int) -> float:
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(x * (1 - t) + y * t) for x, y in zip(a, b))  # type: ignore[return-value]


def prepare_cutout() -> Image.Image:
    src = Image.open(SRC).convert("RGBA")
    w, h = src.size
    src = src.crop((int(w * 0.10), 0, int(w * 0.90), int(h * 0.80)))

    cut = remove(src)
    cut.save(OUT_CUTOUT)

    # composite onto dark bg
    base = Image.new("RGBA", cut.size, (*BG, 255))
    base.alpha_composite(cut)
    rgb = base.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    rgb = ImageEnhance.Color(rgb).enhance(1.05)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.0, percent=120, threshold=2))
    return rgb


def render_digit_portrait() -> Image.Image:
    work = prepare_cutout()

    cell = 7
    rows = max(28, int(COLS * (work.height / work.width)))
    small = work.resize((COLS, rows), Image.Resampling.BOX)
    px = small.load()

    font = load_font(cell, bold=True)
    pad = 8
    canvas = Image.new("RGB", (COLS * cell + pad * 2, rows * cell + pad * 2), BG)
    draw = ImageDraw.Draw(canvas)

    for y in range(rows):
        for x in range(COLS):
            r, g, b = px[x, y]
            # skip pure background cells from rembg composite
            if abs(r - BG[0]) < 10 and abs(g - BG[1]) < 10 and abs(b - BG[2]) < 10:
                continue
            if luma(r, g, b) < 0.045:
                continue

            x0 = pad + x * cell
            y0 = pad + y * cell

            # cell fill = photo color (likeness)
            draw.rectangle((x0, y0, x0 + cell - 1, y0 + cell - 1), fill=(r, g, b))

            # digit overlay — visible but not washing the face
            yv = luma(r, g, b)
            idx = min(len(DIGITS) - 1, int((1.0 - yv) * (len(DIGITS) - 1)))
            digit_target = (10, 14, 20) if yv > 0.40 else (220, 235, 255)
            digit_col = blend((r, g, b), digit_target, 0.42)
            draw.text((x0 + 1, y0 - 1), DIGITS[idx], fill=digit_col, font=font)

    return canvas


def render_terminal_panel(width: int = 460, font_size: int = 16) -> Image.Image:
    font_cmd = load_font(font_size, bold=True)
    font_val = load_font(font_size, bold=False)
    line_h = font_size + 8
    gap = 12
    pad_x, pad_y = 28, 28
    lines = sum(1 + len(v) for _, v in BLOCKS)
    height = pad_y * 2 + lines * line_h + gap * (len(BLOCKS) - 1) + 24

    canvas = Image.new("RGB", (width, height), PANEL_BG)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (6, 6, width - 7, height - 7), radius=12, outline=BORDER, width=2
    )
    y = pad_y
    for cmd, values in BLOCKS:
        draw.text((pad_x, y), cmd, fill=CYAN, font=font_cmd)
        y += line_h
        for val in values:
            color = GREEN if val.startswith("PocketMind AI") else WHITE
            draw.text((pad_x + 10, y), val, fill=color, font=font_val)
            y += line_h
        y += gap
    draw.text((pad_x, height - 28), "▌", fill=MUTED, font=font_cmd)
    return canvas


def framed(img: Image.Image, pad: int = 20) -> Image.Image:
    out = Image.new("RGB", (img.width + pad * 2, img.height + pad * 2), BG)
    out.paste(img, (pad, pad))
    draw = ImageDraw.Draw(out)
    draw.rounded_rectangle(
        (4, 4, out.width - 5, out.height - 5), radius=14, outline=BORDER, width=2
    )
    return out


def scale_to_height(img: Image.Image, height: int) -> Image.Image:
    if img.height == height:
        return img
    scale = height / img.height
    return img.resize((max(1, int(img.width * scale)), height), Image.Resampling.LANCZOS)


def main() -> None:
    portrait = render_digit_portrait()
    portrait.save(OUT_PORTRAIT, "PNG", optimize=True)

    panel = render_terminal_panel(width=460, font_size=16)
    max_h = 540
    portrait_fit = scale_to_height(portrait, max_h) if portrait.height > max_h else portrait
    target_h = max(portrait_fit.height, panel.height)
    p = scale_to_height(portrait_fit, target_h)

    if panel.height < target_h:
        padded = Image.new("RGB", (panel.width, target_h), PANEL_BG)
        padded.paste(panel, (0, (target_h - panel.height) // 2))
        draw = ImageDraw.Draw(padded)
        draw.rounded_rectangle(
            (6, 6, padded.width - 7, padded.height - 7),
            radius=12,
            outline=BORDER,
            width=2,
        )
        t = padded
    else:
        t = panel

    gap = 24
    desktop = Image.new("RGB", (p.width + gap + t.width, target_h), BG)
    desktop.paste(p, (0, 0))
    desktop.paste(t, (p.width + gap, 0))
    framed(desktop, pad=22).save(OUT_HERO, "PNG", optimize=True)

    mobile_w = 720
    p_m = portrait_fit
    if p_m.width > mobile_w - 40:
        scale = (mobile_w - 40) / p_m.width
        p_m = p_m.resize((mobile_w - 40, int(p_m.height * scale)), Image.Resampling.LANCZOS)
    t_m = render_terminal_panel(width=mobile_w - 40, font_size=17)
    stack = Image.new("RGB", (mobile_w - 40, p_m.height + 20 + t_m.height), BG)
    stack.paste(p_m, ((mobile_w - 40 - p_m.width) // 2, 0))
    stack.paste(t_m, (0, p_m.height + 20))
    framed(stack, pad=18).save(OUT_MOBILE, "PNG", optimize=True)

    print(f"Wrote {OUT_PORTRAIT.name} {portrait.size}")
    print(f"Wrote {OUT_HERO.name} {Image.open(OUT_HERO).size}")
    print(f"Wrote {OUT_MOBILE.name} {Image.open(OUT_MOBILE).size}")


if __name__ == "__main__":
    main()
