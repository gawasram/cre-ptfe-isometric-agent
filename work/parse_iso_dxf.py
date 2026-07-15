from __future__ import annotations

import re
from pathlib import Path


DXF = Path("tmp/ISO_31_TO_35_CONVERTED.dxf")


def pairs(path: Path):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i in range(0, len(lines) - 1, 2):
        try:
            code = int(lines[i].strip())
        except ValueError:
            continue
        yield code, lines[i + 1].rstrip()


entities: list[dict] = []
section = None
current = None
pending_section = False
for code, value in pairs(DXF):
    if code == 0 and value == "SECTION":
        pending_section = True
        continue
    if pending_section and code == 2:
        section = value
        pending_section = False
        continue
    if code == 0 and value == "ENDSEC":
        if current is not None and section == "ENTITIES":
            entities.append(current)
        current = None
        section = None
        continue
    if section != "ENTITIES":
        continue
    if code == 0:
        if current is not None:
            entities.append(current)
        current = {"type": value, "pairs": []}
    elif current is not None:
        current["pairs"].append((code, value))


def first(entity, code, default=""):
    return next((value for c, value in entity["pairs"] if c == code), default)


def clean_mtext(value: str) -> str:
    value = value.replace("\\P", " ").replace("\\~", " ")
    value = re.sub(r"\\[A-Za-z][^;]*;", "", value)
    value = re.sub(r"[{}]", "", value)
    value = value.replace("\\S3/4;", '3/4"')
    return " ".join(value.split())


texts = []
for entity in entities:
    if entity["type"] not in {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}:
        continue
    raw = "".join(value for code, value in entity["pairs"] if code in ({1, 3} if entity["type"] == "MTEXT" else {1}))
    try:
        x = float(first(entity, 10, "0"))
        y = float(first(entity, 20, "0"))
    except ValueError:
        x = y = 0.0
    texts.append((x, y, clean_mtext(raw), entity["type"]))


print(f"entities={len(entities)} texts={len(texts)}")
for x, y, text, kind in sorted(texts, key=lambda row: (-row[1], row[0])):
    upper = text.upper()
    if any(
        token in upper
        for token in (
            "SHEET NO",
            "LINE NO",
            "SNA",
            "CUSTOMER",
            "PROJECT",
            "CORROSION RESISTANT",
            "LINING",
            "FLANGE CONNE",
            "HYDRO",
            "SPARK",
            "PIPE SPOOL",
            "BALL VALVE",
            "PLUG VALVE",
            "BLIND FLANGE",
        )
    ):
        print(f"{x:12.1f}|{y:12.1f}|{kind:6s}|{text}")
