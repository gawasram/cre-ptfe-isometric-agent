"""
Automated Spec Extractor Engine
Parses split PDF pages from ilovepdf_extracted-pages/ and stores structured JSON drawing specs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXTRACTED_PAGES_DIR = ROOT / "ilovepdf_extracted-pages"
OUTPUTS_DIR = ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


def extract_page_spec(page_num: int) -> dict:
    pdf_path = (
        EXTRACTED_PAGES_DIR
        / f"ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150-{page_num}.pdf"
    )
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Source PDF page not found: {pdf_path}")

    spec = {
        "page_number": page_num,
        "line_number": "",
        "sheet_number": "1 OF 1",
        "cut_lengths": [],
        "bom_items": [],
        "continuations": [],
        "pdf_path": str(pdf_path.resolve()),
    }

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()
        text = page.extract_text() or ""

        # Extract line number regex match if embedded in text
        match_line = re.search(r'(\d+"-[A-Z0-9]+-\d+-\d+-[A-Z0-9-]+)', text)
        if match_line:
            spec["line_number"] = match_line.group(1)

        # Extract all words found on canvas
        spec["words_count"] = len(words)

    # Saved spec JSON file
    spec_path = OUTPUTS_DIR / f"ISO_{page_num}_SPEC.json"
    spec_path.write_text(json.dumps(spec, indent=2))
    return spec


def main():
    parser = argparse.ArgumentParser(description="CRE PDF Spec Extractor Engine")
    parser.add_argument("--page", type=int, required=True, help="Page number (e.g. 70, 71, 72, 73)")
    args = parser.parse_args()

    spec = extract_page_spec(args.page)
    print(f"✅ Extracted drawing spec for Page {args.page}: {OUTPUTS_DIR / f'ISO_{args.page}_SPEC.json'}")


if __name__ == "__main__":
    main()
