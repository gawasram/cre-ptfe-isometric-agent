from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import pdfplumber
from PIL import Image
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = Path(
    "/Users/ram/Documents/Codex/2026-07-13/please-check-this/ilovepdf_extracted-pages/"
    "ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150-72.pdf"
)
SOURCE_PAGE_INDEX = 0
OUTPUT = ROOT / "outputs"
OUTPUT.mkdir(exist_ok=True)
PDF_PATH = OUTPUT / "ISO_72_PTFE.pdf"
DXF_PATH = OUTPUT / "ISO_72_PTFE.dxf"
DWG_PATH = OUTPUT / "ISO_72_PTFE.dwg"
PNG_PATH = OUTPUT / "ISO_72_PTFE.png"

MM_TO_PT = 72.0 / 25.4
PAGE_W_MM = 420.0
PAGE_H_MM = 594.0
entities: list[dict] = []

DIM_TEXT_HEIGHT = 2.1
DIM_ARROW_LENGTH = DIM_TEXT_HEIGHT
DIM_ARROW_BASE = DIM_ARROW_LENGTH / 3.0
DIM_EXT_OFFSET = DIM_TEXT_HEIGHT * 0.5
DIM_EXT_EXCEED = DIM_TEXT_HEIGHT * 0.5
DIM_TEXT_GAP = DIM_TEXT_HEIGHT * 0.4


def validate_split_source():
    if not SOURCE_PDF.is_file():
        raise FileNotFoundError(f"Split source PDF not found: {SOURCE_PDF}")
    with pdfplumber.open(SOURCE_PDF) as pdf:
        if len(pdf.pages) != 1:
            raise ValueError(f"Expected one split page, found {len(pdf.pages)}")


def add_line(x1, y1, x2, y2, layer="OBJECT", width=0.18):
    entities.append({"kind": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                     "layer": layer, "width": width})


def add_polyline(points, layer="OBJECT", width=0.18, closed=False):
    if len(points) >= 2:
        entities.append({"kind": "polyline", "points": points, "layer": layer,
                         "width": width, "closed": closed})


def add_circle(x, y, r, layer="OBJECT", width=0.18):
    entities.append({"kind": "circle", "x": x, "y": y, "r": r,
                     "layer": layer, "width": width})


def add_text(x, y, value, size=2.5, layer="TEXT", rotation=0.0,
             bold=False, align="left"):
    entities.append({"kind": "text", "x": x, "y": y, "value": str(value),
                     "size": size, "layer": layer, "rotation": rotation,
                     "bold": bold, "align": align})


def add_rect(x, y, w, h, layer="BORDER", width=0.18):
    add_polyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                 layer, width, closed=True)


def add_table(x, y, widths, row_h, rows, font_size=2.6):
    total_w = sum(widths)
    total_h = row_h * len(rows)
    add_rect(x, y, total_w, total_h, "TABLE", 0.25)
    cx = x
    for width in widths[:-1]:
        cx += width
        add_line(cx, y, cx, y + total_h, "TABLE", 0.25)
    for index in range(1, len(rows)):
        add_line(x, y + index * row_h, x + total_w, y + index * row_h, "TABLE", 0.25)
    for visual_row, row in enumerate(reversed(rows)):
        cy = y + (visual_row + 0.30) * row_h
        rx = x
        for c_idx, cell in enumerate(row):
            is_bold = (visual_row == len(rows) - 1)
            cell_w = widths[c_idx]
            if c_idx in (0, len(row) - 1):
                add_text(rx + cell_w / 2.0, cy, cell, font_size, "TABLE",
                         bold=is_bold, align="center")
            else:
                add_text(rx + 2.0, cy, cell, font_size, "TABLE", bold=is_bold, align="left")
            rx += cell_w


def add_balloon(x, y, label, radius=2.15):
    add_circle(x, y, radius, "CALLOUT", 0.35)
    add_text(x, y - 0.90, str(label), 2.2, "CALLOUT", bold=True, align="center")


def add_small_callout(number, bubble, target):
    bx, by = bubble
    tx, ty = target
    add_line(bx, by, tx, ty, "CALLOUT", 0.20)
    add_circle(bx, by, 2.15, "CALLOUT", 0.35)
    add_text(bx, by - 0.90, str(number), 1.80, "CALLOUT", bold=True, align="center")


def add_flange(x, y, angle_deg, length=6.0):
    rad = math.radians(angle_deg)
    if math.isclose(abs(angle_deg % 180.0), 90.0, abs_tol=1.0):
        fx = math.cos(math.radians(30.0))
        fy = math.sin(math.radians(30.0))
    else:
        fx = -math.sin(rad)
        fy = math.cos(rad)

    x1 = x - fx * (length / 2.0)
    y1 = y - fy * (length / 2.0)
    x2 = x + fx * (length / 2.0)
    y2 = y + fy * (length / 2.0)
    add_line(x1, y1, x2, y2, "COMPONENT", 0.35)


def add_valve_ball(center, angle_deg, draw_length=12.0, ball_r=2.5):
    cx, cy = center
    rad = math.radians(angle_deg)
    ux, uy = math.cos(rad), math.sin(rad)
    nx, ny = -uy, ux

    p1 = (cx - ux * (draw_length / 2), cy - uy * (draw_length / 2))
    p2 = (cx + ux * (draw_length / 2), cy + uy * (draw_length / 2))

    flange_len = 5.0
    add_line(p1[0] - nx * flange_len / 2, p1[1] - ny * flange_len / 2,
             p1[0] + nx * flange_len / 2, p1[1] + ny * flange_len / 2, "COMPONENT", 0.35)
    add_line(p2[0] - nx * flange_len / 2, p2[1] - ny * flange_len / 2,
             p2[0] + nx * flange_len / 2, p2[1] + ny * flange_len / 2, "COMPONENT", 0.35)

    add_line(p1[0] - nx * flange_len / 2, p1[1] - ny * flange_len / 2, cx, cy, "COMPONENT", 0.35)
    add_line(p1[0] + nx * flange_len / 2, p1[1] + ny * flange_len / 2, cx, cy, "COMPONENT", 0.35)
    add_line(p2[0] - nx * flange_len / 2, p2[1] - ny * flange_len / 2, cx, cy, "COMPONENT", 0.35)
    add_line(p2[0] + nx * flange_len / 2, p2[1] + ny * flange_len / 2, cx, cy, "COMPONENT", 0.35)

    add_circle(cx, cy, ball_r, "COMPONENT", 0.35)
    return p1, p2


def draw_pipe(p1, p2, width=0.53):
    add_line(p1[0], p1[1], p2[0], p2[1], "PIPE", width)


def add_single_dimension(p1, p2, label, offset, oblique_angle=None):
    add_dimension_pair(p1, p2, (str(label),), offsets=(offset,), oblique_angle=oblique_angle)


def get_default_oblique_angle(p1, p2):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    angle = (math.degrees(math.atan2(dy, dx)) % 180.0)
    if math.isclose(angle, 90.0, abs_tol=5.0):
        return 30.0
    elif math.isclose(angle, 30.0, abs_tol=5.0) or math.isclose(angle, 210.0, abs_tol=5.0):
        return 150.0
    elif math.isclose(angle, 150.0, abs_tol=5.0) or math.isclose(angle, 330.0, abs_tol=5.0):
        return 30.0
    return 30.0


def add_dimension_pair(p1, p2, labels, offsets=(6.0, 11.0), oblique_angle=None):
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return
    if oblique_angle is None:
        oblique_angle = get_default_oblique_angle(p1, p2)
    for label, offset in zip(labels, offsets):
        entities.append({
            "kind": "dimension",
            "p1": (float(x1), float(y1)),
            "p2": (float(x2), float(y2)),
            "label": str(label),
            "offset": float(offset),
            "oblique_angle": float(oblique_angle),
            "layer": "DIM",
            "width": 0.20,
        })


def _readable_dimension_angle(angle_deg):
    angle = ((angle_deg + 180.0) % 360.0) - 180.0
    if angle > 90.0:
        angle -= 180.0
    elif angle <= -90.0:
        angle += 180.0
    return angle


def _dimension_primitives(entity):
    p1 = entity["p1"]
    p2 = entity["p2"]
    offset = entity["offset"]
    oblique_angle = entity.get("oblique_angle", 0.0)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return []

    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux

    rad = math.radians(oblique_angle)
    ex, ey = math.cos(rad), math.sin(rad)
    dot = ex * nx + ey * ny
    if abs(dot) < 1e-4:
        ex, ey = nx, ny
        dot = 1.0

    shift = offset / dot
    ax, ay = p1[0] + ex * shift, p1[1] + ey * shift
    bx, by = p2[0] + ex * shift, p2[1] + ey * shift

    ext_len = DIM_EXT_EXCEED
    ext_off = DIM_EXT_OFFSET
    e_len = math.hypot(ex, ey)
    ev_x, ev_y = (ex / e_len, ey / e_len) if e_len > 0 else (nx, ny)
    if offset < 0:
        ev_x, ev_y = -ev_x, -ev_y

    result = [
        {
            "kind": "line", "x1": ax, "y1": ay, "x2": bx, "y2": by,
            "layer": "DIM", "width": 0.20,
        },
        {
            "kind": "line",
            "x1": p1[0] + ev_x * ext_off,
            "y1": p1[1] + ev_y * ext_off,
            "x2": ax + ev_x * ext_len,
            "y2": ay + ev_y * ext_len,
            "layer": "DIM", "width": 0.20,
        },
        {
            "kind": "line",
            "x1": p2[0] + ev_x * ext_off,
            "y1": p2[1] + ev_y * ext_off,
            "x2": bx + ev_x * ext_len,
            "y2": by + ev_y * ext_len,
            "layer": "DIM", "width": 0.20,
        },
    ]

    half_base = DIM_ARROW_BASE / 2.0
    for tip, inward in (((ax, ay), (ux, uy)), ((bx, by), (-ux, -uy))):
        base_center = (
            tip[0] + inward[0] * DIM_ARROW_LENGTH,
            tip[1] + inward[1] * DIM_ARROW_LENGTH,
        )
        result.append({
            "kind": "solid",
            "points": [
                tip,
                (base_center[0] + nx * half_base, base_center[1] + ny * half_base),
                (base_center[0] - nx * half_base, base_center[1] - ny * half_base),
            ],
            "layer": "DIM",
            "width": 0.50,
        })

    angle = _readable_dimension_angle(math.degrees(math.atan2(dy, dx)))
    side = 1.0 if offset >= 0 else -1.0
    result.append({
        "kind": "text",
        "x": (ax + bx) / 2.0 + nx * side * DIM_TEXT_GAP,
        "y": (ay + by) / 2.0 + ny * side * DIM_TEXT_GAP,
        "value": entity["label"],
        "size": DIM_TEXT_HEIGHT,
        "layer": "DIM",
        "rotation": angle,
        "bold": False,
        "align": "center",
    })
    return result


def build_entities():
    # Outer Border
    add_rect(8, 8, 404, 578, "BORDER", 0.35)
    add_rect(11, 11, 398, 572, "BORDER", 0.20)
    add_rect(11, 568, 112, 13, "BORDER", 0.20)
    add_text(67, 571.8, "IF IN ANY DOUBT PLS ASK", 3.75, "TITLE", bold=True, align="center")
    add_rect(309, 568, 100, 13, "BORDER", 0.20)
    add_text(359, 571.8, "DO NOT SCALE", 3.75, "TITLE", bold=True, align="center")

    # Title Block (Bottom-Right)
    tx, ty, tw, th = 215, 12, 190, 79
    add_rect(tx, ty, tw, th, "BORDER", 0.35)
    for y in [80, 69, 58, 43, 22]:
        add_line(tx, y, tx + tw, y, "BORDER", 0.20)
    add_text(tx + tw / 2, 83.0, "CORROSION RESISTANT EQUIPMENT PVT LTD", 4.7, "COMPANY", bold=True, align="center")
    add_text(tx + 2, 72.2, "CUSTOMER: ENGINEERS INDIA LTD, NEW DELHI", 2.8, "TITLE", bold=True)
    add_text(tx + 2, 61.2, "PROJECT: MIL PROJECT, TNT PLANT, HEF KHADKI, PUNE", 2.6, "TITLE", bold=True)

    grid_right = 287
    add_line(grid_right, 22, grid_right, 58, "BORDER", 0.20)
    for y in [31, 40, 49]:
        add_line(tx, y, grid_right, y, "BORDER", 0.20)
    for x in [235, 260, 272]:
        add_line(x, 22, x, 58, "BORDER", 0.20)
    add_text(247.5, 52.2, "NAME", 2.3, "TITLE", bold=True, align="center")
    add_text(266, 52.2, "SIGN", 2.3, "TITLE", bold=True, align="center")
    add_text(279.5, 52.2, "DATE", 2.3, "TITLE", bold=True, align="center")
    for y, role in [(43.2, "DRAN"), (34.2, "CHK"), (25.2, "APPD.")]:
        add_text(225, y, role, 2.4, "TITLE", bold=True, align="center")
    add_text(247.5, 43.2, "RAM GAWAS", 2.0, "TITLE", align="center")
    add_text(279.5, 43.2, "15.7.26", 2.0, "TITLE", align="center")

    add_text(292, 48.5, "LINE NO.", 3.1, "HIGHLIGHT", bold=True)
    add_text(292, 35.2, '1"-SNA-424-1502-A82Y-D', 2.9, "HIGHLIGHT", bold=True)

    for x in [265, 305, 375]:
        add_line(x, 12, x, 22, "BORDER", 0.20)
    add_text(240, 15.0, "SCALE=NTS", 2.7, "TITLE", bold=True, align="center")

    # Projection Symbol
    add_line(270, 15, 280, 17, "SYMBOL", 0.20)
    add_line(270, 19, 280, 17, "SYMBOL", 0.20)
    add_line(270, 15, 270, 19, "SYMBOL", 0.20)
    add_circle(293, 17, 3.4, "SYMBOL", 0.20)
    add_circle(293, 17, 1.9, "SYMBOL", 0.20)
    add_line(287.5, 17, 298.5, 17, "CENTER", 0.20)
    add_line(293, 11.5, 293, 22.5, "CENTER", 0.20)

    add_text(340, 15.0, "SHEET NO. 1 OF 1", 2.7, "TITLE", bold=True, align="center")
    add_text(390, 18.0, "REV.", 2.3, "TITLE", bold=True, align="center")
    add_line(375, 16, 405, 16, "BORDER", 0.20)
    add_text(390, 12.5, "0", 2.3, "TITLE", bold=True, align="center")

    # Revision Table (Bottom-Left)
    rx, ry, rw, rh = 15, 12, 195, 19
    add_rect(rx, ry, rw, rh, "BORDER", 0.25)
    add_line(rx, 22, rx + rw, 22, "BORDER", 0.20)
    for x in [30.5, 171.4, 182.9, 197.3]:
        add_line(x, 12, x, 31, "BORDER", 0.20)
    add_text(22.75, 15.0, "REV.", 2.7, "TITLE", bold=True, align="center")
    add_text(100.0, 15.0, "DESCRIPTION", 2.7, "TITLE", bold=True, align="center")
    add_text(177.0, 15.0, "BY", 2.5, "TITLE", bold=True, align="center")
    add_text(190.0, 15.0, "CHD.", 2.4, "TITLE", bold=True, align="center")
    add_text(204.0, 15.0, "APPD", 2.2, "TITLE", bold=True, align="center")

    # North Arrow (Top-Right)
    na_x, na_y = 370.0, 540.0
    add_rect(na_x - 12, na_y - 12, 24, 24, "BORDER", 0.35)
    add_line(na_x - 8, na_y - 8, na_x + 6, na_y + 6, "BORDER", 0.35)
    add_polyline([(na_x + 6, na_y + 6), (na_x + 1, na_y + 5), (na_x + 5, na_y + 1)], "BORDER", 0.35, closed=True)
    add_text(na_x + 2, na_y + 8, "N", 4.0, "TEXT", bold=True, align="center")

    # Cut Pipe Length Table
    cut_w = [18.0, 25.0, 20.0]
    cut_rows = [
        ["PIECE", "CUT LENGTH", "PIPE"],
        ["NO", "(MM)", "SIZE"],
        ["<1>", "10651", '1"'],
        ["<2>", "474", '1"'],
        ["<3>", "2472", '1"'],
        ["<4>", "123", '1"'],
        ["<5>", "1938", '1"'],
        ["<6>", "396", '1"'],
        ["<7>", "104", '1.1/2"'],
    ]
    add_table(15.0, 35.0, cut_w, 6.0, cut_rows, font_size=2.2)

    # Fabrication BOM Table
    bom_w = [10.0, 68.0, 18.0, 32.0, 12.0]
    bom_rows = [
        ["PT", "COMPONENT DESCRIPTION", "N.S.", "ITEM CODE", "QTY"],
        ["NO", "", "(INS)", "", ""],
        ["1", 'PIPE B-36.19 BE SEAMLESS 10S', '4"', "PI3D217Z01312ZZZZ", "0.2M"],
        ["2", 'PIPE B-36.19 BE SEAMLESS 40S', '1.1/2"', "PI3D217Z00813ZZZZ", "0.2M"],
        ["3", 'PIPE B-36.19 BE SEAMLESS 40S', '1"', "PI3D217Z00613ZZZZ", "16.1M"],
        ["4", 'REDUC.CONC B-16.9 BW 10S 40S', '4 x 2', "WUGC84ZZ013120913", "1 NO"],
        ["5", 'WELDOLET MSS-SP97 BW 10S 40S', '4 x 1.1/2', "YWSAF4ZZ013120813", "1 NO"],
        ["6", 'REDUC.CONC B-16.9 BW 40S 40S', '2 x 1', "WUGC84ZZ009130613", "1 NO"],
        ["7", 'ELBOW.90 B-16.9 BW 1.5D 40S', '1"', "WAGC84Z100613ZZZZ", "5 NO"],
        ["8", 'FLNG.WN B-16.5 150 RF/125AARH 40S', '1.1/2"', "FWCG527Z00813ZZZZ", "1 NO"],
        ["9", 'GASKET B-16.20-ANSI B16.5 SPIRAL', '1.1/2"', "GK6CF72Z008ZZZZZ", "2 NO"],
        ["10", '70 MM LONG BOLT.STUD 2 NUTS', '1/2"', "--", "8 NO"],
        ["11", 'VLV.BALL SHEET 543DR', '1.1/2"', "543DRZZZ008ZZZZZ", "1 NO"],
        ["12", 'PRESS.TRANSMETER FLANGED 150#', '1.1/2"', "--", "1 NO"],
    ]
    add_table(15.0, 85.0, bom_w, 6.0, bom_rows, font_size=2.2)

    # -------------------------------------------------------------
    # PIPE MODEL TOPOLOGY (PAGE 72)
    # -------------------------------------------------------------

    # Start Continuation Node (Top-Right)
    p0 = (340.0, 310.0)
    add_text(p0[0] + 5, p0[1] + 5, "CONT. ON 1\"-SNA-424-1502-A82Y-D\nE 676552 N 543606 EL +106217",
             2.25, "LABEL", bold=True)

    # Leg 1: Segment <1> (150° Isometric Axis down-left)
    u150 = (-math.cos(math.radians(30.0)), -math.sin(math.radians(30.0)))
    p1 = (p0[0] + 130.0 * u150[0], p0[1] + 130.0 * u150[1]) # (227.4, 245.0)

    draw_pipe(p0, p1)
    add_single_dimension(p0, p1, "10690", offset=10.0)
    add_text((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 5.0, "<1> [3]", 2.35, "LABEL", rotation=30, bold=True, align="center")
    add_text((p0[0] + p1[0]) / 2 + 5, (p0[1] + p1[1]) / 2 - 5.0, "1\"NS", 2.25, "LABEL", rotation=30, bold=True, align="center")

    # 90° Elbow at p1
    add_small_callout("7", (p1[0] - 8.0, p1[1] + 10.0), p1)

    # Leg 2: Vertical Drop Leg <2> (90° Vertical Axis down)
    p2 = (p1[0], p1[1] - 40.0) # (227.4, 205.0)
    draw_pipe(p1, p2)
    add_single_dimension(p1, p2, "550", offset=-10.0, oblique_angle=30.0)
    add_text(p1[0] + 5.0, (p1[1] + p2[1]) / 2, "<2> [3]", 2.35, "LABEL", rotation=90, bold=True, align="center")
    add_text(p2[0] + 5.0, p2[1] - 5.0, "EL +105667", 2.25, "LABEL", bold=True)

    # 90° Elbow at p2
    add_small_callout("7", (p2[0] + 12.0, p2[1] - 8.0), p2)

    # Leg 3: Segment <3> (150° Isometric Axis down-left)
    p3 = (p2[0] + 80.0 * u150[0], p2[1] + 80.0 * u150[1]) # (158.1, 165.0)
    draw_pipe(p2, p3)
    add_single_dimension(p2, p3, "2548", offset=-10.0)
    add_text((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2 + 5.0, "<3> [3]", 2.35, "LABEL", rotation=30, bold=True, align="center")

    add_text(p3[0] - 15, p3[1] - 12, "CONT. ON DRG 2", 2.25, "LABEL", bold=True)

    # Leg 4: Slanted 45° offset loop & branch manifold section
    # Pipe goes at 45° offset loop
    p4 = (p3[0] - 45.0, p3[1] + 45.0) # (113.1, 210.0)
    draw_pipe(p3, p4)

    add_single_dimension(p3, p4, "2014", offset=10.0)
    add_text((p3[0] + p4[0]) / 2, (p3[1] + p4[1]) / 2 + 5.0, "<5> [3]", 2.35, "LABEL", bold=True, align="center")
    add_text((p3[0] + p4[0]) / 2 - 10, (p3[1] + p4[1]) / 2 - 5.0, "4\"x2\"NS", 2.25, "LABEL", bold=True, align="center")

    # Vertical offset 200 mm at p4
    add_single_dimension(p4, (p4[0], p4[1] - 15.0), "200", offset=-8.0, oblique_angle=30.0)
    add_text(p4[0] - 15.0, p4[1] - 10.0, "EL +105467", 2.25, "LABEL", bold=True)

    # Branch Riser & Instrument Assembly
    branch_node = ((p3[0] + p4[0]) / 2 + 10, (p3[1] + p4[1]) / 2 + 10)
    branch_top = (branch_node[0], branch_node[1] + 35.0)
    draw_pipe(branch_node, branch_top)

    add_single_dimension(branch_node, branch_top, "434", offset=8.0, oblique_angle=30.0)
    add_text(branch_node[0] - 5.0, (branch_node[1] + branch_top[1]) / 2, "<6> [3]", 2.35, "LABEL", rotation=90, bold=True, align="center")
    add_text(branch_top[0] + 5.0, branch_top[1], "2\"x1\"NS", 2.25, "LABEL", bold=True)
    add_text(branch_top[0] + 5.0, branch_top[1] - 8.0, "EL +104754", 2.25, "LABEL", bold=True)

    # Valve & Transmitter Callout Block
    add_flange(branch_top[0], branch_top[1], 90.0)
    add_valve_ball((branch_top[0], branch_top[1] + 8.0), 90.0)
    add_small_callout("11", (branch_top[0] - 15.0, branch_top[1] + 8.0), (branch_top[0], branch_top[1] + 8.0))
    add_text(branch_top[0] - 25.0, branch_top[1] + 14.0, "F8 G9 B10 [12]", 2.2, "LABEL", bold=True)


def export_dxf():
    doc = ezdxf.new("R2018", setup=True)
    doc.units = units.MM

    layer_specs = {
        "BORDER": (7, 35),
        "TABLE": (7, 25),
        "LABEL": (7, 25),
        "TEXT": (7, 25),
        "TITLE": (7, 25),
        "COMPANY": (4, 20),
        "HIGHLIGHT": (3, 20),
        "SYMBOL": (2, 20),
        "PIPE": (4, 53),
        "DIM": (2, 20),
        "CALLOUT": (3, 35),
        "COMPONENT": (4, 50),
    }
    for name, (color, lineweight) in layer_specs.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color, lineweight=lineweight, linetype="Continuous")
    if "CENTER" not in doc.layers:
        doc.layers.add("CENTER", color=2, lineweight=20, linetype="CENTER")

    if "CRE_ARIAL_NARROW" not in doc.styles:
        doc.styles.new("CRE_ARIAL_NARROW", dxfattribs={"font": "Arial Narrow.ttf"})
    if "CRE_ARIAL_NARROW_BOLD" not in doc.styles:
        doc.styles.new("CRE_ARIAL_NARROW_BOLD", dxfattribs={"font": "Arial Narrow Bold.ttf"})
    if "CRE_ROMANS" not in doc.styles:
        doc.styles.new("CRE_ROMANS", dxfattribs={"font": "romans.shx"})

    if "CRE_PTFE_DIM" not in doc.dimstyles:
        doc.dimstyles.new("CRE_PTFE_DIM", dxfattribs={
            "dimscale": 1.0,
            "dimasz": DIM_ARROW_LENGTH,
            "dimtxt": DIM_TEXT_HEIGHT,
            "dimexo": DIM_EXT_OFFSET,
            "dimexe": DIM_EXT_EXCEED,
            "dimgap": DIM_TEXT_GAP,
            "dimtad": 1,
            "dimtofl": 1,
            "dimsoxd": 1,
            "dimtix": 0,
            "dimtih": 0,
            "dimtoh": 0,
            "dimdec": 0,
            "dimlunit": 2,
            "dimzin": 12,
            "dimtsz": 0.0,
            "dimsah": 0,
            "dimclrd": 2,
            "dimclre": 2,
            "dimclrt": 2,
            "dimlwd": 20,
            "dimlwe": 20,
            "dimtxsty": "CRE_ROMANS",
        })

    msp = doc.modelspace()

    for entity in entities:
        layer = entity.get("layer", "0")
        kind = entity["kind"]
        if kind == "line":
            e = msp.add_line((entity["x1"], entity["y1"]), (entity["x2"], entity["y2"]), dxfattribs={"layer": layer})
            e.dxf.lineweight = max(5, min(211, round(entity.get("width", 0.18) * 100)))
        elif kind == "polyline":
            e = msp.add_lwpolyline(entity["points"], close=entity.get("closed", False), dxfattribs={"layer": layer})
            e.dxf.lineweight = max(5, min(211, round(entity.get("width", 0.18) * 100)))
        elif kind == "circle":
            e = msp.add_circle((entity["x"], entity["y"]), entity["r"], dxfattribs={"layer": layer})
            e.dxf.lineweight = max(5, min(211, round(entity.get("width", 0.18) * 100)))
        elif kind == "solid":
            points = entity["points"]
            if len(points) >= 3:
                e = msp.add_solid(points[0], points[1], points[2], points[2], dxfattribs={"layer": layer})
                e.dxf.lineweight = max(5, min(211, round(entity.get("width", 0.18) * 100)))
        elif kind == "text":
            style = "CRE_ROMANS" if layer in ("CALLOUT", "DIM", "LABEL") else ("CRE_ARIAL_NARROW_BOLD" if entity.get("bold") else "CRE_ARIAL_NARROW")
            text = msp.add_text(entity["value"], dxfattribs={
                "height": entity["size"], "layer": layer,
                "rotation": entity.get("rotation", 0.0),
                "style": style,
            })
            alignment = {
                "left": TextEntityAlignment.LEFT,
                "center": TextEntityAlignment.CENTER,
                "right": TextEntityAlignment.RIGHT,
            }[entity.get("align", "left")]
            text.set_placement((entity["x"], entity["y"]), align=alignment)
        elif kind == "dimension":
            dim = msp.add_aligned_dim(
                p1=entity["p1"], p2=entity["p2"], distance=entity["offset"],
                dimstyle="CRE_PTFE_DIM",
                override={
                    "dimclrd": 2, "dimclre": 2, "dimclrt": 2, "dimtxsty": "CRE_ROMANS",
                },
            )
            dim.dimension.dxf.layer = "DIM"
            dim.dimension.dxf.lineweight = 20
            dim.dimension.dxf.text = entity["label"]
            if "oblique_angle" in entity:
                dim.dimension.dxf.oblique_angle = entity["oblique_angle"]
            dim.render()

    doc.header["$INSUNITS"] = units.MM
    paper = doc.layouts.get("Layout1")
    paper.page_setup(size=(PAGE_W_MM, PAGE_H_MM), margins=(0.0, 0.0, 0.0, 0.0), units="mm", scale=(1.0, 1.0), name="ISO_A2_PORTRAIT", device="DWG To PDF.pc3")
    vp = paper.add_viewport(center=(PAGE_W_MM / 2.0, PAGE_H_MM / 2.0), size=(PAGE_W_MM, PAGE_H_MM), view_center_point=(PAGE_W_MM / 2.0, PAGE_H_MM / 2.0), view_height=PAGE_H_MM, status=2, dxfattribs={"layer": "VIEWPORTS"})

    doc.saveas(DXF_PATH)
    print(f"Generated DXF: {DXF_PATH}")


def export_pdf_and_png():
    expanded_entities = []
    for entity in entities:
        if entity["kind"] == "dimension":
            expanded_entities.extend(_dimension_primitives(entity))
        else:
            expanded_entities.append(entity)

    c = canvas.Canvas(str(PDF_PATH), pagesize=(PAGE_W_MM * MM_TO_PT, PAGE_H_MM * MM_TO_PT))

    for e in expanded_entities:
        kind = e["kind"]
        if kind == "line":
            c.setLineWidth(e.get("width", 0.18) * MM_TO_PT)
            c.line(e["x1"] * MM_TO_PT, e["y1"] * MM_TO_PT, e["x2"] * MM_TO_PT, e["y2"] * MM_TO_PT)
        elif kind == "polyline":
            c.setLineWidth(e.get("width", 0.18) * MM_TO_PT)
            p = c.beginPath()
            pts = e["points"]
            p.moveTo(pts[0][0] * MM_TO_PT, pts[0][1] * MM_TO_PT)
            for pt in pts[1:]:
                p.lineTo(pt[0] * MM_TO_PT, pt[1] * MM_TO_PT)
            if e.get("closed"):
                p.close()
            c.drawPath(p)
        elif kind == "circle":
            c.setLineWidth(e.get("width", 0.18) * MM_TO_PT)
            c.circle(e["x"] * MM_TO_PT, e["y"] * MM_TO_PT, e["r"] * MM_TO_PT)
        elif kind == "solid":
            c.setLineWidth(e.get("width", 0.18) * MM_TO_PT)
            p = c.beginPath()
            pts = e["points"]
            p.moveTo(pts[0][0] * MM_TO_PT, pts[0][1] * MM_TO_PT)
            for pt in pts[1:]:
                p.lineTo(pt[0] * MM_TO_PT, pt[1] * MM_TO_PT)
            p.close()
            c.drawPath(p, fill=1)
        elif kind == "text":
            c.saveState()
            c.translate(e["x"] * MM_TO_PT, e["y"] * MM_TO_PT)
            c.rotate(e.get("rotation", 0.0))
            font_name = "Helvetica-Bold" if e.get("bold") else "Helvetica"
            c.setFont(font_name, e["size"] * MM_TO_PT)
            if e.get("align") == "center":
                c.drawCentredString(0, 0, e["value"])
            else:
                c.drawString(0, 0, e["value"])
            c.restoreState()

    c.save()
    print(f"Generated PDF: {PDF_PATH}")

    scr_path = OUTPUT / "conv_iso72.scr"
    scr_path.write_text(
        f'FILEDIA 0\nDXFIN "{DXF_PATH.resolve()}"\nSAVEAS 2018 "{DWG_PATH.resolve()}"\nQUIT Y\n'
    )
    for candidate in [
        Path("/Applications/Autodesk/AutoCAD 2026/AutoCAD 2026.app/Contents/Helpers/AcCoreConsole.app/Contents/MacOS/accoreconsole"),
        Path("/Applications/Autodesk/AutoCAD 2027/AutoCAD 2027.app/Contents/Helpers/AcCoreConsole.app/Contents/MacOS/accoreconsole"),
    ]:
        if candidate.exists():
            subprocess.run([str(candidate), "/i", str(DXF_PATH.resolve()), "/s", str(scr_path.resolve())],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Generated DWG via AcCoreConsole: {DWG_PATH}")
            break

    with pdfplumber.open(PDF_PATH) as pdf:
        im = pdf.pages[0].to_image(resolution=300)
        im.save(PNG_PATH)
        print(f"Generated PNG: {PNG_PATH}")


def main():
    validate_split_source()
    build_entities()
    export_dxf()
    export_pdf_and_png()


if __name__ == "__main__":
    main()
