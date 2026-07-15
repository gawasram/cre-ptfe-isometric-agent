"""
Visual Output Comparer
Generates side-by-side visual comparisons of input source PNG vs generated CRE output PNG.
"""

from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PNG_PAGES_DIR = ROOT / "png_pages"
OUTPUTS_DIR = ROOT / "outputs"


def create_side_by_side_comparison(page_no: int) -> Path | None:
    src_png = PNG_PAGES_DIR / f"page_{page_no}.png"
    out_png = OUTPUTS_DIR / f"ISO_{page_no}_PTFE.png"

    if not src_png.is_file():
        print(f"⚠️ Source PNG missing: {src_png}")
        return None
    if not out_png.is_file():
        print(f"⚠️ Output PNG missing: {out_png}")
        return None

    img_src = Image.open(src_png).convert("RGB")
    img_out = Image.open(out_png).convert("RGB")

    # Resize both to equal target height
    target_h = 1600
    w_src = int(img_src.width * (target_h / img_src.height))
    w_out = int(img_out.width * (target_h / img_out.height))

    img_src_res = img_src.resize((w_src, target_h), Image.Resampling.LANCZOS)
    img_out_res = img_out.resize((w_out, target_h), Image.Resampling.LANCZOS)

    header_h = 80
    combined_w = w_src + w_out + 20
    combined_h = target_h + header_h

    canvas = Image.new("RGB", (combined_w, combined_h), (240, 240, 240))
    draw = ImageDraw.Draw(canvas)

    # Title Labels
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 36)
    except Exception:
        font = ImageFont.load_default()

    draw.text((w_src / 2 - 200, 20), f"ORIGINAL SOURCE PDF PAGE {page_no}", fill=(0, 0, 0), font=font)
    draw.text((w_src + 20 + w_out / 2 - 200, 20), f"GENERATED CRE CAD OUTPUT ISO_{page_no}_PTFE", fill=(0, 102, 204), font=font)

    # Paste Images
    canvas.paste(img_src_res, (0, header_h))
    canvas.paste(img_out_res, (w_src + 20, header_h))

    # Divider line
    draw.line([(w_src + 10, 0), (w_src + 10, combined_h)], fill=(180, 180, 180), width=6)

    cmp_path = PNG_PAGES_DIR / f"comparison_page_{page_no}.png"
    canvas.save(cmp_path)
    print(f"✅ Comparison image created: {cmp_path}")
    return cmp_path


def main():
    pages = [70, 71, 72, 106]
    for p in pages:
        create_side_by_side_comparison(p)


if __name__ == "__main__":
    main()
