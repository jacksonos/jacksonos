"""Photo -> ASCII portrait (dark pixels = dense chars, for ink on paper).
Usage: python scripts/make_portrait.py PHOTO   (writes assets/portrait.txt only)"""
import sys
from pathlib import Path
from PIL import Image, ImageOps

COLS, ROWS = 72, 48
RAMP = "  .:-=+*#%@"  # light -> dark
LO, HI = 0.15, 0.9  # darkness below LO = blank (background), above HI = solid (shirt, hair)
GAMMA = 1.4  # >1 lightens midtones (keeps skin sparse)
CROP = (0.1, 0.0, 0.9, 1.0)  # fractions l,t,r,b; 3:4 box, since 72x48 cells with 2:1 glyphs is 3:4

def main(photo):
    im = ImageOps.exif_transpose(Image.open(photo)).convert("L")
    w, h = im.size
    im = im.crop((int(CROP[0] * w), int(CROP[1] * h), int(CROP[2] * w), int(CROP[3] * h)))
    im = ImageOps.autocontrast(im, cutoff=2).resize((COLS, ROWS), Image.LANCZOS)
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
