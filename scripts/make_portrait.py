"""Photo -> ASCII portrait (dark pixels = dense chars, for ink on paper).
Usage: python scripts/make_portrait.py PHOTO   (writes assets/portrait.txt only)"""
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter, ImageOps

COLS, ROWS = 108, 54  # cells are 1:2 (Geist Mono advance 0.6 em, line height 1.2 em), so a square crop needs COLS = 2 * ROWS
RAMP = "  .:-=+*#%@"  # light -> dark
LO, HI = 0.18, 0.58  # tone below LO = blank (skin, background), above HI = solid
TONE = 0.3  # <1 lifts the dark end of the green channel so hair strands spread over the ramp instead of all being solid
MARGIN = 0.03  # padding around the non-white bbox, as a fraction of its size

def main(photo):
    im = ImageOps.exif_transpose(Image.open(photo)).convert("RGB")
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, "white")).point(lambda v: 255 if v > 12 else 0).convert("L").getbbox()
    l, t, r, b = bbox
    m = int(MARGIN * max(r - l, b - t))
    side = max(r - l, b - t) + 2 * m  # square crop centred on the bbox
    cx, cy = (l + r) // 2, (t + b) // 2
    im = ImageOps.expand(im, border=side, fill="white")  # a crop past the edge would pad with black
    im = im.crop((cx + side - side // 2, cy + side - side // 2, cx + side + side // 2, cy + side + side // 2)).split()[1]  # green: skin stays light, lips and lines stand out
    big = im.resize((COLS * 4, ROWS * 4), Image.LANCZOS)
    mean = big.resize((COLS, ROWS), Image.BOX)
    # thin black lines (frame, brows, outline) would be averaged away: pull light cells toward their darkest pixel, leave dark (hair) cells alone
    low = ImageChops.darker(mean, big.filter(ImageFilter.MinFilter(5)).resize((COLS, ROWS), Image.BOX))
    im = ImageChops.subtract(mean, ImageChops.multiply(mean, ImageChops.subtract(mean, low))).filter(ImageFilter.UnsharpMask(1, 120, 2))
    rows = []
    for y in range(ROWS):
        line = ""
        for x in range(COLS):
            d = min(max((1 - (im.getpixel((x, y)) / 255) ** TONE - LO) / (HI - LO), 0), 1)
            line += RAMP[min(int(d * len(RAMP)), len(RAMP) - 1)]
        rows.append(line.rstrip())
    out = Path(__file__).resolve().parent.parent / "assets" / "portrait.txt"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("\n".join(rows))

if __name__ == "__main__":
    main(sys.argv[1])
