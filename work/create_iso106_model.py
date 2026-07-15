"""
ISO 106 – 2"-WNA-418-1401-A82Y-G  SHEET 2 OF 2
Topology traced from png_pages/page_106.png

Key orientation from the source image:
  - CONT. FROM DRG 1 is at the RIGHT side
  - <9> runs LEFT from DRG 1 along the 210° isometric axis (going lower-left)
  - Junction near center: downward branch goes to CONT. ON ...
  - From junction, <10> goes UP, then <11> goes up-right along 30°
  - <12> is a tall vertical riser going UP
  - At top, <13> branches upper-left (150°), <14> weldolet branch right
  - <15> runs RIGHT along 330° to CONN. TO 418-T-102B/F
  - <16> final tail segment
"""
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

    # ── 1. Title Block & Sheet Frame ──────────────────────────────────────
    builder.add_title_block(
        line_number=spec["line_number"],
        sheet_number=spec["sheet_number"],
        drafter="RAM GAWAS",
        drawing_date="15.7.26",
        revision=spec["revision"],
    )

    # ── 2. Fabrication Materials BOM Table (Upper-Left) ───────────────────
    bom_w = [8.0, 68.0, 16.0, 33.0, 10.0]
    bom_rows = [
        ["PT", "COMPONENT DESCRIPTION", "N.S.", "ITEM CODE", "QTY"],
        ["NO", "", "(INS)", "", ""],
    ]
    for item in spec["bom_items"]:
        bom_rows.append([
            str(item["pt_no"]),
            item["description"],
            item["nominal_size"],
            item["item_code"],
            item["qty"],
        ])
    builder.add_table(15.0, 380.0, bom_w, 4.8, bom_rows, font_size=2.0)

    # ── 3. Cut Pipe Length Table (Left, below BOM) ────────────────────────
    cut_w = [18.0, 25.0, 20.0, 18.0, 25.0, 20.0]
    cut_rows = [
        ["PIECE", "CUT", "N.S.", "PIECE", "CUT", "N.S."],
        ["NO", "LENGTH", "(INS)", "NO", "LENGTH", "(INS)"],
    ]
    cuts = spec["cut_lengths"]
    half = (len(cuts) + 1) // 2
    for i in range(half):
        left = cuts[i]
        if i + half < len(cuts):
            right = cuts[i + half]
            cut_rows.append([
                left["piece"], str(left["cut_length_mm"]), left["pipe_size"],
                right["piece"], str(right["cut_length_mm"]), right["pipe_size"],
            ])
        else:
            cut_rows.append([
                left["piece"], str(left["cut_length_mm"]), left["pipe_size"],
                "", "", "",
            ])
    builder.add_table(15.0, 290.0, cut_w, 5.0, cut_rows, font_size=2.0)

    # ── 4. Isometric Topology ─────────────────────────────────────────────
    # Unit vectors for isometric axes
    cos30 = math.cos(math.radians(30))
    sin30 = math.sin(math.radians(30))
    # 30°  direction: right-up
    u30  = ( cos30,  sin30)
    # 150° direction: left-up
    u150 = (-cos30,  sin30)
    # 210° direction: left-down (opposite of 30°)
    u210 = (-cos30, -sin30)
    # 330° direction: right-down (opposite of 150°)
    u330 = ( cos30, -sin30)

    # ─── Key anchor: CONT. FROM DRG 1 (right side of drawing) ───────────
    p_drg1 = (370.0, 230.0)
    builder.add_text(p_drg1[0] + 3.0, p_drg1[1] + 2.0, "CONT. FROM", 2.25, "LABEL", bold=True)
    builder.add_text(p_drg1[0] + 3.0, p_drg1[1] - 3.0, "DRG 1", 2.25, "LABEL", bold=True)
    builder.add_balloon(p_drg1[0] + 10, p_drg1[1] + 10, "13")

    # ─── Segment <9>: Long run going LEFT from DRG 1 along 210° axis ────
    # Scale: 6351mm fabrication → 150 drawing units
    s9_len = 150.0
    p_junc = (p_drg1[0] + s9_len * u210[0], p_drg1[1] + s9_len * u210[1])
    # p_junc ≈ (240.1, 155.0)

    builder.add_line(p_drg1[0], p_drg1[1], p_junc[0], p_junc[1], "PIPE", 0.53)
    # Inline pipe label
    mid9 = ((p_drg1[0] + p_junc[0]) / 2, (p_drg1[1] + p_junc[1]) / 2)
    builder.add_text(mid9[0] + 3, mid9[1] + 4, '<9> [1]', 2.35, "LABEL", rotation=30, bold=True, align="center")
    builder.add_text(mid9[0] + 3, mid9[1] - 4, '2"NS', 2.25, "LABEL", rotation=30, bold=True, align="center")
    # Dimension
    builder.entities.append({
        "kind": "dimension", "p1": p_junc, "p2": p_drg1,
        "label": "6351", "offset": -12.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    # Inline dim 6250 text
    builder.add_text(mid9[0] - 15, mid9[1] - 12, "6250", 2.0, "DIM")
    builder.add_balloon(p_drg1[0] - 15, p_drg1[1] - 6, "20")

    # ─── Junction balloons at left end of <9> ────────────────────────────
    builder.add_balloon(p_junc[0] - 6, p_junc[1] - 12, "24")

    # ─── Downward continuation from junction to CONT. ON ... ─────────────
    # Runs down along 210° axis from junction (small branch)
    p_cont_on_mid = (p_junc[0] + 25.0 * u210[0], p_junc[1] + 25.0 * u210[1])
    # Then vertical drop
    p_cont_on = (p_cont_on_mid[0], p_cont_on_mid[1] - 30.0)
    builder.add_line(p_junc[0], p_junc[1], p_cont_on_mid[0], p_cont_on_mid[1], "PIPE", 0.53)
    builder.add_line(p_cont_on_mid[0], p_cont_on_mid[1], p_cont_on[0], p_cont_on[1], "PIPE", 0.53)
    # 530 dim along this branch
    builder.entities.append({
        "kind": "dimension", "p1": p_junc, "p2": p_cont_on,
        "label": "530", "offset": -10.0, "oblique_angle": 150.0, "layer": "DIM"
    })
    builder.add_text(p_cont_on[0] - 5.0, p_cont_on[1] - 6.0, "<10> [1]", 2.35, "LABEL", rotation=90, bold=True, align="center")

    # CONT. ON label
    builder.add_text(p_cont_on[0] - 50.0, p_cont_on[1] - 3.0, "CONT. ON", 2.0, "LABEL", bold=True)
    builder.add_text(p_cont_on[0] - 50.0, p_cont_on[1] - 7.0, '2"-WNA-418-1402-A82Y-G', 2.0, "LABEL", bold=True)
    builder.add_text(p_cont_on[0] - 50.0, p_cont_on[1] - 11.0, "E 676884", 2.0, "LABEL", bold=True)
    builder.add_text(p_cont_on[0] - 50.0, p_cont_on[1] - 15.0, "N 603047", 2.0, "LABEL", bold=True)
    builder.add_text(p_cont_on[0] - 50.0, p_cont_on[1] - 19.0, "EL +102230", 2.0, "LABEL", bold=True)
    builder.add_balloon(p_cont_on[0] + 8, p_cont_on[1] - 4, "23")
    builder.add_balloon(p_cont_on[0] - 8, p_cont_on[1] - 10, "22")
    # Inline 2"x2"NS and EL labels
    builder.add_text(p_cont_on[0] - 25.0, p_cont_on[1] + 6.0, '2"x2"NS', 2.0, "LABEL", bold=True)
    builder.add_text(p_cont_on[0] - 25.0, p_cont_on[1] + 2.0, 'EL +102230', 2.0, "LABEL", bold=True)
    # Dim 172 & 775
    builder.entities.append({
        "kind": "dimension", "p1": p_cont_on_mid, "p2": p_cont_on,
        "label": "400", "offset": 10.0, "oblique_angle": 150.0, "layer": "DIM"
    })

    # ─── From junction upward: <10> goes UP along 90° vertical ───────────
    p_up1 = (p_junc[0], p_junc[1] + 40.0)
    builder.add_line(p_junc[0], p_junc[1], p_up1[0], p_up1[1], "PIPE", 0.53)

    # ─── <11> from p_up1 goes UP-RIGHT along 30° axis ───────────────────
    s11_len = 40.0
    p_11end = (p_up1[0] + s11_len * u30[0], p_up1[1] + s11_len * u30[1])
    builder.add_line(p_up1[0], p_up1[1], p_11end[0], p_11end[1], "PIPE", 0.53)
    mid11 = ((p_up1[0] + p_11end[0]) / 2, (p_up1[1] + p_11end[1]) / 2)
    builder.add_text(mid11[0] - 8.0, mid11[1] + 3.0, "<11> [1]", 2.35, "LABEL", rotation=30, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_up1, "p2": p_11end,
        "label": "1441", "offset": -10.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    builder.add_balloon(p_up1[0] - 8, p_up1[1] + 4, "25")

    # ─── <12> tall vertical riser going UP from p_11end ──────────────────
    s12_len = 130.0  # scaled for 1810mm
    p_12top = (p_11end[0], p_11end[1] + s12_len)
    builder.add_line(p_11end[0], p_11end[1], p_12top[0], p_12top[1], "PIPE", 0.53)
    builder.add_text(p_11end[0] - 8.0, (p_11end[1] + p_12top[1]) / 2, "<12> [1]", 2.35, "LABEL", rotation=90, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_11end, "p2": p_12top,
        "label": "1810", "offset": -10.0, "oblique_angle": 150.0, "layer": "DIM"
    })
    builder.add_balloon(p_11end[0] - 8, p_11end[1] + 15, "26")
    builder.add_balloon(p_12top[0] - 8, p_12top[1] - 10, "27")

    # ─── <13> from p_12top goes UP-LEFT along 150° axis ──────────────────
    s13_len = 25.0  # scaled for 359mm
    p_13end = (p_12top[0] + s13_len * u150[0], p_12top[1] + s13_len * u150[1])
    builder.add_line(p_12top[0], p_12top[1], p_13end[0], p_13end[1], "PIPE", 0.53)
    builder.add_text(p_13end[0] - 5.0, p_13end[1] + 5.0, "<13> [1]", 2.35, "LABEL", rotation=150, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_12top, "p2": p_13end,
        "label": "359", "offset": 10.0, "oblique_angle": 150.0, "layer": "DIM"
    })
    # EL label and tags at top-left
    builder.add_text(p_13end[0] - 35.0, p_13end[1] + 2.0, "EL +104593", 2.25, "LABEL", bold=True)
    builder.add_balloon(p_13end[0] - 8, p_13end[1] - 4, "28")
    builder.add_balloon(p_13end[0] + 8, p_13end[1] + 4, "29")

    # ─── Top spindle labels near balloon 18, E9 ──────────────────────────
    builder.add_text(p_13end[0] - 10, p_13end[1] + 15.0, "SPINDLE W 12.99 N", 2.0, "LABEL", bold=True)
    builder.add_balloon(p_13end[0] - 5, p_13end[1] + 12, "18")
    builder.add_text(p_13end[0] + 15, p_13end[1] + 16.0, "E9", 2.0, "LABEL", bold=True)
    # F8 G11 B14 tags
    builder.add_text(p_13end[0] - 5, p_13end[1] + 8.0, "F8 G11 B14", 1.8, "LABEL", bold=True)

    # ─── <14> weldolet branch from top of riser, going RIGHT (30° axis) ──
    # Branch point is midway along <13>
    p_branch = (p_12top[0] + 10.0 * u150[0], p_12top[1] + 10.0 * u150[1])
    p_14end = (p_branch[0] + 12.0 * u30[0], p_branch[1] + 12.0 * u30[1])
    builder.add_line(p_branch[0], p_branch[1], p_14end[0], p_14end[1], "PIPE", 0.35)
    builder.add_text(p_14end[0] + 5.0, p_14end[1] + 5.0, '<14> [2]', 2.0, "LABEL", bold=True)
    builder.add_text(p_14end[0] + 5.0, p_14end[1] + 1.0, '118', 2.0, "DIM")
    builder.add_text(p_14end[0] + 5.0, p_14end[1] - 3.0, '2"x3/4"NS', 2.0, "LABEL", bold=True)
    builder.add_balloon(p_14end[0] + 5, p_14end[1] + 12, "32")
    # G11 B14 tag near vent
    builder.add_text(p_14end[0] + 15, p_14end[1] + 8, "G11 B14", 1.8, "LABEL", bold=True)

    # ─── F7 G10 B12 component tag on riser ───────────────────────────────
    builder.add_text(p_12top[0] + 12, p_12top[1] + 4.0, "F7 G10 B12", 1.8, "LABEL", bold=True)

    # ─── From p_12top, <15> goes RIGHT along 330° axis ───────────────────
    # Toward CONN. TO 418-T-102B/F
    s15_len = 70.0  # scaled for 1017mm
    p_15end = (p_12top[0] + s15_len * u330[0], p_12top[1] + s15_len * u330[1])
    builder.add_line(p_12top[0], p_12top[1], p_15end[0], p_15end[1], "PIPE", 0.53)
    mid15 = ((p_12top[0] + p_15end[0]) / 2, (p_12top[1] + p_15end[1]) / 2)
    builder.add_text(mid15[0] + 3, mid15[1] + 5, "<15> [1]", 2.35, "LABEL", rotation=-30, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_12top, "p2": p_15end,
        "label": "1017", "offset": 12.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    # SPINDLE W 12.99 N label below <15>
    builder.add_text(mid15[0] - 30, mid15[1] - 8, "SPINDLE W 12.99 N", 2.0, "LABEL", bold=True)
    builder.add_balloon(mid15[0], mid15[1] - 6, "15")
    builder.add_balloon(p_15end[0] - 8, p_15end[1] + 4, "34")

    # ─── <16> from p_15end, short run going DOWN (vertical) ─────────────
    s16_len = 22.0  # scaled for 305mm
    p_16end = (p_15end[0], p_15end[1] - s16_len)
    builder.add_line(p_15end[0], p_15end[1], p_16end[0], p_16end[1], "PIPE", 0.53)
    builder.add_text(p_16end[0] + 5, (p_15end[1] + p_16end[1]) / 2, "<16> [1]", 2.35, "LABEL", rotation=90, bold=True, align="center")
    builder.entities.append({
        "kind": "dimension", "p1": p_15end, "p2": p_16end,
        "label": "305", "offset": 10.0, "oblique_angle": 30.0, "layer": "DIM"
    })
    # Dim 313 also visible
    builder.add_text(p_16end[0] + 15, p_16end[1] + 14, "313", 2.0, "DIM")

    # ─── CONN. TO 418-T-102B/F label (right side) ─────────────────────────
    builder.add_text(p_16end[0] + 12, p_16end[1] + 4, "CONN. TO", 2.25, "LABEL", bold=True)
    builder.add_text(p_16end[0] + 12, p_16end[1] + 0, "418-T-102B/F", 2.25, "LABEL", bold=True)
    builder.add_text(p_16end[0] + 12, p_16end[1] - 4, "E 678505", 2.0, "LABEL", bold=True)
    builder.add_text(p_16end[0] + 12, p_16end[1] - 8, "N 602352", 2.0, "LABEL", bold=True)
    builder.add_text(p_16end[0] + 12, p_16end[1] - 12, "EL +104450", 2.0, "LABEL", bold=True)
    builder.add_text(p_16end[0] + 4, p_16end[1] - 4, "F7 G10 B13", 1.8, "LABEL", bold=True)
    builder.add_balloon(p_15end[0] + 8, p_15end[1] + 4, "33")
    builder.add_balloon(p_16end[0] + 4, p_16end[1] + 8, "36")
    builder.add_balloon(p_16end[0] - 6, p_16end[1] - 4, "35")

    # ─── Additional items near junction: short horizontal runs ───────────
    # 71, 140 dim between junction right branch
    # Elbow connection dimensions
    p_right = (p_junc[0] + 25.0, p_junc[1])
    builder.add_line(p_junc[0], p_junc[1], p_right[0], p_right[1], "PIPE", 0.35)
    builder.entities.append({
        "kind": "dimension", "p1": p_junc, "p2": p_right,
        "label": "71", "offset": 8.0, "oblique_angle": 30.0, "layer": "DIM"
    })

    # ─── Balloon 21 (continuation junction), 63 item ─────────────────────
    builder.add_text(p_cont_on[0] - 12, p_cont_on[1] + 20, "63", 1.8, "LABEL", bold=True)
    builder.add_balloon(p_cont_on[0] - 4, p_cont_on[1] + 14, "21")

    # ─── CONT. ON 2"-WNA-418-1401-1-A82Y-G lower-left ────────────────────
    p_cont1 = (p_cont_on[0] - 10, p_cont_on[1] - 35.0)
    builder.add_text(p_cont1[0] - 30, p_cont1[1] + 8.0, "CONT. ON", 2.25, "LABEL", bold=True)
    builder.add_text(p_cont1[0] - 30, p_cont1[1] + 4.0, '2"-WNA-418-1401-1-A82Y-G', 2.0, "LABEL", bold=True)
    builder.add_text(p_cont1[0] - 30, p_cont1[1] + 0.0, "E 676931  N 602970", 2.0, "LABEL", bold=True)
    builder.add_text(p_cont1[0] - 30, p_cont1[1] - 4.0, "EL +101830", 2.0, "LABEL", bold=True)
    builder.add_line(p_cont_on[0], p_cont_on[1], p_cont1[0], p_cont1[1], "PIPE", 0.53)
    builder.add_balloon(p_cont1[0] + 4, p_cont1[1] + 4, "20")

    # ─── Valve items near junction ────────────────────────────────────────
    # 2"NS label on vertical run
    builder.add_text(p_cont_on[0] + 8, p_cont_on[1] + 10, '2"NS', 2.0, "LABEL", rotation=90, bold=True)

    # ─── F7 G10 B13 near p_15end / connection area ───────────────────────
    # 30, 39 dimension marks near right-side connection
    builder.entities.append({
        "kind": "dimension", "p1": (p_16end[0] - 10, p_16end[1]),
        "p2": (p_16end[0] + 10, p_16end[1]),
        "label": "305", "offset": -8.0, "oblique_angle": 30.0, "layer": "DIM"
    })

    # ─── Balloons 30, 31, etc. for flange components ─────────────────────
    builder.add_balloon(p_12top[0] + 4, p_12top[1] + 12, "30")
    builder.add_balloon(p_11end[0] + 10, p_11end[1] + 4, "31")

    # ── 5. Export CAD Deliverables ────────────────────────────────────────
    builder.export_dxf()
    builder.export_pdf_and_png()
    builder.compile_dwg_via_accoreconsole()

    print(f"✅ Page 106 deliverables generated with corrected topology: {builder.dxf_path}")


if __name__ == "__main__":
    main()
