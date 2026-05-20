"""Generate the 1200x630 social-share card (og:image) for the app.

Run once to produce static/og-image.png. Committed so the deployed app can
serve it; LinkedIn / Slack render it when the app URL is shared.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "og-image.png"

W, H = 1200, 630
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

    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(
            int(NAVY[i] + (NAVY_DARK[i] - NAVY[i]) * t) for i in range(3)
        ))
    for y in range(0, H, 30):
        for x in range(0, W, 30):
            d.ellipse([x, y, x + 2, y + 2], fill=(12, 58, 105))
    d.ellipse([W - 300, -180, W + 160, 300], fill=(0, 56, 112))
    d = ImageDraw.Draw(img)

    margin = 80

    # Logo
    d.rounded_rectangle([margin, margin, margin + 56, margin + 56], radius=12, fill=WHITE)
    uf = font("segoeuib.ttf", 38)
    d.text((margin + 28 - d.textlength("U", font=uf) / 2, margin + 4), "U", font=uf, fill=NAVY)
    d.text((margin + 72, margin + 13), "Document Intelligence", font=font("segoeuib.ttf", 30), fill=WHITE)

    # Headline
    hf = font("georgiab.ttf", 60)
    d.text((margin, margin + 110), "AI-assisted tools for", font=hf, fill=WHITE)
    d.text((margin, margin + 184), "insurance claims", font=hf, fill=WHITE)

    # Subtitle
    d.text((margin, margin + 280),
           "Extract structured data, route incoming cases, summarize long",
           font=font("segoeui.ttf", 26), fill=MUTED)
    d.text((margin, margin + 314),
           "narratives — with the adjuster in the loop on every decision.",
           font=font("segoeui.ttf", 26), fill=MUTED)

    # Chips
    cf = font("segoeuib.ttf", 23)
    cx, cy = margin, margin + 372
    for chip in ["Extract", "Classify", "Summarize"]:
        cw = d.textlength(chip, font=cf)
        d.rounded_rectangle([cx, cy, cx + cw + 46, cy + 50], radius=25, fill=CHIP)
        d.text((cx + 23, cy + 11), chip, font=cf, fill=WHITE)
        cx += cw + 46 + 15

    # Footer
    d.text((margin, H - margin - 24), "Live concept demo", font=font("segoeuib.ttf", 24), fill=WHITE)
    stack = "FastAPI · Claude Opus 4.7 · Docker"
    sf = font("segoeui.ttf", 21)
    d.text((W - margin - d.textlength(stack, font=sf), H - margin - 22), stack, font=sf, fill=MUTED)
    d.rectangle([0, H - 7, W, H], fill=BLUE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
