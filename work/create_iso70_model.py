from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import pdfplumber
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A2
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = Path(
    "/Users/ram/Downloads/ilovepdf_extracted-pages/"
    "ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150-70.pdf"
)
SOURCE_PAGE_INDEX = 0
OUTPUT = ROOT / "outputs"
OUTPUT.mkdir(exist_ok=True)
PDF_PATH = OUTPUT / "ISO_70_PTFE.pdf"
DXF_PATH = OUTPUT / "ISO_70_PTFE.dxf"
DWG_PATH = OUTPUT / "ISO_70_PTFE.dwg"
PNG_PATH = OUTPUT / "ISO_70_PTFE.png"

ARIAL_NARROW_PATH = Path("/System/Library/Fonts/Supplemental/Arial Narrow.ttf")
ARIAL_NARROW_BOLD_PATH = Path(
    "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"
)
# AutoCAD's romans.shx is authoritative in the DXF.  Times New Roman is used
# only as a visibly distinct, single-stroke-like preview surrogate in PDF/PNG.
ROMANS_PREVIEW_PATH = Path(
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
)

MM_TO_PT = 72.0 / 25.4
PAGE_W_MM = 420.0
PAGE_H_MM = 594.0
entities: list[dict] = []

# Normalised A2 values derived from the useful ratios in the client
# CHEM@123 dimension style.  The reference sheets are unitless and use raw
# DIMSCALE overrides from 10 to 60, so those values must not be copied into a
# true millimetre drawing.
DIM_TEXT_HEIGHT = 2.1
DIM_ARROW_LENGTH = DIM_TEXT_HEIGHT
DIM_ARROW_BASE = DIM_ARROW_LENGTH / 3.0
DIM_EXT_OFFSET = DIM_TEXT_HEIGHT * 0.5
DIM_EXT_EXCEED = DIM_TEXT_HEIGHT * 0.5
DIM_TEXT_GAP = DIM_TEXT_HEIGHT * 0.4
ISOMETRIC_AXIS_TOLERANCE_DEG = 0.2


def validate_split_source():
    """Fail early if the requested one-page source is not the input file.

    Page 70 was extracted into its own A2 landscape PDF.  Keeping this check
    in the generator prevents a future run from silently falling back to the
    combined document or the wrong viewer-page index.
    """
    if not SOURCE_PDF.is_file():
        raise FileNotFoundError(f"Split source PDF not found: {SOURCE_PDF}")
    with pdfplumber.open(SOURCE_PDF) as pdf:
        if len(pdf.pages) != 1:
            raise ValueError(f"Expected one split page, found {len(pdf.pages)}")
        page = pdf.pages[SOURCE_PAGE_INDEX]
        if abs(page.width - 1683.78) > 2 or abs(page.height - 1190.55) > 2:
            raise ValueError(
                f"Unexpected split-page size: {page.width:.2f} x {page.height:.2f} pt"
            )


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


def balloon_leader_start(bubble, target, radius):
    """Return the point where a straight leader leaves a balloon circle.

    The public helper is intentionally page-independent so a new ISO generator
    can reuse it.  A target inside (or at the centre of) the bubble is a
    drafting error because no outward leader segment can be constructed.
    """
    bx, by = bubble
    tx, ty = target
    dx, dy = tx - bx, ty - by
    distance = math.hypot(dx, dy)
    if distance <= float(radius) + 1e-9:
        raise ValueError(
            "balloon leader target must lie outside the balloon perimeter"
        )
    scale = float(radius) / distance
    return bx + dx * scale, by + dy * scale


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
        # Text height is measured from the baseline.  This offset visually
        # centres the lettering in the cell instead of sitting on a rule.
        baseline = y + visual_row * row_h + (row_h - font_size) / 2 + font_size * 0.18
        original_index = len(rows) - 1 - visual_row
        cx = x
        is_header = str(row[0]).strip().upper() in {"PART NO", "PIECE", "ITEM"}
        for col, (value, width) in enumerate(zip(row, widths)):
            if col in (0, 2, 3, 4):
                add_text(cx + width / 2, baseline, value, font_size, "TABLE",
                         bold=is_header, align="center")
            else:
                add_text(cx + 1.0, baseline, value, font_size, "TABLE",
                         bold=is_header)
            cx += width


def add_callout(number, bubble, target):
    bx, by = bubble
    radius = 2.30
    leader_start = balloon_leader_start(bubble, target, radius)
    add_line(*leader_start, *target, "CALLOUT", 0.20)
    add_circle(bx, by, radius, "CALLOUT", 0.35)
    add_text(bx, by - 0.90, number, 1.80, "CALLOUT", bold=True, align="center")


def add_flange(x, y, angle_deg=0.0):
    angle = math.radians(angle_deg)
    if math.isclose(abs(angle_deg % 180.0), 90.0, abs_tol=1.0):
        # On vertical pipe risers, flange faces run along 30° isometric axis
        fx, fy = math.cos(math.radians(30.0)), math.sin(math.radians(30.0))
    else:
        fx, fy = -math.sin(angle), math.cos(angle)
    for offset in (-1.4, 1.4):
        cx = x + math.cos(angle) * offset
        cy = y + math.sin(angle) * offset
        add_line(cx - fx * 4.0, cy - fy * 4.0, cx + fx * 4.0, cy + fy * 4.0,
                 "COMPONENT", 0.32)


def add_valve(x, y, angle_deg=0.0):
    angle = math.radians(angle_deg)
    ux, uy = math.cos(angle), math.sin(angle)
    nx, ny = -uy, ux
    p1 = (x - ux * 5, y - uy * 5)
    p2 = (x + ux * 5, y + uy * 5)
    top = (x + nx * 4, y + ny * 4)
    bottom = (x - nx * 4, y - ny * 4)
    add_line(*p1, *top, "COMPONENT", 0.32)
    add_line(*top, *p2, "COMPONENT", 0.32)
    add_line(*p2, *bottom, "COMPONENT", 0.32)
    add_line(*bottom, *p1, "COMPONENT", 0.32)
    add_circle(x, y, 1.2, "COMPONENT", 0.24)


def move_point(point, angle_deg, distance):
    angle = math.radians(angle_deg)
    return (
        point[0] + math.cos(angle) * distance,
        point[1] + math.sin(angle) * distance,
    )


def draw_pipe(p1, p2, width=0.53):
    add_line(p1[0], p1[1], p2[0], p2[1], "PIPE", width)


def draw_flanged_valve(center, angle_deg, draw_length=14.0, globe=False):
    """Draw the ISO-31-to-35 style simplified flanged valve."""
    p1 = move_point(center, angle_deg, -draw_length / 2)
    p2 = move_point(center, angle_deg, draw_length / 2)
    add_flange(*p1, angle_deg)
    add_flange(*p2, angle_deg)
    body1 = move_point(center, angle_deg, -5.0)
    body2 = move_point(center, angle_deg, 5.0)
    draw_pipe(p1, body1, 0.42)
    draw_pipe(body2, p2, 0.42)
    add_valve(*center, angle_deg)
    if globe:
        stem_end = move_point(center, angle_deg + 90, 6.0)
        add_line(center[0], center[1], stem_end[0], stem_end[1], "COMPONENT", 0.20)
        add_circle(stem_end[0], stem_end[1], 1.2, "COMPONENT", 0.18)
    return p1, p2


def draw_orifice(center, angle_deg, draw_length=24.0, body_width=4.4):
    cx, cy = center
    rad = math.radians(angle_deg)
    ux, uy = math.cos(rad), math.sin(rad)
    nx, ny = -uy, ux

    if math.isclose(abs(angle_deg % 180.0), 90.0, abs_tol=1.0):
        fx, fy = math.cos(math.radians(30.0)), math.sin(math.radians(30.0))
    else:
        fx, fy = nx, ny

    p1 = (cx - ux * (draw_length / 2), cy - uy * (draw_length / 2))
    p2 = (cx + ux * (draw_length / 2), cy + uy * (draw_length / 2))

    # Weld dots at endpoints (welds 46 and 47)
    add_circle(p1[0], p1[1], 0.85, "COMPONENT", 0.35)
    add_circle(p2[0], p2[1], 0.85, "COMPONENT", 0.35)

    # Flange hub neck flared trapezoids
    flange1_base = (cx - ux * 8.5, cy - uy * 8.5)
    flange2_base = (cx + ux * 8.5, cy + uy * 8.5)

    add_line(p1[0] - fx * 0.6, p1[1] - fy * 0.6, flange1_base[0] - fx * 2.8, flange1_base[1] - fy * 2.8, "COMPONENT", 0.25)
    add_line(p1[0] + fx * 0.6, p1[1] + fy * 0.6, flange1_base[0] + fx * 2.8, flange1_base[1] + fy * 2.8, "COMPONENT", 0.25)

    add_line(p2[0] - fx * 0.6, p2[1] - fy * 0.6, flange2_base[0] - fx * 2.8, flange2_base[1] - fy * 2.8, "COMPONENT", 0.25)
    add_line(p2[0] + fx * 0.6, p2[1] + fy * 0.6, flange2_base[0] + fx * 2.8, flange2_base[1] + fy * 2.8, "COMPONENT", 0.25)

    # Flange face bars (hollow thin rectangles slanted at isometric angle)
    def draw_flange_bar(f_center):
        b_top = (f_center[0] + ux * 0.6, f_center[1] + uy * 0.6)
        b_bot = (f_center[0] - ux * 0.6, f_center[1] - uy * 0.6)
        t1 = (b_top[0] - fx * 3.2, b_top[1] - fy * 3.2)
        t2 = (b_top[0] + fx * 3.2, b_top[1] + fy * 3.2)
        m1 = (b_bot[0] - fx * 3.2, b_bot[1] - fy * 3.2)
        m2 = (b_bot[0] + fx * 3.2, b_bot[1] + fy * 3.2)
        add_line(*t1, *t2, "COMPONENT", 0.25)
        add_line(*m1, *m2, "COMPONENT", 0.25)
        add_line(*t1, *m1, "COMPONENT", 0.25)
        add_line(*t2, *m2, "COMPONENT", 0.25)

    draw_flange_bar(flange1_base)
    draw_flange_bar(flange2_base)

    # Central hollow rectangle meter body
    body1 = (cx - ux * 5.8, cy - uy * 5.8)
    body2 = (cx + ux * 5.8, cy + uy * 5.8)
    w_half = body_width / 2.0

    r1_l = (body1[0] - fx * w_half, body1[1] - fy * w_half)
    r1_r = (body1[0] + fx * w_half, body1[1] + fy * w_half)
    r2_l = (body2[0] - fx * w_half, body2[1] - fy * w_half)
    r2_r = (body2[0] + fx * w_half, body2[1] + fy * w_half)

    add_line(*r1_l, *r2_l, "COMPONENT", 0.28)
    add_line(*r1_r, *r2_r, "COMPONENT", 0.28)
    add_line(*r1_l, *r1_r, "COMPONENT", 0.24)
    add_line(*r2_l, *r2_r, "COMPONENT", 0.24)

    return p1, p2


def add_stadium_tag(text, center_x, center_y, number=None, target=None):
    w, h = 26.0, 5.0
    half_w, half_h = w / 2.0, h / 2.0
    left_x = center_x - half_w
    right_x = center_x + half_w
    bottom_y = center_y - half_h
    top_y = center_y + half_h
    add_line(left_x, top_y, right_x, top_y, "COMPONENT", 0.22)
    add_line(left_x, bottom_y, right_x, bottom_y, "COMPONENT", 0.22)
    r = half_h
    add_circle(left_x, center_y, r, "COMPONENT", 0.22)
    add_circle(right_x, center_y, r, "COMPONENT", 0.22)
    add_text(center_x, center_y - 0.9, text, 2.15, "LABEL", bold=True, align="center")
    if number:
        sq_x, sq_y = left_x + 3.0, top_y + 4.5
        add_polyline([(sq_x - 2.2, sq_y - 2.2), (sq_x + 2.2, sq_y - 2.2),
                      (sq_x + 2.2, sq_y + 2.2), (sq_x - 2.2, sq_y + 2.2)],
                     "CALLOUT", 0.25, closed=True)
        add_text(sq_x, sq_y - 0.9, str(number), 2.0, "CALLOUT", bold=True, align="center")
    if target:
        add_line(right_x + r, center_y, target[0], target[1], "CALLOUT", 0.22)


def draw_reducer(p1, p2, large_width=7.0, small_width=3.8):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return
    nx, ny = -dy / length, dx / length
    a1 = (p1[0] + nx * large_width / 2, p1[1] + ny * large_width / 2)
    a2 = (p1[0] - nx * large_width / 2, p1[1] - ny * large_width / 2)
    b1 = (p2[0] + nx * small_width / 2, p2[1] + ny * small_width / 2)
    b2 = (p2[0] - nx * small_width / 2, p2[1] - ny * small_width / 2)
    add_line(*a1, *b1, "COMPONENT", 0.24)
    add_line(*a2, *b2, "COMPONENT", 0.24)
    draw_pipe(p1, p2, 0.40)


def draw_blind_flange(center, angle_deg):
    add_flange(*center, angle_deg)
    cap = move_point(center, angle_deg, 1.8)
    perp = angle_deg + 90
    a = move_point(cap, perp, -4.2)
    b = move_point(cap, perp, 4.2)
    add_line(a[0], a[1], b[0], b[1], "COMPONENT", 0.26)


def add_small_callout(number, bubble, target):
    bx, by = bubble
    radius = 2.15
    leader_start = balloon_leader_start(bubble, target, radius)
    add_line(*leader_start, *target, "CALLOUT", 0.20)
    add_circle(bx, by, radius, "CALLOUT", 0.35)
    add_text(bx, by - 0.90, number, 1.80, "CALLOUT", bold=True, align="center")


def add_single_dimension(p1, p2, label, offset, oblique_angle=None):
    add_dimension_pair(p1, p2, (str(label),), offsets=(offset,), oblique_angle=oblique_angle)


def get_default_oblique_angle(p1, p2):
    """Choose the CRE Group-Code-52 angle for a standard isometric baseline.

    Nonstandard/source-proven projection dimensions must pass an explicit
    ``oblique_angle``.  Silently defaulting an off-axis baseline made malformed
    geometry look compliant in earlier generators.
    """
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    if math.hypot(dx, dy) <= 1e-9:
        raise ValueError("cannot choose an oblique angle for a zero-length baseline")
    angle = math.degrees(math.atan2(dy, dx)) % 180.0
    if math.isclose(angle, 90.0, abs_tol=ISOMETRIC_AXIS_TOLERANCE_DEG):
        return 30.0
    if math.isclose(angle, 30.0, abs_tol=ISOMETRIC_AXIS_TOLERANCE_DEG):
        return 150.0
    if math.isclose(angle, 150.0, abs_tol=ISOMETRIC_AXIS_TOLERANCE_DEG):
        return 30.0
    raise ValueError(
        f"dimension baseline is {angle:.6f} degrees; expected 30, 90 or 150. "
        "Pass oblique_angle explicitly only for a source-proven projection."
    )


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
    """Return a pipe-aligned angle that never renders the text upside-down."""
    angle = ((angle_deg + 180.0) % 360.0) - 180.0
    if angle > 90.0:
        angle -= 180.0
    elif angle <= -90.0:
        angle += 180.0
    return angle


def _dimension_primitives(entity):
    """Expand a dimension for PDF/PNG while DXF keeps a live DIMENSION entity."""
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

    # Direction of extension line extension past dim line
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


def _render_entities():
    """Yield primitives for page renderers; keep dimensions live in DXF."""
    for entity in entities:
        if entity["kind"] == "dimension":
            yield from _dimension_primitives(entity)
        else:
            yield entity


def add_notes():
    x = 15
    add_text(x, 132.0, "GENERAL NOTES :-", 3.2, "TITLE", bold=True)
    add_line(x, 130.4, x + 35, 130.4, "TITLE", 0.20)
    notes = [
        "1) ALL DIMENSIONS ARE IN MM.",
        "2) FLANGE DRILLING: ANSI B16.5 CLASS 150#.",
        "3) PTFE LINING: ASTM D4895 STANDARD.",
        "4) TESTING & DIMENSIONS: ASTM 1545.",
        "5) HYDRO TEST: 29 KG/CM2; SPARK TEST: 15 KVA.",
        "6) PROTECT ALL LINED FACES DURING PACKING.",
    ]
    for i, note in enumerate(notes):
        add_text(x, 125.0 - i * 5.1, note, 2.60, "NOTES", bold=i == 0)


def add_reference_notes():
    """Notes block arranged like the supplied ISO_31_TO_35 reference."""
    x = 215
    add_text(x, 198, "GENERAL NOTES :-", 4.0, "TITLE", bold=True)
    add_line(x, 196.4, x + 38, 196.4, "TITLE", 0.20)
    notes = [
        "1) ALL DIMENSIONS ARE IN MM.",
        "2) FLANGE CONN. DRILLING AS PER ANSI B16.5 CLASS 150#.",
        "3) PTFE LINING AS PER ASTM D4895 STANDARD.",
        "4) TESTING AND DIMENSIONS AS PER ASTM 1545.",
    ]
    for i, note in enumerate(notes):
        add_text(x + 2, 190 - i * 6.2, note, 2.80, "NOTES", bold=i == 0)
    add_text(x, 160, "INSPECTION", 3.6, "TITLE", bold=True)
    add_line(x, 158.4, x + 27, 158.4, "TITLE", 0.18)
    add_text(x + 2, 152, "- HYDRO TEST :- 29 KG/CM2", 2.80, "NOTES")
    add_text(x + 2, 145, "- SPARK TEST :- 15 KVA", 2.80, "NOTES")
    add_text(x, 134, "PACKING:- WOODEN / PLASTIC COVERS WILL BE USED", 2.55, "NOTES")
    add_text(x, 128, "TO PROTECT ALL LINED PORTIONS.", 2.55, "NOTES")


def add_title_block(
    *,
    line_number='1"-SNA-424-1501-1-A82Y-A',
    sheet_number="2 OF 2",
    drafter="RAM GAWAS",
    drawing_date="14.7.26",
    revision="0",
):
    # Right title block from ISO_06 model.
    tx, ty, tw, th = 215, 12, 190, 79
    add_rect(tx, ty, tw, th, "BORDER", 0.28)
    for y in [80, 69, 58, 43, 22]:
        add_line(tx, y, tx + tw, y, "BORDER", 0.14)
    add_text(tx + tw / 2, 83.0, "CORROSION RESISTANT EQUIPMENT PVT LTD",
             4.7, "COMPANY", bold=True, align="center")
    add_text(tx + 2, 72.2, "CUSTOMER: ENGINEERS INDIA LTD, NEW DELHI", 2.8, "TITLE", bold=True)
    add_text(tx + 2, 61.2, "PROJECT: MIL PROJECT, TNT PLANT, HEF KHADKI, PUNE", 2.6, "TITLE", bold=True)

    # Approval grid.
    grid_right = 287
    add_line(grid_right, 22, grid_right, 58, "BORDER", 0.14)
    for y in [31, 40, 49]:
        add_line(tx, y, grid_right, y, "BORDER", 0.12)
    for x in [235, 260, 272]:
        add_line(x, 22, x, 58, "BORDER", 0.12)
    add_text(247.5, 52.2, "NAME", 2.3, "TITLE", bold=True, align="center")
    add_text(266, 52.2, "SIGN", 2.3, "TITLE", bold=True, align="center")
    add_text(279.5, 52.2, "DATE", 2.3, "TITLE", bold=True, align="center")
    for y, role in [(43.2, "DRAN"), (34.2, "CHK"), (25.2, "APPD.")]:
        add_text(225, y, role, 2.4, "TITLE", bold=True, align="center")
    add_text(247.5, 43.2, drafter, 2.0, "TITLE", align="center")
    add_text(279.5, 43.2, drawing_date, 2.0, "TITLE", align="center")

    add_text(292, 48.5, "LINE NO.", 3.1, "HIGHLIGHT", bold=True)
    add_text(292, 35.2, line_number, 2.9, "HIGHLIGHT", bold=True)

    # Bottom fields and client cone/circle projection symbol.  Preserve the
    # supplied orientation without assigning an unsupported projection name.
    for x in [265, 305, 375]:
        add_line(x, 12, x, 22, "BORDER", 0.12)
    add_text(240, 15.0, "SCALE=NTS", 2.7, "TITLE", bold=True, align="center")
    add_line(270, 15, 280, 17, "SYMBOL", 0.16)
    add_line(270, 19, 280, 17, "SYMBOL", 0.16)
    add_line(270, 15, 270, 19, "SYMBOL", 0.16)
    add_circle(293, 17, 3.4, "SYMBOL", 0.16)
    add_circle(293, 17, 1.9, "SYMBOL", 0.14)
    add_line(287.5, 17, 298.5, 17, "CENTER", 0.20)
    add_line(293, 11.5, 293, 22.5, "CENTER", 0.20)
    add_text(340, 15.0, f"SHEET NO. {sheet_number}", 2.7, "TITLE", bold=True, align="center")
    add_text(390, 18.0, "REV.", 2.3, "TITLE", bold=True, align="center")
    add_line(375, 16, 405, 16, "BORDER", 0.12)
    add_text(390, 12.5, revision, 2.3, "TITLE", bold=True, align="center")

    # Revision-description table on the left.
    rx, ry, rw, rh = 15, 12, 200, 19
    add_rect(rx, ry, rw, rh, "BORDER", 0.25)
    add_line(rx, 22, rx + rw, 22, "BORDER", 0.12)
    # ISO35 revision-strip proportions: 7.75 | 72.94 | 5.75 | 7.19 | 6.38%.
    for x in [30.5, 176.4, 187.9, 202.3]:
        add_line(x, 12, x, 31, "BORDER", 0.12)
    add_text(22.75, 15.0, "REV.", 2.7, "TITLE", bold=True, align="center")
    add_text(103.45, 15.0, "DESCRIPTION", 2.7, "TITLE", bold=True, align="center")
    add_text(182.15, 15.0, "BY", 2.5, "TITLE", bold=True, align="center")
    add_text(195.10, 15.0, "CHD.", 2.4, "TITLE", bold=True, align="center")
    add_text(208.65, 15.0, "APPD", 2.2, "TITLE", bold=True, align="center")


def build_reference_sheet():
    """Build ISO 70 in the simplified CRE style of ISO_31_TO_35."""

    def midpoint(p1, p2):
        return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

    add_rect(8, 8, 404, 578, "BORDER", 0.35)
    add_rect(11, 11, 398, 572, "BORDER", 0.18)
    add_rect(11, 568, 112, 13, "BORDER", 0.22)
    add_text(67, 571.8, "IF IN ANY DOUBT PLS ASK", 3.75, "TITLE", bold=True, align="center")
    add_rect(309, 568, 100, 13, "BORDER", 0.22)
    add_text(359, 571.8, "DO NOT SCALE", 3.75, "TITLE", bold=True, align="center")

    # Principal nodes of the simplified, connected page-70 network.  Solve
    # related coordinates from tan(30°) so ordinary PIPE segments are exact
    # 30°/150°/vertical axes rather than eye-fitted approximations.
    iso_slope = math.tan(math.radians(30.0))
    # Define nodes with +25mm X-shift to keep entire topology and callouts inside the A2 border
    conn = (40.0, 264.33)
    ang150_rad = math.radians(-30.0)

    ext_flange = (conn[0] + 5.0 * math.cos(ang150_rad),
                  conn[1] + 5.0 * math.sin(ang150_rad))
    reducer_start = (conn[0] + 7.5 * math.cos(ang150_rad),
                     conn[1] + 7.5 * math.sin(ang150_rad))
    reducer_end = (conn[0] + 12.5 * math.cos(ang150_rad),
                   conn[1] + 12.5 * math.sin(ang150_rad))
    elbow_a = (conn[0] + 16.0 * math.cos(ang150_rad),
               conn[1] + 16.0 * math.sin(ang150_rad))
    elbow_b = (118.0, elbow_a[1] + (118.0 - elbow_a[0]) * iso_slope)
    orifice_300_c = (118.0, 321.363)
    elbow_c = (118.0, 423.0)

    elbow_d = (273.0, elbow_c[1] + (273.0 - elbow_c[0]) * iso_slope)
    tee_a = (273.0, 433.163)
    tee_b = (380.0, tee_a[1] - (380.0 - tee_a[0]) * iso_slope)
    globe_c = (326.5, tee_a[1] - (326.5 - tee_a[0]) * iso_slope)
    continuation_top = (380.0, tee_b[1] + 15.0)

    elbow_e = (273.0, 360.583)
    red_tee_a = (295.0, elbow_e[1] - (295.0 - elbow_e[0]) * iso_slope)
    orifice_600_c = (326.5, elbow_e[1] - (326.5 - elbow_e[0]) * iso_slope)
    red_tee_b = (358.0, elbow_e[1] - (358.0 - elbow_e[0]) * iso_slope)
    elbow_f = (380.0, elbow_e[1] - (380.0 - elbow_e[0]) * iso_slope)
    ball_right_c = (380.0, 335.096)

    # Dotted continuation lines past connection flange to existing plant nozzle
    add_line(conn[0], conn[1], conn[0] - 6.0 * math.cos(ang150_rad),
             conn[1] - 6.0 * math.sin(ang150_rad), "CENTER", 0.18)

    # External connection, 1-1/2-inch flange, eccentric reducer and 150° offset elbow.
    draw_pipe(conn, ext_flange)
    add_flange(*ext_flange, -30)
    draw_pipe(ext_flange, reducer_start, 0.42)
    draw_reducer(reducer_start, reducer_end)
    draw_pipe(reducer_end, elbow_a)

    # Main route: <17>, 300-mm orifice, <16>, <15>, <14> to equal tee A.
    draw_pipe(elbow_a, elbow_b)
    or300_p1, or300_p2 = draw_orifice(orifice_300_c, 90, 18.0)
    draw_pipe(elbow_b, or300_p1)
    draw_pipe(or300_p2, elbow_c)
    draw_pipe(elbow_c, elbow_d)
    draw_pipe(elbow_d, tee_a)

    # Upper route between the two equal tees: <13>, globe valve and 94-mm leg.
    globe_p1, globe_p2 = draw_flanged_valve(globe_c, -30, 14.0, globe=True)
    draw_pipe(tee_a, globe_p1)
    draw_pipe(globe_p2, tee_b)

    # Source-supported vertical continuation to drawing 1.
    draw_pipe(tee_b, continuation_top)
    add_text(380, 393, "CONT. FROM DRG 1", 2.6, "LABEL", bold=True, align="center")
    add_text(384, 379, '1"NS', 2.35, "LABEL", rotation=90, bold=True)

    # Lower route, left side: <12>, 1-inch ball valve, 93 and 76 legs.
    ball_left_c = (273.0, 406.0)
    ball_left_p1, ball_left_p2 = draw_flanged_valve(ball_left_c, -90, 14.0)
    draw_pipe(tee_a, ball_left_p1)
    draw_pipe(ball_left_p2, elbow_e)
    draw_pipe(elbow_e, red_tee_a)

    # Lower route centre: 94, 600-mm orifice and 94 to reducing tee B.
    lower_angle = math.degrees(math.atan2(
        red_tee_b[1] - red_tee_a[1], red_tee_b[0] - red_tee_a[0]
    ))
    or600_p1, or600_p2 = draw_orifice(orifice_600_c, lower_angle, 30.0)
    draw_pipe(red_tee_a, or600_p1)
    draw_pipe(or600_p2, red_tee_b)

    # Lower route, right side: 76, elbow, 94, ball valve and <11>.
    ball_right_p1, ball_right_p2 = draw_flanged_valve(ball_right_c, 90, 14.0)
    draw_pipe(red_tee_b, elbow_f)
    draw_pipe(elbow_f, ball_right_p1)
    draw_pipe(ball_right_p2, tee_b)

    # Two identical 3/4-inch blind branches from the reducing tees.
    def branch(tee, center):
        top = (center[0], center[1] + 7.0)
        bottom = (center[0], center[1] - 7.0)
        draw_pipe(tee, top)
        add_flange(*top, -90)
        body_top = (center[0], center[1] + 5.0)
        body_bottom = (center[0], center[1] - 5.0)
        draw_pipe(top, body_top, 0.42)
        add_valve(*center, -90)
        draw_pipe(body_bottom, bottom, 0.42)
        draw_blind_flange(bottom, -90)
        return top, bottom

    branch_left_c = (295.0, 328.0)
    branch_right_c = (358.0, 291.5)
    branch_left_top, branch_left_bottom = branch(red_tee_a, branch_left_c)
    branch_right_top, branch_right_bottom = branch(red_tee_b, branch_right_c)

    # Cut and overall dimensions, arranged like the reference drawings.
    add_dimension_pair(elbow_a, elbow_b, ("167", "243"), offsets=(6.0, 11.0))
    add_dimension_pair(or300_p2, elbow_c, ("576", "669"), offsets=(7.0, 13.0))
    add_dimension_pair(elbow_c, elbow_d, ("2576", "2652"), offsets=(7.0, 13.0))
    add_dimension_pair(elbow_d, tee_a, ("857", "933"), offsets=(-7.0, -13.0))
    add_dimension_pair(tee_a, globe_p1, ("625", "719"), offsets=(6.0, 11.0))
    add_dimension_pair(tee_a, ball_left_p1, ("100", "194"), offsets=(-7.0, -13.0))
    add_dimension_pair(ball_right_p2, tee_b, ("100", "194"), offsets=(7.0, 13.0))

    add_single_dimension(or300_p1, or300_p2, "300", 7.0)
    add_single_dimension(globe_p1, globe_p2, "127", -7.0)
    add_single_dimension(globe_p2, tee_b, "94", 5.0)
    add_single_dimension(tee_b, continuation_top, "38", 6.0, oblique_angle=30.0)
    add_single_dimension(ball_left_p1, ball_left_p2, "128", 7.0)
    add_single_dimension(ball_right_p1, ball_right_p2, "128", -7.0)
    add_single_dimension(red_tee_a, or600_p1, "94", 5.0)
    add_single_dimension(or600_p1, or600_p2, "600", 6.0)
    add_single_dimension(or600_p2, red_tee_b, "94", 5.0)
    add_single_dimension(ball_left_p2, elbow_e, "93", 7.0)
    add_single_dimension(elbow_e, red_tee_a, "76", -5.0)
    add_single_dimension(red_tee_b, elbow_f, "76", -5.0)
    add_single_dimension(elbow_f, ball_right_p1, "94", -7.0)
    add_single_dimension(red_tee_a, branch_left_top, "90", -6.0)
    add_single_dimension(branch_left_top, branch_left_bottom, "118", -6.0)
    add_single_dimension(red_tee_b, branch_right_top, "90", -6.0)
    add_single_dimension(branch_right_top, branch_right_bottom, "118", -6.0)
    add_single_dimension(conn, elbow_a, "125", -7.0)
    add_single_dimension(elbow_b, or300_p1, "94", -7.0)
    add_single_dimension(reducer_end, elbow_a, "38", 6.0, oblique_angle=30.0)

    # 1"NS inline label and square balloon 5 at elbow_a (weld 50)
    add_text(54.0, 245.0, '1"NS', 2.35, "LABEL", bold=True)

    # Source connection callout – text block positioned just below the
    # connection flange with a clear diagonal leader.  In the source the
    # text left-edge is roughly aligned with the pipe endpoint X and the
    # leader runs from the right end of the top text line to the flange.
    conn_text_x = 18.0
    conn_text_top_y = 250.0      # ~14 mm below conn.Y = 264.33
    add_text(conn_text_x, conn_text_top_y,        "CONN. TO",    2.35, "LABEL", bold=True)
    add_text(conn_text_x, conn_text_top_y - 5.0,  "424-N-104/S", 2.35, "LABEL", bold=True)
    add_text(conn_text_x, conn_text_top_y - 9.5,  "E 677077",   2.15, "LABEL")
    add_text(conn_text_x, conn_text_top_y - 13.5, "N 532036",   2.15, "LABEL")
    add_text(conn_text_x, conn_text_top_y - 18.0, "EL +104060", 2.35, "LABEL", bold=True)
    # Leader from top-right of text block to connection flange endpoint
    # Use LABEL layer (ACI 7 black) not CALLOUT (ACI 3 green) so the
    # leader is clearly visible in AutoCAD on a white background.
    add_line(conn_text_x + 18.0, conn_text_top_y + 1.5,
             conn[0], conn[1], "LABEL", 0.25)

    # Source reducer specification callout – sits below the connection
    # block with a small gap (source shows a [2] box between them).
    red_text_top_y = conn_text_top_y - 25.0   # ~7 mm gap from bottom of conn block
    add_text(conn_text_x, red_text_top_y,        '1.1/2"x1"NS',   2.35, "LABEL", bold=True)
    add_text(conn_text_x, red_text_top_y - 5.0,  "7MM OFFSET",    2.35, "LABEL", bold=True)
    add_text(conn_text_x, red_text_top_y - 10.0, "FLAT SIDE DOWN", 2.35, "LABEL", bold=True)
    # Leader from top-right of reducer text to the eccentric reducer centre
    # Use LABEL layer (ACI 7 black) not CALLOUT (ACI 3 green).
    add_line(conn_text_x + 22.0, red_text_top_y + 1.5,
             (reducer_start[0] + reducer_end[0]) / 2.0,
             (reducer_start[1] + reducer_end[1]) / 2.0, "LABEL", 0.25)

    # Capsule stadium tag and square balloon 19 for 300 mm orifice 424-SG-1601
    add_stadium_tag("424-SG-1601", 82.0, 335.0, number="19", target=orifice_300_c)
    add_text(118.0, 395.0, "<16>", 2.35, "LABEL", bold=True, align="center")
    add_text(124, 293.363, "EL +104053", 2.25, "LABEL", bold=True)
    add_text(290, 510, "EL +105122", 2.25, "LABEL", bold=True)
    add_text(243, 442, '1"x1"NS EL +104188', 2.25, "LABEL", bold=True)
    add_text(388, 368, '1"x1"NS EL +104188', 2.25, "LABEL", bold=True)
    add_text(385, 295, "EL +103767", 2.25, "LABEL", bold=True)
    add_text(280, 335, '1"x3/4"NS', 2.25, "LABEL", bold=True)
    add_text(345, 298, '1"x3/4"NS', 2.25, "LABEL", bold=True)

    # Fabrication balloons: repeated components carry the same BOM number.
    callouts = [
        ("1", (366, 360), midpoint(ball_right_p2, tee_b)),
        ("2", (249, 421), midpoint(tee_a, ball_left_p1)),
        ("3", (298, 423), midpoint(tee_a, globe_p1)),
        ("4", (286, 471), midpoint(elbow_d, tee_a)),
        ("5", (191, 469), midpoint(elbow_c, elbow_d)),
        ("6", (100, 378), midpoint(or300_p2, elbow_c)),
        ("7", (88, 271), midpoint(elbow_a, elbow_b)),
        ("8", (46, 247), midpoint(reducer_start, reducer_end)),
        ("9", (283, 438), tee_a), ("9", (377, 384), tee_b),
        ("10", (283, 373), red_tee_a), ("10", (365, 334), red_tee_b),
        ("11", (60, 251), elbow_a), ("11", (133, 289.363), elbow_b),
        ("11", (101, 431), elbow_c), ("11", (282, 516), elbow_d),
        ("11", (263, 378), elbow_e), ("11", (393, 292), elbow_f),
        ("12", (36, 268), ext_flange),
        ("13", (133, 309.363), or300_p1), ("13", (133, 333.363), or300_p2),
        ("13", (313, 414), globe_p1), ("13", (347, 387), globe_p2),
        ("13", (260, 418), ball_left_p1), ("13", (260, 396), ball_left_p2),
        ("13", (307, 350), or600_p1), ("13", (335, 320), or600_p2),
        ("13", (368, 346), ball_right_p2), ("13", (368, 324), ball_right_p1),
        ("14", (273, 348), branch_left_top), ("14", (347, 309), branch_right_top),
        ("15", (273, 312), branch_left_bottom), ("15", (347, 276), branch_right_bottom),
        ("16", (339, 416), globe_c),
        ("17", (241, 406), ball_left_c), ("17", (403, 335), ball_right_c),
        ("18", (267, 320), branch_left_c), ("18", (373, 283), branch_right_c),
        ("20", (325, 368), orifice_600_c),
    ]
    for number, bubble, target in callouts:
        add_small_callout(number, bubble, target)

    # ISO-31-to-35 style fabrication table: header at bottom, parts ascending up.
    header = ["PART NO", "DESCRIPTION", "SIZE", "LENGTH MM", "QTY."]
    rows = [
        ["1", "PIPE SPOOL", '1" (25NB)', "100", "01NO"],
        ["2", "PIPE SPOOL", '1" (25NB)', "100", "01NO"],
        ["3", "PIPE SPOOL", '1" (25NB)', "625", "01NO"],
        ["4", "PIPE SPOOL", '1" (25NB)', "857", "01NO"],
        ["5", "PIPE SPOOL", '1" (25NB)', "2576", "01NO"],
        ["6", "PIPE SPOOL", '1" (25NB)', "576", "01NO"],
        ["7", "PIPE SPOOL", '1" (25NB)', "167", "01NO"],
        ["8", "ECC. REDUCER", '1-1/2"x1"', "--", "01NO"],
        ["9", "EQUAL TEE", '1"x1"', "--", "02NO"],
        ["10", "REDUCING TEE", '1"x3/4"', "--", "02NO"],
        ["11", "90 DEG ELBOW", '1" (25NB)', "38 C/H", "06NO"],
        ["12", "WN FLANGE CL150", '1-1/2"', "--", "01NO"],
        ["13", "WN FLANGE CL150", '1"', "--", "10NO"],
        ["14", "WN FLANGE CL150", '3/4"', "--", "02NO"],
        ["15", "BLIND FLANGE CL150", '3/4"', "--", "02NO"],
        ["16", "GLOBE VALVE", '1"', "127", "01NO"],
        ["17", "BALL VALVE", '1"', "128", "02NO"],
        ["18", "BALL VALVE", '3/4"', "118", "02NO"],
        ["19", "ORIFICE FLOW ELEMENT", '1"', "300", "01NO"],
        ["20", "ORIFICE FLOW ELEMENT", '1"', "600", "01NO"],
    ]
    table_rows = list(reversed(rows)) + [header]
    # ISO35 BOM column proportions, normalised to a 190 mm table width.
    add_table(15, 34, [22.1, 68.5, 40.1, 33.1, 26.2], 7.50, table_rows, 2.45)
    add_reference_notes()
    add_title_block()


LAYER_RGB = {
    "PIPE": (0.0, 0.0, 0.0),
    "DIM": (0.0, 0.0, 0.0),
    "CALLOUT": (0.0, 0.0, 0.0),
    "COMPANY": (0.0, 0.0, 0.0),
    "HIGHLIGHT": (0.0, 0.0, 0.0),
}

# Enforce the extracted CRE line hierarchy even when an old page-specific
# helper passes a thinner legacy width. Entity-level overrides in the supplied
# DWG were visually important, so page renderers and DXF export share this map.
LAYER_WIDTH_LIMITS = {
    "PIPE": (0.53, 0.53),
    "COMPONENT": (0.35, 0.50),
    "DIM": (0.20, 0.25),
    "CALLOUT": (0.20, 0.35),
    "TABLE": (0.25, 0.25),
    "BORDER": (0.20, 0.35),
    "SYMBOL": (0.20, 0.35),
    "CENTER": (0.20, 0.20),
}


def _effective_width(entity):
    width = float(entity.get("width", 0.18))
    limits = LAYER_WIDTH_LIMITS.get(entity.get("layer"))
    if limits is None:
        return width
    return min(max(width, limits[0]), limits[1])


def _png_font(size_px: int, bold: bool = False, role: str = "arial"):
    if role == "romans":
        candidates = [
            str(ROMANS_PREVIEW_PATH),
            "/System/Library/Fonts/Times.ttc",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        ]
    else:
        candidates = [
            str(ARIAL_NARROW_BOLD_PATH if bold else ARIAL_NARROW_PATH),
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
            "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size_px)
    return ImageFont.load_default()


def _register_pdf_fonts():
    """Embed preview fonts that preserve the client text-role distinction."""
    registrations = (
        ("CREArialNarrow", ARIAL_NARROW_PATH),
        ("CREArialNarrowBold", ARIAL_NARROW_BOLD_PATH),
        ("CRERomansPreview", ROMANS_PREVIEW_PATH),
    )
    registered = set(pdfmetrics.getRegisteredFontNames())
    for name, path in registrations:
        if name not in registered and path.is_file():
            pdfmetrics.registerFont(TTFont(name, str(path)))


def render_png():
    scale = 4.0
    width_px = round(PAGE_W_MM * scale)
    height_px = round(PAGE_H_MM * scale)
    image = Image.new("RGB", (width_px, height_px), "white")
    draw = ImageDraw.Draw(image)

    def xy(point):
        x, y = point
        return (round(x * scale), round((PAGE_H_MM - y) * scale))

    def dashed_line(p1, p2, width):
        """Draw the normalised CENTER pattern 2.5-.5-.5-.5 mm."""
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            return
        ux, uy = dx / length, dy / length
        pattern = [2.5 * scale, 0.5 * scale, 0.5 * scale, 0.5 * scale]
        cursor = 0.0
        index = 0
        draw_segment = True
        while cursor < length:
            segment = min(pattern[index % len(pattern)], length - cursor)
            if draw_segment:
                start = (x1 + ux * cursor, y1 + uy * cursor)
                end = (x1 + ux * (cursor + segment), y1 + uy * (cursor + segment))
                draw.line([start, end], fill="black", width=width)
            cursor += segment
            index += 1
            draw_segment = not draw_segment

    for entity in _render_entities():
        kind = entity["kind"]
        line_width = max(1, round(_effective_width(entity) * scale))
        if kind == "line":
            p1 = xy((entity["x1"], entity["y1"]))
            p2 = xy((entity["x2"], entity["y2"]))
            if entity.get("layer") == "CENTER":
                dashed_line(p1, p2, line_width)
            else:
                draw.line([p1, p2], fill="black", width=line_width)
        elif kind == "polyline":
            points = [xy(point) for point in entity["points"]]
            if entity.get("closed") and points:
                points = points + [points[0]]
            if len(points) >= 2:
                draw.line(points, fill="black", width=line_width, joint="curve")
        elif kind == "circle":
            cx, cy = xy((entity["x"], entity["y"]))
            radius = entity["r"] * scale
            box = [cx - radius, cy - radius, cx + radius, cy + radius]
            draw.ellipse(box, outline="black", width=line_width)
        elif kind == "solid":
            points = [xy(point) for point in entity["points"]]
            if len(points) >= 3:
                draw.polygon(points, fill="black")
        elif kind == "text":
            font_size = max(6, round(entity["size"] * scale * 1.25))
            role = "romans" if entity.get("layer") in {"DIM", "CALLOUT"} else "arial"
            font = _png_font(font_size, entity.get("bold", False), role=role)
            x, y = xy((entity["x"], entity["y"]))
            value = entity["value"]
            rotation = entity.get("rotation", 0.0)
            anchor = {"left": "ls", "center": "ms", "right": "rs"}.get(
                entity.get("align", "left"), "ls"
            )
            if abs(rotation) < 0.01:
                draw.text((x, y), value, fill="black", font=font, anchor=anchor)
                continue

            bbox = draw.textbbox((0, 0), value, font=font)
            text_w = bbox[2] - bbox[0] + 8
            text_h = bbox[3] - bbox[1] + 8
            text_img = Image.new("RGBA", (text_w, text_h), (255, 255, 255, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((4 - bbox[0], 4 - bbox[1]), value, fill="black", font=font)
            rotated = text_img.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
            if entity.get("align") == "center":
                paste_x = x - rotated.width // 2
            elif entity.get("align") == "right":
                paste_x = x - rotated.width
            else:
                paste_x = x
            paste_y = y - rotated.height // 2
            image.paste(rotated, (paste_x, paste_y), rotated)

    image.save(PNG_PATH)


def render_pdf():
    _register_pdf_fonts()
    c = canvas.Canvas(str(PDF_PATH), pagesize=A2)
    for entity in _render_entities():
        color = LAYER_RGB.get(entity.get("layer"), (0.0, 0.0, 0.0))
        c.setStrokeColorRGB(*color)
        c.setFillColorRGB(*color)
        c.setLineWidth(_effective_width(entity) * MM_TO_PT)
        if entity.get("layer") == "CENTER":
            c.setDash([2.5 * MM_TO_PT, 0.5 * MM_TO_PT, 0.5 * MM_TO_PT, 0.5 * MM_TO_PT])
        else:
            c.setDash([])
        kind = entity["kind"]
        if kind == "line":
            c.line(entity["x1"] * MM_TO_PT, entity["y1"] * MM_TO_PT,
                   entity["x2"] * MM_TO_PT, entity["y2"] * MM_TO_PT)
        elif kind == "polyline":
            points = entity["points"]
            if len(points) < 2:
                continue
            path = c.beginPath()
            path.moveTo(points[0][0] * MM_TO_PT, points[0][1] * MM_TO_PT)
            for x, y in points[1:]:
                path.lineTo(x * MM_TO_PT, y * MM_TO_PT)
            if entity.get("closed"):
                path.close()
            c.drawPath(path, stroke=1, fill=0)
        elif kind == "circle":
            c.circle(entity["x"] * MM_TO_PT, entity["y"] * MM_TO_PT,
                     entity["r"] * MM_TO_PT, stroke=1, fill=0)
        elif kind == "solid":
            points = entity["points"]
            if len(points) < 3:
                continue
            path = c.beginPath()
            path.moveTo(points[0][0] * MM_TO_PT, points[0][1] * MM_TO_PT)
            for x, y in points[1:]:
                path.lineTo(x * MM_TO_PT, y * MM_TO_PT)
            path.close()
            c.drawPath(path, stroke=0, fill=1)
        elif kind == "text":
            if entity.get("layer") in {"DIM", "CALLOUT"}:
                preferred = "CRERomansPreview"
                fallback = "Times-Roman"
            else:
                preferred = "CREArialNarrowBold" if entity.get("bold") else "CREArialNarrow"
                fallback = "Helvetica-Bold" if entity.get("bold") else "Helvetica"
            font = preferred if preferred in pdfmetrics.getRegisteredFontNames() else fallback
            size_pt = entity["size"] * MM_TO_PT
            value = entity["value"]
            width = pdfmetrics.stringWidth(value, font, size_pt)
            c.saveState()
            c.translate(entity["x"] * MM_TO_PT, entity["y"] * MM_TO_PT)
            c.rotate(entity.get("rotation", 0.0))
            offset = 0.0
            if entity.get("align") == "center":
                offset = -width / 2
            elif entity.get("align") == "right":
                offset = -width
            c.setFont(font, size_pt)
            c.drawString(offset, 0, value)
            c.restoreState()
    c.showPage()
    c.save()


def render_dxf():
    doc = ezdxf.new("R2010", setup=True)
    doc.units = units.MM
    layer_specs = {
        "BORDER": (7, 35),
        "TITLE": (7, 20),
        "TEXT": (7, 20),
        "LABEL": (7, 20),
        "TABLE": (7, 25),
        "NOTES": (7, 18),
        "SYMBOL": (2, 20),
        "PIPE": (4, 53),
        "DIM": (2, 20),
        "CALLOUT": (3, 35),
        "COMPONENT": (4, 50),
        "COMPANY": (4, 20),
        "HIGHLIGHT": (3, 20),
    }
    for name, (color, lineweight) in layer_specs.items():
        if name not in doc.layers:
            doc.layers.add(
                name,
                color=color,
                lineweight=lineweight,
                linetype="Continuous",
            )
    if "CENTER" not in doc.layers:
        doc.layers.add("CENTER", color=2, lineweight=20, linetype="CENTER")
    if "VIEWPORTS" not in doc.layers:
        doc.layers.add("VIEWPORTS", color=8, lineweight=5, plot=False)

    if "CRE_ARIAL_NARROW" not in doc.styles:
        doc.styles.new("CRE_ARIAL_NARROW", dxfattribs={"font": "Arial Narrow.ttf"})
    if "CRE_ARIAL_NARROW_BOLD" not in doc.styles:
        doc.styles.new(
            "CRE_ARIAL_NARROW_BOLD",
            dxfattribs={"font": "Arial Narrow Bold.ttf"},
        )
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
            e = msp.add_line((entity["x1"], entity["y1"]),
                             (entity["x2"], entity["y2"]),
                             dxfattribs={"layer": layer})
            e.dxf.lineweight = max(5, min(211, round(_effective_width(entity) * 100)))
        elif kind == "polyline":
            e = msp.add_lwpolyline(entity["points"], close=entity.get("closed", False),
                                   dxfattribs={"layer": layer})
            e.dxf.lineweight = max(5, min(211, round(_effective_width(entity) * 100)))
        elif kind == "circle":
            e = msp.add_circle((entity["x"], entity["y"]), entity["r"],
                               dxfattribs={"layer": layer})
            e.dxf.lineweight = max(5, min(211, round(_effective_width(entity) * 100)))
        elif kind == "solid":
            points = entity["points"]
            if len(points) >= 3:
                e = msp.add_solid(
                    points[0], points[1], points[2], points[2],
                    dxfattribs={"layer": layer},
                )
                e.dxf.lineweight = max(
                    5, min(211, round(_effective_width(entity) * 100))
                )
        elif kind == "text":
            if layer in {"CALLOUT", "DIM"}:
                style = "CRE_ROMANS"
            elif entity.get("bold"):
                style = "CRE_ARIAL_NARROW_BOLD"
            else:
                style = "CRE_ARIAL_NARROW"
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
                p1=entity["p1"],
                p2=entity["p2"],
                distance=entity["offset"],
                dimstyle="CRE_PTFE_DIM",
                override={
                    "dimclrd": 2,
                    "dimclre": 2,
                    "dimclrt": 2,
                    "dimtxsty": "CRE_ROMANS",
                },
            )
            dim.dimension.dxf.layer = "DIM"
            dim.dimension.dxf.lineweight = 20
            # The NTS geometry is presentation only; this label is the
            # source-verified fabrication value.
            dim.dimension.dxf.text = entity["label"]
            if "oblique_angle" in entity:
                dim.dimension.dxf.oblique_angle = entity["oblique_angle"]
            dim.render()
    doc.header["$INSUNITS"] = units.MM
    # A real A2 paper-space setup accompanies the 420 x 594 mm model frame.
    paper = doc.layouts.get("Layout1")
    paper.page_setup(
        size=(PAGE_W_MM, PAGE_H_MM),
        margins=(0.0, 0.0, 0.0, 0.0),
        units="mm",
        scale=(1.0, 1.0),
        name="ISO_A2_PORTRAIT",
        device="DWG To PDF.pc3",
    )
    paper.add_viewport(
        center=(PAGE_W_MM / 2.0, PAGE_H_MM / 2.0),
        size=(PAGE_W_MM, PAGE_H_MM),
        view_center_point=(PAGE_W_MM / 2.0, PAGE_H_MM / 2.0),
        view_height=PAGE_H_MM,
        status=2,
        dxfattribs={"layer": "VIEWPORTS"},
    )
    doc.saveas(DXF_PATH)


def render_dwg():
    accoreconsole_path = Path("/Applications/Autodesk/AutoCAD 2027/AutoCAD 2027.app/Contents/Helpers/AcCoreConsole.app/Contents/MacOS/accoreconsole")
    scr_path = ROOT / "work" / "refresh_iso70_dwg.scr"
    if accoreconsole_path.exists() and DXF_PATH.exists() and scr_path.exists():
        cmd = [
            str(accoreconsole_path),
            "/i", str(DXF_PATH.resolve()),
            "/s", str(scr_path.resolve()),
            "/l", "en-US"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Generated DWG via AcCoreConsole: {DWG_PATH}")


if __name__ == "__main__":
    validate_split_source()
    build_reference_sheet()
    render_pdf()
    render_dxf()
    render_dwg()
    render_png()
    print(PDF_PATH)
    print(DXF_PATH)
    print(DWG_PATH)
    print(PNG_PATH)
    print(f"source={SOURCE_PDF}")
    print(f"entities={len(entities)}")
