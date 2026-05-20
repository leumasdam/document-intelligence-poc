"""Generate the README hero banner for the document-intelligence repo.

Run once to produce docs/banner.png. Committed so GitHub renders it at the
top of the README.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "banner.png"

W, H = 1280, 420
NAVY = (0, 47, 95)
NAVY_DARK = (0, 30, 80)
BLUE = (51, 128, 224)
WHITE = (248, 250, 252)
MUTED = (158, 180, 207)
CHIP = (0, 62, 120)

FONTS = "C:/Windows/Fonts"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(f"{FONTS}/{name}", size)


def main() -> None:
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)

    # Vertical gradient navy -> darker navy
    for y in range(H):
        t = y / H
        r = int(NAVY[0] + (NAVY_DARK[0] - NAVY[0]) * t)
        g = int(NAVY[1] + (NAVY_DARK[1] - NAVY[1]) * t)
        b = int(NAVY[2] + (NAVY_DARK[2] - NAVY[2]) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))

    # Dot grid
    for y in range(0, H, 30):
        for x in range(0, W, 30):
            d.ellipse([x, y, x + 2, y + 2], fill=(12, 58, 105))

    margin = 80

    # Logo mark — navy "U" tile
    d.rounded_rectangle([margin, margin, margin + 56, margin + 56], radius=12, fill=WHITE)
    uf = font("segoeuib.ttf", 38)
    uw = d.textlength("U", font=uf)
    d.text((margin + 28 - uw / 2, margin + 4), "U", font=uf, fill=NAVY)
    bf = font("segoeuib.ttf", 30)
    d.text((margin + 72, margin + 12), "Document Intelligence", font=bf, fill=WHITE)

    # Headline
    hf = font("georgiab.ttf", 56)
    d.text((margin, margin + 92), "AI-assisted tools for the", font=hf, fill=WHITE)
    d.text((margin, margin + 158), "insurance claims back-office", font=hf, fill=WHITE)

    # Subtitle
    sf = font("segoeui.ttf", 24)
    d.text((margin, margin + 232),
           "PDF extraction · case routing · summarization — with the adjuster in the loop.",
           font=sf, fill=MUTED)

    # Tool chips
    chips = ["Extract", "Classify", "Summarize"]
    cf = font("segoeuib.ttf", 22)
    cx = margin
    cy = margin + 280
    for chip in chips:
        cw = d.textlength(chip, font=cf)
        d.rounded_rectangle([cx, cy, cx + cw + 44, cy + 48], radius=24, fill=CHIP)
        d.text((cx + 22, cy + 10), chip, font=cf, fill=WHITE)
        cx += cw + 44 + 14

    # Right-side accent + stack
    d.ellipse([W - 280, -160, W + 160, 280], fill=(0, 56, 112))
    img2 = Image.new("RGB", (W, H))
    img2.paste(img)
    d = ImageDraw.Draw(img2)
    # (re-draw chips region not needed; accent is behind text area on the right only)

    stf = font("segoeui.ttf", 20)
    stack = "FastAPI  ·  Claude Opus 4.7  ·  pdfplumber  ·  Docker"
    sw = d.textlength(stack, font=stf)
    d.text((W - margin - sw, H - margin + 12), stack, font=stf, fill=MUTED)

    # Bottom accent line
    d.rectangle([0, H - 6, W, H], fill=BLUE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img2.save(OUT, "PNG")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
