"""
Batch PDF-to-PNG Converter
Converts all extracted PDF pages in ilovepdf_extracted-pages/ to high-resolution 300 DPI PNG images in png_pages/.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pdfplumber

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXTRACTED_PAGES_DIR = ROOT / "ilovepdf_extracted-pages"
PNG_PAGES_DIR = ROOT / "png_pages"
PNG_PAGES_DIR.mkdir(exist_ok=True)


def convert_pdf_to_png(pdf_file: Path) -> Path:
    page_name = pdf_file.stem.split("-")[-1]
    out_png = PNG_PAGES_DIR / f"page_{page_name}.png"

    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[0]
        im = page.to_image(resolution=300)
        im.save(out_png)

    print(f"✅ Converted {pdf_file.name} -> {out_png.name}")
    return out_png


def convert_all(pages: list[int] | None = None) -> tuple[int, int]:
    pdf_files = sorted(EXTRACTED_PAGES_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF pages in {EXTRACTED_PAGES_DIR}")

    count = 0
    failures = 0
    for pdf_file in pdf_files:
        try:
            page_no = int(pdf_file.stem.split("-")[-1])
            if pages and page_no not in pages:
                continue
            convert_pdf_to_png(pdf_file)
            count += 1
        except Exception as e:
            print(f"❌ Error converting {pdf_file.name}: {e}")
            failures += 1

    print(f"\n✨ Successfully converted {count} PDF pages to PNG images in {PNG_PAGES_DIR}")
    if failures:
        print(f"❌ Failed to convert {failures} PDF page(s)")
    return count, failures


def main():
    parser = argparse.ArgumentParser(description="Convert PDF pages to PNG images")
    parser.add_argument("--pages", type=int, nargs="*", help="Optional list of page numbers to convert (e.g. 70 71 72 106)")
    args = parser.parse_args()

    _count, failures = convert_all(args.pages)
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
