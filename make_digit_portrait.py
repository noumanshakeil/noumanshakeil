"""Digit portrait where numbers are clearly visible.

Each mosaic cell is a large bold digit colored from the photo — no solid
photo fill underneath. Zoom in = numbers. Zoom out = your face.
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

# Fewer, larger cells so each digit is readable on GitHub
COLS = 56
DIGITS = "9876543210@"

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


def digit_color(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Mix photo hue with bright cyan so glyphs stay obviously 'numbers'."""
    y = max(0.18, luma(r, g, b))
    # terminal cyan ramp by brightness
    cyan = (
        int(40 + 160 * y),
        int(90 + 150 * y),
        int(140 + 115 * y),
    )
    # keep a bit of skin/hair hue so the face still looks like you
    return (
        min(255, int(r * 0.45 + cyan[0] * 0.55)),
        min(255, int(g * 0.40 + cyan[1] * 0.60)),
        min(255, int(b * 0.35 + cyan[2] * 0.65)),
    )


def prepare_cutout() -> Image.Image:
    if OUT_CUTOUT.exists():
        cut = Image.open(OUT_CUTOUT).convert("RGBA")
    else:
        src = Image.open(SRC).convert("RGBA")
        w, h = src.size
        src = src.crop((int(w * 0.10), 0, int(w * 0.90), int(h * 0.80)))
        cut = remove(src)
        cut.save(OUT_CUTOUT)

    base = Image.new("RGBA", cut.size, (*BG, 255))
    base.alpha_composite(cut)
    rgb = base.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.25)
    rgb = ImageEnhance.Color(rgb).enhance(1.1)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=2))
    return rgb


def render_digit_portrait() -> Image.Image:
    work = prepare_cutout()

    # Large glyphs — clearly readable as numbers
    cell_w, cell_h = 14, 18
    rows = max(16, int(COLS * (work.height / work.width) * (cell_w / cell_h)))
    small = work.resize((COLS, rows), Image.Resampling.BOX)
    px = small.load()

    font = load_font(cell_h - 2, bold=True)
    pad = 10
    canvas = Image.new("RGB", (COLS * cell_w + pad * 2, rows * cell_h + pad * 2), BG)
    draw = ImageDraw.Draw(canvas)

    for y in range(rows):
        for x in range(COLS):
            r, g, b = px[x, y]
            # skip background
            if abs(r - BG[0]) < 12 and abs(g - BG[1]) < 12 and abs(b - BG[2]) < 12:
                continue
            if luma(r, g, b) < 0.05:
                continue

            yv = luma(r, g, b)
            # darker photo → denser-looking digit glyph
            idx = min(len(DIGITS) - 1, int((1.0 - yv) * (len(DIGITS) - 1)))
            ch = DIGITS[idx]
            fill = digit_color(r, g, b)

            # THE digit IS the pixel — no photo rectangle under it
            draw.text(
                (pad + x * cell_w, pad + y * cell_h - 1),
                ch,
                fill=fill,
                font=font,
            )

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
