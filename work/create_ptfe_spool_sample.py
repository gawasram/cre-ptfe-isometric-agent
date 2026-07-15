from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib.pagesizes import A2, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "outputs" / "PTFE_Spool_Sample_1507_Sheet1_REVIEW.pdf"
DXF_PATH = ROOT / "outputs" / "PTFE_Spool_Sample_1507_Sheet1_REVIEW.dxf"

PAGE_W = 594.0
PAGE_H = 420.0

entities: list[dict] = []


def add_line(x1, y1, x2, y2, layer="OBJECT", width=0.25, dash=None):
    entities.append(
        dict(kind="line", x1=x1, y1=y1, x2=x2, y2=y2, layer=layer, width=width, dash=dash)
    )


def add_polyline(points, layer="OBJECT", width=0.25, closed=False, dash=None):
    for index in range(len(points) - 1):
        add_line(*points[index], *points[index + 1], layer=layer, width=width, dash=dash)
    if closed:
        add_line(*points[-1], *points[0], layer=layer, width=width, dash=dash)


def add_circle(x, y, r, layer="OBJECT", width=0.25):
    entities.append(dict(kind="circle", x=x, y=y, r=r, layer=layer, width=width))


def add_text(x, y, value, size=3.0, layer="TEXT", rotation=0.0, bold=False, align="left"):
    entities.append(
        dict(
            kind="text",
            x=x,
            y=y,
            value=value,
            size=size,
            layer=layer,
            rotation=rotation,
            bold=bold,
            align=align,
        )
    )


def add_arrow(x, y, angle_deg, size=2.2, layer="DIM"):
    angle = math.radians(angle_deg)
    back = (x - size * math.cos(angle), y - size * math.sin(angle))
    normal = (-math.sin(angle), math.cos(angle))
    p2 = (back[0] + size * 0.45 * normal[0], back[1] + size * 0.45 * normal[1])
    p3 = (back[0] - size * 0.45 * normal[0], back[1] - size * 0.45 * normal[1])
    entities.append(dict(kind="solid", points=[(x, y), p2, p3], layer=layer))


def readable_angle(angle):
    while angle > 90:
        angle -= 180
    while angle < -90:
        angle += 180
    return angle


def add_aligned_dimension(p1, p2, offset, label):
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    q1 = (x1 + nx * offset, y1 + ny * offset)
    q2 = (x2 + nx * offset, y2 + ny * offset)
    add_line(x1, y1, q1[0] + nx * 2, q1[1] + ny * 2, layer="DIM", width=0.13)
    add_line(x2, y2, q2[0] + nx * 2, q2[1] + ny * 2, layer="DIM", width=0.13)
    add_line(*q1, *q2, layer="DIM", width=0.13)
    angle = math.degrees(math.atan2(dy, dx))
    add_arrow(*q1, angle, layer="DIM")
    add_arrow(*q2, angle + 180, layer="DIM")
    tx = (q1[0] + q2[0]) / 2 + nx * 1.5
    ty = (q1[1] + q2[1]) / 2 + ny * 1.5
    add_text(tx, ty, label, size=2.8, layer="DIM", rotation=readable_angle(angle), align="center")


def marker(number, x, y, target_x, target_y):
    add_circle(x, y, 3.1, layer="BALLOON", width=0.18)
    add_text(x, y - 0.9, str(number), size=2.4, layer="BALLOON", align="center")
    add_line(x + (3.1 if target_x >= x else -3.1), y, target_x, target_y, layer="BALLOON", width=0.13)


def flange(cx, cy, angle_deg, size=8, layer="OBJECT"):
    angle = math.radians(angle_deg)
    ux, uy = math.cos(angle), math.sin(angle)
    nx, ny = -uy, ux
    for dist in (-1.8, 1.8):
        x = cx + ux * dist
        y = cy + uy * dist
        add_line(x - nx * size / 2, y - ny * size / 2, x + nx * size / 2, y + ny * size / 2, layer, 0.42)


def valve(cx, cy, angle_deg, length=12, size=7):
    angle = math.radians(angle_deg)
    ux, uy = math.cos(angle), math.sin(angle)
    nx, ny = -uy, ux
    left = (cx - ux * length / 2, cy - uy * length / 2)
    right = (cx + ux * length / 2, cy + uy * length / 2)
    top = (cx + nx * size / 2, cy + ny * size / 2)
    bottom = (cx - nx * size / 2, cy - ny * size / 2)
    add_polyline([left, top, right, bottom, left], layer="OBJECT", width=0.42)


def add_table(x, y, widths, row_heights, rows, header_rows=1, font_size=2.4):
    total_w = sum(widths)
    total_h = sum(row_heights)
    add_polyline([(x, y), (x + total_w, y), (x + total_w, y + total_h), (x, y + total_h)], layer="TABLE", width=0.18, closed=True)
    cursor = x
    for width in widths[:-1]:
        cursor += width
        add_line(cursor, y, cursor, y + total_h, layer="TABLE", width=0.13)
    cursor_y = y + total_h
    for height in row_heights[:-1]:
        cursor_y -= height
        add_line(x, cursor_y, x + total_w, cursor_y, layer="TABLE", width=0.13)
    cursor_y = y + total_h
    for row_index, (row, height) in enumerate(zip(rows, row_heights)):
        baseline = cursor_y - height + max(1.0, (height - font_size) / 2)
        cursor_x = x
        for col_index, (value, width) in enumerate(zip(row, widths)):
            align = "center" if col_index in (0, len(widths) - 1) else "left"
            tx = cursor_x + (width / 2 if align == "center" else 1.2)
            add_text(tx, baseline, str(value), size=font_size, layer="TABLE", bold=row_index < header_rows, align=align)
            cursor_x += width
        cursor_y -= height


# Sheet border and headings.
add_polyline([(8, 8), (586, 8), (586, 412), (8, 412)], layer="BORDER", width=0.35, closed=True)
add_polyline([(11, 11), (583, 11), (583, 409), (11, 409)], layer="BORDER", width=0.18, closed=True)
add_text(18, 397, "IF IN DOUBT, PLEASE ASK", 3.2, "TITLE", bold=True)
add_text(575, 397, "DO NOT SCALE", 3.2, "TITLE", bold=True, align="right")
add_text(297, 399, "DRAFT FOR TECHNICAL REVIEW - NOT FOR FABRICATION", 5.0, "REVIEW", bold=True, align="center")

# Main spool geometry, laid out NTS.
top_tee = (154, 314)
bottom_tee = (342, 143)
main_angle = math.degrees(math.atan2(bottom_tee[1] - top_tee[1], bottom_tee[0] - top_tee[0]))

add_line(*top_tee, *bottom_tee, layer="PIPE_25NB", width=1.0)
add_text(240, 234, '1" NS', 3.0, "LABEL", rotation=readable_angle(main_angle))
add_aligned_dimension(top_tee, bottom_tee, 11, "923 PIPE SPOOL")
add_aligned_dimension((133, 333), (363, 124), 27, "1190 OVERALL")

# Top 25NB blind/spacer connection.
top_up = (133, 333)
add_line(*top_tee, *top_up, layer="PIPE_25NB", width=0.8)
flange(132, 334, main_angle, size=9)
flange(127, 338, main_angle, size=9)
marker(7, 119, 347, 130, 336)
marker(8, 112, 354, 126, 340)
marker(1, 144, 327, 153, 314)
add_text(143, 337, '1" NS', 2.7, "LABEL", rotation=readable_angle(main_angle))

# Top 20NB branch with elbow, pipe, valve and blind flange.
top_drop = (154, 290)
top_branch_end = (91, 259)
add_line(*top_tee, *top_drop, layer="PIPE_20NB", width=0.75)
add_line(*top_drop, 134, 272, layer="PIPE_20NB", width=0.75)
add_line(134, 272, *top_branch_end, layer="PIPE_20NB", width=0.75)
branch_angle_top = math.degrees(math.atan2(top_branch_end[1] - 272, top_branch_end[0] - 134))
valve(108, 264.5, branch_angle_top, length=13, size=8)
flange(88, 258, branch_angle_top, size=9)
marker(2, 144, 286, 153, 292)
marker(3, 127, 282, 136, 273)
marker(4, 110, 278, 108, 265)
marker(5, 79, 270, 89, 259)
add_text(112, 254, '3/4" NS', 2.7, "LABEL", rotation=readable_angle(branch_angle_top))
add_text(97, 272, "118", 2.4, "DIM")
add_text(126, 278, "72", 2.4, "DIM")
add_text(149, 298, "89", 2.4, "DIM")

# Bottom tee and continuation.
continuation = (367, 120)
add_line(*bottom_tee, *continuation, layer="CONTINUATION", width=0.45, dash=(3, 2))
add_text(350, 128, "CONT. ON SHEET 2", 2.6, "LABEL", bold=True)
marker(1, 350, 157, 343, 143)

# Bottom 20NB branch.
bottom_drop = (342, 119)
bottom_branch_end = (280, 88)
add_line(*bottom_tee, *bottom_drop, layer="PIPE_20NB", width=0.75)
add_line(*bottom_drop, 322, 101, layer="PIPE_20NB", width=0.75)
add_line(322, 101, *bottom_branch_end, layer="PIPE_20NB", width=0.75)
branch_angle_bottom = math.degrees(math.atan2(bottom_branch_end[1] - 101, bottom_branch_end[0] - 322))
valve(296, 93.5, branch_angle_bottom, length=13, size=8)
flange(277, 87, branch_angle_bottom, size=9)
marker(2, 332, 115, 341, 120)
marker(3, 315, 111, 324, 102)
marker(4, 298, 107, 296, 94)
marker(5, 268, 99, 278, 88)
add_text(300, 83, '3/4" NS', 2.7, "LABEL", rotation=readable_angle(branch_angle_bottom))
add_text(285, 102, "118", 2.4, "DIM")
add_text(314, 108, "72", 2.4, "DIM")
add_text(337, 127, "89", 2.4, "DIM")

# General notes.
add_text(403, 337, "GENERAL NOTES", 4.2, "TITLE", bold=True)
notes = [
    "1. ALL DIMENSIONS ARE IN mm.",
    "2. FLANGE DRILLING: ASME B16.5, CLASS 150.",
    "3. PTFE RESIN MATERIAL: ASTM D4895.",
    "4. LINED PIPING REQUIREMENTS: ASTM F1545.",
    "5. VERIFY LINER THICKNESS, FLANGE FACING AND TOLERANCES.",
]
for i, note in enumerate(notes):
    add_text(403, 327 - i * 7, note, 2.65, "NOTES", bold=(i == 4))

add_text(403, 286, "INSPECTION", 4.0, "TITLE", bold=True)
add_text(403, 277, "HYDROSTATIC TEST: 29 kg/cm2 (CONFIRM PROCEDURE)", 2.65, "NOTES")
add_text(403, 270, "SPARK TEST: 15 kV (CONFIRM PROCEDURE)", 2.65, "NOTES")
add_text(403, 261, "PACKING: PROTECT ALL LINED FACES WITH WOOD/PLASTIC COVERS.", 2.65, "NOTES")

# Review warning.
add_polyline([(400, 225), (583, 225), (583, 253), (400, 253)], layer="REVIEW", width=0.32, closed=True)
add_text(402, 245, "DIMENSIONAL HOLD POINT", 3.4, "REVIEW", bold=True)
add_text(402, 237, "SAMPLE LISTS 923/72; SOURCE CUT-LENGTH TABLE LISTS 1114/80.", 2.7, "REVIEW", bold=True)
add_text(402, 230, "OBTAIN APPROVED LINED-FITTING DATA BEFORE FABRICATION.", 2.7, "REVIEW", bold=True)

# Corrected BOM.
bom_rows = [
    ["ITEM", "DESCRIPTION", "SIZE", "LENGTH", "QTY"],
    ["*", "GASKET, SPIRAL, CLASS 150", "25NB", "-", "1"],
    ["*", "GASKET, SPIRAL, CLASS 150", "20NB", "-", "4"],
    ["8", "BLIND FLANGE", "25NB", "17", "1"],
    ["7", "PTFE SOLID SPACER", "25NB", "5", "1"],
    ["6", "PIPE SPOOL - VERIFY LENGTH", "25NB", "923", "1"],
    ["5", "BLIND FLANGE", "20NB", "17", "2"],
    ["4", "BALL VALVE", "20NB", "118", "2"],
    ["3", "PIPE SPOOL - VERIFY LENGTH", "20NB", "72", "2"],
    ["2", "90 DEG ELBOW", "20NB", "89 C/H", "2"],
    ["1", "REDUCING TEE", "25x20NB", "89 C/H", "2"],
]
add_table(400, 97, [12, 92, 28, 25, 16], [7] * len(bom_rows), bom_rows, header_rows=1, font_size=2.35)

# Title block.
tx, ty, tw, th = 400, 12, 183, 78
add_polyline([(tx, ty), (tx + tw, ty), (tx + tw, ty + th), (tx, ty + th)], layer="BORDER", width=0.28, closed=True)
for y in [79, 69, 59, 49, 30]:
    add_line(tx, y, tx + tw, y, layer="BORDER", width=0.13)
add_line(455, 12, 455, 49, layer="BORDER", width=0.13)
add_line(505, 12, 505, 49, layer="BORDER", width=0.13)
add_line(545, 12, 545, 49, layer="BORDER", width=0.13)
add_text(491.5, 82, "CORROSION RESISTANT EQUIPMENT PVT LTD", 4.1, "TITLE", bold=True, align="center")
add_text(402, 72, "CUSTOMER: ENGINEERS INDIA LTD., NEW DELHI", 2.7, "TITLE")
add_text(402, 62, "PROJECT: MIL PROJECT, TNT PLANT, HEF KHADKI, PUNE", 2.7, "TITLE")
add_text(402, 52, 'LINE NO.: 1"-SNA-418-1507-A82Y-G', 2.8, "TITLE", bold=True)
add_text(402, 41, "DRAWN: PRACTICE SAMPLE", 2.45, "TITLE")
add_text(457, 41, "DATE: 13.07.2026", 2.45, "TITLE")
add_text(507, 41, "SCALE: NTS", 2.45, "TITLE")
add_text(547, 41, "REV: P0", 2.45, "TITLE")
add_text(402, 34, "CHECKED: -", 2.45, "TITLE")
add_text(457, 34, "APPROVED: -", 2.45, "TITLE")
add_text(507, 34, "SHEET: 1 OF 4", 2.45, "TITLE")
add_text(402, 21, "STATUS: DRAFT FOR TECHNICAL REVIEW", 3.0, "REVIEW", bold=True)


LAYER_COLORS = {
    "REVIEW": (0.8, 0.0, 0.0),
    "DIM": (0.25, 0.25, 0.25),
    "CONTINUATION": (0.25, 0.25, 0.25),
}


def render_pdf():
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(PDF_PATH), pagesize=landscape(A2), pageCompression=1)
    c.setTitle("PTFE Spool Sample 1507 Sheet 1 - Review")
    for entity in entities:
        layer = entity.get("layer", "OBJECT")
        color = LAYER_COLORS.get(layer, (0.0, 0.0, 0.0))
        c.setStrokeColorRGB(*color)
        c.setFillColorRGB(*color)
        c.setLineWidth(entity.get("width", 0.25) * mm)
        if entity["kind"] == "line":
            dash = entity.get("dash")
            if dash:
                c.setDash(*[value * mm for value in dash])
            else:
                c.setDash()
            c.line(entity["x1"] * mm, entity["y1"] * mm, entity["x2"] * mm, entity["y2"] * mm)
        elif entity["kind"] == "circle":
            c.setDash()
            c.circle(entity["x"] * mm, entity["y"] * mm, entity["r"] * mm, stroke=1, fill=0)
        elif entity["kind"] == "solid":
            path = c.beginPath()
            points = entity["points"]
            path.moveTo(points[0][0] * mm, points[0][1] * mm)
            for point in points[1:]:
                path.lineTo(point[0] * mm, point[1] * mm)
            path.close()
            c.drawPath(path, stroke=0, fill=1)
        elif entity["kind"] == "text":
            font = "Helvetica-Bold" if entity.get("bold") else "Helvetica"
            size_pt = entity["size"] * mm
            value = entity["value"]
            width_pt = stringWidth(value, font, size_pt)
            x_pt = entity["x"] * mm
            if entity.get("align") == "center":
                x_pt -= width_pt / 2
            elif entity.get("align") == "right":
                x_pt -= width_pt
            c.saveState()
            c.translate(entity["x"] * mm, entity["y"] * mm)
            c.rotate(entity.get("rotation", 0.0))
            local_x = 0
            if entity.get("align") == "center":
                local_x = -width_pt / 2
            elif entity.get("align") == "right":
                local_x = -width_pt
            c.setFont(font, size_pt)
            c.drawString(local_x, 0, value)
            c.restoreState()
    c.showPage()
    c.save()


def dxf_pair(lines, code, value):
    lines.append(str(code))
    lines.append(str(value))


def render_dxf():
    lines: list[str] = []
    dxf_pair(lines, 0, "SECTION")
    dxf_pair(lines, 2, "HEADER")
    dxf_pair(lines, 9, "$ACADVER")
    # R12/AC1009 keeps the hand-written DXF intentionally simple and broadly
    # compatible; later DXF versions require handles and additional tables.
    dxf_pair(lines, 1, "AC1009")
    dxf_pair(lines, 9, "$MEASUREMENT")
    dxf_pair(lines, 70, 1)
    dxf_pair(lines, 0, "ENDSEC")
    dxf_pair(lines, 0, "SECTION")
    dxf_pair(lines, 2, "TABLES")
    dxf_pair(lines, 0, "TABLE")
    dxf_pair(lines, 2, "LAYER")
    layers = sorted({entity.get("layer", "OBJECT") for entity in entities} | {"0"})
    dxf_pair(lines, 70, len(layers))
    for index, layer in enumerate(layers):
        dxf_pair(lines, 0, "LAYER")
        dxf_pair(lines, 2, layer)
        dxf_pair(lines, 70, 0)
        dxf_pair(lines, 62, 1 if layer == "REVIEW" else 7)
        dxf_pair(lines, 6, "CONTINUOUS")
    dxf_pair(lines, 0, "ENDTAB")
    dxf_pair(lines, 0, "ENDSEC")
    dxf_pair(lines, 0, "SECTION")
    dxf_pair(lines, 2, "ENTITIES")
    for entity in entities:
        kind = entity["kind"]
        layer = entity.get("layer", "OBJECT")
        if kind == "line":
            dxf_pair(lines, 0, "LINE")
            dxf_pair(lines, 8, layer)
            dxf_pair(lines, 10, f'{entity["x1"]:.4f}')
            dxf_pair(lines, 20, f'{entity["y1"]:.4f}')
            dxf_pair(lines, 30, 0)
            dxf_pair(lines, 11, f'{entity["x2"]:.4f}')
            dxf_pair(lines, 21, f'{entity["y2"]:.4f}')
            dxf_pair(lines, 31, 0)
        elif kind == "circle":
            dxf_pair(lines, 0, "CIRCLE")
            dxf_pair(lines, 8, layer)
            dxf_pair(lines, 10, f'{entity["x"]:.4f}')
            dxf_pair(lines, 20, f'{entity["y"]:.4f}')
            dxf_pair(lines, 30, 0)
            dxf_pair(lines, 40, f'{entity["r"]:.4f}')
        elif kind == "solid":
            dxf_pair(lines, 0, "SOLID")
            dxf_pair(lines, 8, layer)
            points = entity["points"]
            four = [points[0], points[1], points[2], points[2]]
            for index, point in enumerate(four):
                dxf_pair(lines, 10 + index, f"{point[0]:.4f}")
                dxf_pair(lines, 20 + index, f"{point[1]:.4f}")
                dxf_pair(lines, 30 + index, 0)
        elif kind == "text":
            dxf_pair(lines, 0, "TEXT")
            dxf_pair(lines, 8, layer)
            dxf_pair(lines, 10, f'{entity["x"]:.4f}')
            dxf_pair(lines, 20, f'{entity["y"]:.4f}')
            dxf_pair(lines, 30, 0)
            dxf_pair(lines, 40, f'{entity["size"]:.4f}')
            dxf_pair(lines, 1, entity["value"])
            dxf_pair(lines, 50, f'{entity.get("rotation", 0.0):.4f}')
            dxf_pair(lines, 7, "STANDARD")
    dxf_pair(lines, 0, "ENDSEC")
    dxf_pair(lines, 0, "EOF")
    DXF_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    render_pdf()
    render_dxf()
    print(PDF_PATH)
    print(DXF_PATH)
