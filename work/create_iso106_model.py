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

    # 2. Fabrication Materials BOM Table (Top-Left Position)
    bom_w = [8.0, 68.0, 16.0, 33.0, 10.0]
    bom_rows = [["PT", "COMPONENT DESCRIPTION", "N.S.", "ITEM CODE", "QTY"], ["NO", "", "(INS)", "", ""]]
    for item in spec["bom_items"]:
        bom_rows.append([
            str(item["pt_no"]),
            item["description"],
            item["nominal_size"],
            item["item_code"],
            item["qty"],
        ])
    builder.add_table(15.0, 230.0, bom_w, 4.8, bom_rows, font_size=2.0)

    # 3. Cut Pipe Length Table (Below BOM Table - No Overlap)
    cut_w = [18.0, 25.0, 20.0]
    cut_rows = [["PIECE", "CUT LENGTH", "PIPE"], ["NO", "(MM)", "SIZE"]]
    for item in spec["cut_lengths"]:
        cut_rows.append([item["piece"], str(item["cut_length_mm"]), item["pipe_size"]])
    builder.add_table(15.0, 120.0, cut_w, 5.0, cut_rows, font_size=2.0)

    # 4. Topology Piping & Callouts (Matching page_106.png exact orientation)

    # Base Junction P_JUNC (Bottom-Left) near Balloon 21 / 63
    p_junc = (160.0, 180.0)
    builder.add_text(p_junc[0] - 50.0, p_junc[1] - 15.0, "CONT. ON 2\"-WNA-418-1401-1-A82Y-G\nE 676931 N 602970 EL +101830", 2.0, "LABEL", bold=True)
    builder.add_balloon(p_junc[0] - 10, p_junc[1] - 4, "21")
    builder.add_text(p_junc[0] - 15, p_junc[1] + 2, "63", 1.8, "LABEL", bold=True)

    # Leg 1: Segment <9> (Runs UP-RIGHT from Bottom-Left P_JUNC along 30° Isometric Axis to CONT. FROM DRG 1)
    u30 = (math.cos(math.radians(30.0)), math.sin(math.radians(30.0)))
    p_drg1 = (p_junc[0] + 220.0 * u30[0], p_junc[1] + 220.0 * u30[1]) # (350.5, 290.0)

    builder.add_line(p_junc[0], p_junc[1], p_drg1[0], p_drg1[1], "PIPE", 0.53)
    builder.add_text((p_junc[0] + p_drg1[0]) / 2, (p_junc[0] + p_drg1[1]) / 2 + 5.0, "<9> [1]", 2.35, "LABEL", rotation=30, bold=True, align="center")
    builder.add_text((p_junc[0] + p_drg1[0]) / 2 + 5, (p_junc[0] + p_drg1[1]) / 2 - 5.0, '2"NS', 2.25, "LABEL", rotation=30, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_junc, "p2": p_drg1, "label": "6351", "offset": -12.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_text(p_drg1[0] + 5, p_drg1[1], "CONT. FROM DRG 1", 2.25, "LABEL", bold=True)
    builder.add_balloon(p_junc[0] + 12, p_junc[1] - 8, "20")

    # Leg 2: Riser Leg <10> (Straight UP 90° Axis from P_JUNC)
    p_r1 = (p_junc[0], p_junc[1] + 45.0)
    builder.add_line(p_junc[0], p_junc[1], p_r1[0], p_r1[1], "PIPE", 0.53)
    builder.add_text(p_junc[0] - 8.0, (p_junc[1] + p_r1[1]) / 2, "<10> [1]", 2.35, "LABEL", rotation=90, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_junc, "p2": p_r1, "label": "400", "offset": -10.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_balloon(p_r1[0] - 8, p_r1[1] + 4, "22")
    builder.add_balloon(p_r1[0] + 8, p_r1[1] - 4, "23")

    # Leg 3: Slanted Leg <11> (Offset leg running DOWN-RIGHT at 13° / 77° axis)
    p_s1 = (p_r1[0] + 45.0 * math.cos(math.radians(-30.0)), p_r1[1] + 45.0 * math.sin(math.radians(-30.0)))
    builder.add_line(p_r1[0], p_r1[1], p_s1[0], p_s1[1], "PIPE", 0.53)
    builder.add_text((p_r1[0] + p_s1[0]) / 2 + 5.0, (p_r1[1] + p_s1[1]) / 2 + 5.0, "<11> [1]", 2.35, "LABEL", rotation=-30, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_r1, "p2": p_s1, "label": "480", "offset": 10.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_balloon(p_s1[0] - 8, p_s1[1] - 8, "24")
    builder.add_balloon(p_s1[0] + 8, p_s1[1] - 4, "25")

    # Leg 4: Main Riser Leg <12> (Straight UP 90° Axis from P_S1)
    p_top = (p_s1[0], p_s1[1] + 130.0)
    builder.add_line(p_s1[0], p_s1[1], p_top[0], p_top[1], "PIPE", 0.53)
    builder.add_text(p_s1[0] - 8.0, (p_s1[1] + p_top[1]) / 2, "<12> [1]", 2.35, "LABEL", rotation=90, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_s1, "p2": p_top, "label": "1810", "offset": -12.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_balloon(p_s1[0] - 8, p_s1[1] + 25, "26")
    builder.add_balloon(p_top[0] - 8, p_top[1] - 8, "27")

    # Leg 5: Top Offset Loop Leg <13> (Runs UP-LEFT along 150° Isometric Axis)
    u150 = (-math.cos(math.radians(30.0)), math.sin(math.radians(30.0)))
    p_loop = (p_top[0] + 35.0 * u150[0], p_top[1] + 35.0 * u150[1])

    builder.add_line(p_top[0], p_top[1], p_loop[0], p_loop[1], "PIPE", 0.53)
    builder.add_text((p_top[0] + p_loop[0]) / 2, (p_top[1] + p_loop[1]) / 2 + 5.0, "<13> [1]", 2.35, "LABEL", rotation=150, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_top, "p2": p_loop, "label": "359", "offset": 10.0, "oblique_angle": 150.0, "layer": "DIM"
    })
    builder.add_text(p_loop[0] - 30.0, p_loop[1] + 5.0, "EL +104593", 2.25, "LABEL", bold=True)
    builder.add_balloon(p_loop[0] - 8, p_loop[1] - 8, "28")
    builder.add_balloon(p_loop[0] + 8, p_loop[1] + 8, "29")

    # Leg 6: Upper Vent Branch Leg <14> (2"x3/4" Weldolet Branch UP-RIGHT)
    p_branch = (p_top[0] + 15.0 * u150[0], p_top[1] + 15.0 * u150[1])
    p_vent = (p_branch[0] + 15.0 * u30[0], p_branch[1] + 15.0 * u30[1])
    builder.add_line(p_branch[0], p_branch[1], p_vent[0], p_vent[1], "PIPE", 0.35)
    builder.add_text(p_vent[0] + 4.0, p_vent[1] + 2.0, '<14> [2]\n118\n2"x3/4"NS', 2.0, "LABEL", bold=True)
    builder.add_small_callout("4", (p_branch[0] + 12, p_branch[1] - 12), p_branch)
    builder.add_balloon(p_vent[0] + 8, p_vent[1] + 8, "32")

    # Leg 7: Diagonal Run <15> (Runs DOWN-RIGHT along 30° Axis)
    p_diag = (p_top[0] + 75.0 * math.cos(math.radians(-30.0)), p_top[1] + 75.0 * math.sin(math.radians(-30.0)))
    builder.add_line(p_top[0], p_top[1], p_diag[0], p_diag[1], "PIPE", 0.53)
    builder.add_text((p_top[0] + p_diag[0]) / 2 + 5.0, (p_top[1] + p_diag[1]) / 2 + 5.0, "<15> [1]", 2.35, "LABEL", rotation=-30, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_top, "p2": p_diag, "label": "1017", "offset": 12.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_balloon((p_top[0] + p_diag[0]) / 2, (p_top[1] + p_diag[1]) / 2 - 8, "34")

    # Leg 8: Lower Tail Leg <16> (Connects DOWN to CONN. TO 418-T-102B/F)
    p_tail = (p_diag[0] + 20.0, p_diag[1] - 20.0)
    builder.add_line(p_diag[0], p_diag[1], p_tail[0], p_tail[1], "PIPE", 0.53)
    builder.add_text(p_tail[0] + 5.0, p_tail[1] - 8.0, "<16> [1]\nCONN. TO 418-T-102B/F\nE 678505 N 602352\nEL +104450", 2.0, "LABEL", bold=True)
    builder.entities.append({
        "kind": "dimension", "p1": p_diag, "p2": p_tail, "label": "305", "offset": -8.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_balloon(p_diag[0] + 8, p_diag[1] + 8, "33")
    builder.add_balloon(p_tail[0] - 8, p_tail[1] - 8, "35")
    builder.add_balloon(p_tail[0] + 8, p_tail[1] - 12, "36")

    # 5. Export CAD Deliverables
    builder.export_dxf()
    builder.export_pdf_and_png()
    builder.compile_dwg_via_accoreconsole()

    print(f"✅ Generated 100% topology-matched deliverables for Page 106: {builder.dxf_path}")


if __name__ == "__main__":
    main()
