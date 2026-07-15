from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from cre_standard_lib import CREModelBuilder

SPEC_PATH = ROOT / "outputs" / "ISO_106_SPEC.json"


def main():
    if not SPEC_PATH.is_file():
        raise FileNotFoundError(f"Spec file not found: {SPEC_PATH}")

    spec = json.loads(SPEC_PATH.read_text())
    builder = CREModelBuilder("ISO_106_PTFE", ROOT / "outputs")

    # 1. Title Block & Sheet Frame
    builder.add_title_block(
        line_number=spec["line_number"],
        sheet_number=spec["sheet_number"],
        drafter="RAM GAWAS",
        drawing_date="15.7.26",
        revision=spec["revision"],
    )

    # 2. Cut Pipe Length Table
    cut_w = [18.0, 25.0, 20.0]
    cut_rows = [["PIECE", "CUT LENGTH", "PIPE"], ["NO", "(MM)", "SIZE"]]
    for item in spec["cut_lengths"]:
        cut_rows.append([item["piece"], str(item["cut_length_mm"]), item["pipe_size"]])
    builder.add_table(15.0, 35.0, cut_w, 5.5, cut_rows, font_size=2.0)

    # 3. Fabrication Materials BOM Table
    bom_w = [8.0, 70.0, 16.0, 33.0, 10.0]
    bom_rows = [["PT", "COMPONENT DESCRIPTION", "N.S.", "ITEM CODE", "QTY"], ["NO", "", "(INS)", "", ""]]
    for item in spec["bom_items"]:
        bom_rows.append([
            str(item["pt_no"]),
            item["description"],
            item["nominal_size"],
            item["item_code"],
            item["qty"],
        ])
    builder.add_table(15.0, 80.0, bom_w, 5.0, bom_rows, font_size=2.0)

    # 4. Topology Piping & Callouts
    p0 = (340.0, 190.0) # Continuation start from DRG 1
    builder.add_text(p0[0] + 5, p0[1], "CONT. FROM DRG 1", 2.25, "LABEL", bold=True)

    # Leg 1: Segment <9> (150° Isometric Axis)
    u150 = (-math.cos(math.radians(30.0)), -math.sin(math.radians(30.0)))
    p1 = (p0[0] + 120.0 * u150[0], p0[1] + 120.0 * u150[1]) # (236.0, 130.0)

    builder.add_line(p0[0], p0[1], p1[0], p1[1], "PIPE", 0.53)
    builder.add_text((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 5.0, "<9> [1]", 2.35, "LABEL", rotation=30, bold=True, align="center")
    builder.add_text((p0[0] + p1[0]) / 2 + 5, (p0[1] + p1[1]) / 2 - 5.0, '2"NS', 2.25, "LABEL", rotation=30, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p0, "p2": p1, "label": "6351", "offset": -10.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_small_callout("5", (p1[0] - 8.0, p1[1] + 8.0), p1)

    # Vertical Riser Leg <10>
    p2 = (p1[0], p1[1] + 35.0)
    builder.add_line(p1[0], p1[1], p2[0], p2[1], "PIPE", 0.53)
    builder.add_text(p1[0] + 5.0, (p1[1] + p2[1]) / 2, "<10> [1]", 2.35, "LABEL", rotation=90, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p1, "p2": p2, "label": "400", "offset": 10.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_text(p1[0] - 15.0, p1[1] - 8.0, "CONT. ON 2\"-WNA-418-1401-1-A82Y-G\nE 676931 N 602970 EL +101830", 2.0, "LABEL", bold=True)

    # Slanted Offset Leg <11>
    p3 = (p2[0] - 25.0, p2[1] + 25.0)
    builder.add_line(p2[0], p2[1], p3[0], p3[1], "PIPE", 0.53)
    builder.add_text((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2 + 4.0, "<11> [1]", 2.35, "LABEL", bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p2, "p2": p3, "label": "480", "offset": 8.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_small_callout("5", (p3[0] - 8.0, p3[1] + 8.0), p3)

    # Riser Leg <12> (90° Vertical Axis)
    p4 = (p3[0], p3[1] + 65.0)
    builder.add_line(p3[0], p3[1], p4[0], p4[1], "PIPE", 0.53)
    builder.add_text(p3[0] - 5.0, (p3[1] + p4[1]) / 2, "<12> [1]", 2.35, "LABEL", rotation=90, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p3, "p2": p4, "label": "1810", "offset": -10.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_small_callout("5", (p4[0] - 8.0, p4[1] + 8.0), p4)

    # Top Offset Loop Leg <13> & <14>
    p5 = (p4[0] + 30.0 * u150[0], p4[1] + 30.0 * u150[1])
    builder.add_line(p4[0], p4[1], p5[0], p5[1], "PIPE", 0.53)
    builder.add_text((p4[0] + p5[0]) / 2, (p4[1] + p5[0]) / 2 + 4.0, "<13> [1]", 2.35, "LABEL", rotation=30, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p4, "p2": p5, "label": "359", "offset": 10.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_text(p5[0] - 10.0, p5[1] + 8.0, "EL +104593", 2.25, "LABEL", bold=True)

    # Diagonal Run <15>
    p6 = (p5[0] + 50.0 * math.cos(math.radians(30.0)), p5[1] - 50.0 * math.sin(math.radians(30.0)))
    builder.add_line(p5[0], p5[1], p6[0], p6[1], "PIPE", 0.53)
    builder.add_text((p5[0] + p6[0]) / 2, (p5[1] + p6[1]) / 2 + 4.0, "<15> [1]", 2.35, "LABEL", bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p5, "p2": p6, "label": "1017", "offset": 10.0, "oblique_angle": 150.0, "layer": "DIM"
    })

    # Lower Tail Leg <16>
    p7 = (p6[0] + 15.0, p6[1] - 15.0)
    builder.add_line(p6[0], p6[1], p7[0], p7[1], "PIPE", 0.53)
    builder.add_text(p7[0] + 5.0, p7[1] - 5.0, "<16> [1]\nCONN. TO 418-T-102B/F\nE 678505 N 602352 EL +104450", 2.0, "LABEL", bold=True)
    builder.entities.append({
        "kind": "dimension", "p1": p6, "p2": p7, "label": "305", "offset": -8.0, "oblique_angle": 30.0, "layer": "DIM"
    })

    # 5. Export CAD Deliverables
    builder.export_dxf()
    builder.compile_dwg_via_accoreconsole()

    print(f"✅ Generated deliverables for Page 106: {builder.dxf_path}")


if __name__ == "__main__":
    main()
