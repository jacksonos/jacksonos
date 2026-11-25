"""Photo -> ASCII portrait (dark pixels = dense chars, for ink on paper).
Usage: python scripts/make_portrait.py PHOTO   (writes assets/portrait.txt only)"""
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter, ImageOps

COLS, ROWS = 84, 42
RAMP = "  .:-=+*#%@"  # light -> dark
LO, HI = 0.09, 0.95  # darkness below LO = blank (background), above HI = solid (hair)
GAMMA = 0.75  # <1 darkens midtones (keeps skin visible)
MARGIN = 0.03  # padding around the non-white bbox, as a fraction of its size

def main(photo):
    im = ImageOps.exif_transpose(Image.open(photo)).convert("RGB")
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, "white")).point(lambda v: 255 if v > 12 else 0).convert("L").getbbox()
    l, t, r, b = bbox
    m = int(MARGIN * max(r - l, b - t))
    side = max(r - l, b - t) + 2 * m  # square crop centred on the bbox
    cx, cy = (l + r) // 2, (t + b) // 2
    im = im.convert("L").crop((cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2))
    im = im.resize((COLS, ROWS), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1, 120, 2))
    rows = []
    for y in range(ROWS):
        line = ""
        for x in range(COLS):
            d = min(max((1 - im.getpixel((x, y)) / 255 - LO) / (HI - LO), 0), 1) ** GAMMA
            line += RAMP[min(int(d * len(RAMP)), len(RAMP) - 1)]
        rows.append(line.rstrip())
    out = Path(__file__).resolve().parent.parent / "assets" / "portrait.txt"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("\n".join(rows))

if __name__ == "__main__":
    main(sys.argv[1])
