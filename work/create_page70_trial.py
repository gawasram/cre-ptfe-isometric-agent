from __future__ import annotations

import math
import sys
from pathlib import Path

import pdfplumber
from reportlab.lib.pagesizes import A2, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
import ezdxf
from ezdxf.enums import TextEntityAlignment
from ezdxf import units


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = Path("/Users/ram/Downloads/ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150.pdf")
OUTPUT = ROOT / "outputs"
OUTPUT.mkdir(exist_ok=True)
PDF_PATH = OUTPUT / "ISO_70_PTFE.pdf"
DXF_PATH = OUTPUT / "ISO_70_PTFE.dxf"

MM_TO_PT = 72.0 / 25.4
PAGE_W_MM = 594.0
PAGE_H_MM = 420.0

entities: list[dict] = []


def add_line(x1, y1, x2, y2, layer="OBJECT", width=0.18):
    entities.append({"kind": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "layer": layer, "width": width})


def add_polyline(points, layer="OBJECT", width=0.18, closed=False):
    if len(points) >= 2:
        entities.append({"kind": "polyline", "points": points, "layer": layer, "width": width, "closed": closed})


def add_circle(x, y, r, layer="OBJECT", width=0.18):
    entities.append({"kind": "circle", "x": x, "y": y, "r": r, "layer": layer, "width": width})


def add_text(x, y, value, size=2.5, layer="TEXT", rotation=0.0, bold=False, align="left"):
    entities.append({"kind": "text", "x": x, "y": y, "value": str(value), "size": size, "layer": layer,
                     "rotation": rotation, "bold": bold, "align": align})


def add_rect(x, y, w, h, layer="BORDER", width=0.18):
    add_polyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer, width, closed=True)


def add_table(x, y, widths, row_h, rows, font_size=2.15, header=True):
    total_w = sum(widths)
    total_h = row_h * len(rows)
    add_rect(x, y, total_w, total_h, "TABLE", 0.18)
    cx = x
    for width in widths[:-1]:
        cx += width
        add_line(cx, y, cx, y + total_h, "TABLE", 0.13)
    for idx in range(1, len(rows)):
        add_line(x, y + idx * row_h, x + total_w, y + idx * row_h, "TABLE", 0.13)
    for visual_row, row in enumerate(reversed(rows)):
        baseline = y + visual_row * row_h + (row_h - font_size) / 2
        cx = x
        original_index = len(rows) - 1 - visual_row
        for col, (value, width) in enumerate(zip(row, widths)):
            if col in (0, len(widths) - 1):
                add_text(cx + width / 2, baseline, value, font_size, "TABLE", bold=header and original_index == 0, align="center")
            else:
                add_text(cx + 1.0, baseline, value, font_size, "TABLE", bold=header and original_index == 0)
            cx += width


def import_source_geometry():
    # Crop excludes the original BOM/title block but keeps the complete page-70
    # process isometric, dimensions, tags and callouts as editable vectors.
    crop = (700.0, 450.0, 1640.0, 1150.0)  # PDF points, bottom-left origin
    target_x, target_y = 15.0, 118.0
    scale = min(368.0 / (crop[2] - crop[0]), 274.0 / (crop[3] - crop[1]))

    def transform(x, y):
        return target_x + (x - crop[0]) * scale, target_y + (y - crop[1]) * scale

    def accepted(obj):
        x0, x1 = obj.get("x0", 0.0), obj.get("x1", 0.0)
        y0, y1 = obj.get("y0", 0.0), obj.get("y1", 0.0)
        intersects = x1 >= crop[0] and x0 <= crop[2] and y1 >= crop[1] and y0 <= crop[3]
        not_page_border = max(abs(x1 - x0), abs(y1 - y0)) < 500.0
        return intersects and not_page_border

    with pdfplumber.open(SOURCE_PDF) as pdf:
        page = pdf.pages[69]
        for line in page.lines:
            if not accepted(line):
                continue
            x1, y1 = transform(line["x0"], line["y0"])
            x2, y2 = transform(line["x1"], line["y1"])
            thick = line.get("linewidth", 0.0) > 2.0
            add_line(x1, y1, x2, y2, "SOURCE_PIPE" if thick else "SOURCE_TRACE", 0.62 if thick else 0.12)
        for curve in page.curves:
            if not accepted(curve):
                continue
            # pdfplumber curve points use top-origin coordinates.
            points = [transform(x, page.height - y_top) for x, y_top in curve.get("pts", [])]
            thick = curve.get("linewidth", 0.0) > 2.0
            add_polyline(points, "SOURCE_PIPE" if thick else "SOURCE_TRACE", 0.62 if thick else 0.12,
                         closed=bool(curve.get("fill")))
        for rect in page.rects:
            if not accepted(rect):
                continue
            x1, y1 = transform(rect["x0"], rect["y0"])
            x2, y2 = transform(rect["x1"], rect["y1"])
            add_rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1), "SOURCE_TRACE", 0.12)


def build_sheet():
    add_rect(8, 8, 578, 404, "BORDER", 0.35)
    add_rect(11, 11, 572, 398, "BORDER", 0.18)
    add_text(18, 400, "IF IN ANY DOUBT PLS ASK", 3.0, "TITLE", bold=True)
    add_text(576, 400, "DO NOT SCALE", 3.0, "TITLE", bold=True, align="right")

    import_source_geometry()
    bom_rows = [
        ["IT", "DESCRIPTION", "SIZE", "LENGTH", "QTY"],
        ["1", "PIPE B36.19 SEAMLESS 40S", '1"', "5.1M", "-"],
        ["2", "ECC. REDUCER BW", '1-1/2x1"', "-", "1"],
        ["3", "EQUAL TEE BW", '1x1"', "-", "2"],
        ["4", "REDUCING TEE BW", '1x3/4"', "-", "2"],
        ["5", "90 DEG ELBOW BW", '1"', "-", "6"],
        ["6", "WN FLANGE CL150", '1-1/2"', "-", "1"],
        ["7", "WN FLANGE CL150", '1"', "-", "10"],
        ["8", "WN FLANGE CL150", '3/4"', "-", "2"],
        ["9", "BLIND FLANGE CL150", '3/4"', "-", "2"],
        ["16", "GLOBE VALVE", '1"', "-", "1"],
        ["17", "BALL VALVE", '1"', "-", "2"],
        ["18", "BALL VALVE", '3/4"', "-", "2"],
        ["19", "ORIFICE FLOW ELEMENT", '1"', "-", "2"],
    ]
    add_text(489, 395, "BILL OF MATERIAL", 3.4, "TITLE", bold=True, align="center")
    add_table(397, 270, [10, 101, 25, 24, 14], 8.5, bom_rows, 2.05)

    cut_rows = [
        ["PIECE", "CUT LENGTH", "N.S."],
        ["<11>", "100", '1"'],
        ["<12>", "100", '1"'],
        ["<13>", "625", '1"'],
        ["<14>", "857", '1"'],
        ["<15>", "2576", '1"'],
        ["<16>", "576", '1"'],
        ["<17>", "167", '1"'],
    ]
    add_text(437, 260, "CUT PIPE LENGTHS", 3.0, "TITLE", bold=True, align="center")
    add_table(397, 196, [28, 32, 24], 7.5, cut_rows, 2.15)

    add_text(399, 184, "GENERAL NOTES :-", 3.4, "TITLE", bold=True)
    notes = [
        "1) ALL DIMENSIONS ARE IN MM.",
        "2) FLANGE CONN. DRILLING AS PER ANSI B16.5, CLASS 150.",
        "3) LINING: PTFE LINING AS PER ASTM D4895.",
        "4) TOLERANCES AS PER ASTM F1545.",
        "5) VERIFY FLANGE ORIENTATION, VALVES AND INSTRUMENTS.",
    ]
    for index, note in enumerate(notes):
        add_text(399, 174 - index * 7.2, note, 2.25, "NOTES")
    add_text(399, 132, "INSPECTION", 3.0, "TITLE", bold=True)
    add_line(399, 130, 430, 130, "TITLE", 0.18)
    add_text(401, 123, "- HYDRO TEST: AS PER APPROVED PROCEDURE", 2.1, "NOTES")
    add_text(401, 116, "- SPARK TEST: AS PER APPROVED PROCEDURE", 2.1, "NOTES")

    # Lahu / CRE title-block format reproduced from ISO_31_TO_35.dwg.
    tx, ty, tw, th = 397, 12, 174, 94
    add_rect(tx, ty, tw, th, "BORDER", 0.28)

    # Company / customer / project rows.
    for y in [94, 82, 70]:
        add_line(tx, y, tx + tw, y, "BORDER", 0.16)
    add_text(tx + tw / 2, 98, "CORROSION RESISTANT EQUIPMENT PVT LTD", 3.6,
             "COMPANY", bold=True, align="center")
    add_text(399, 85.5, "CUSTOMER: ENGINEERS INDIA LTD., NEW DELHI", 2.25, "TITLE")
    add_text(399, 73.5, "PROJECT: MIL PROJECT, TNT PLANT, HEF KHADKI, PUNE", 2.15, "TITLE")

    # Approval grid and line-number field.
    add_line(tx, 30, tx + tw, 30, "BORDER", 0.16)
    add_line(tx, 40, 465, 40, "BORDER", 0.13)
    add_line(tx, 50, 465, 50, "BORDER", 0.13)
    add_line(tx, 60, 465, 60, "BORDER", 0.13)
    for x in [415, 439, 450, 465]:
        add_line(x, 30, x, 70, "BORDER", 0.13)
    add_text(427, 62.5, "NAME", 2.0, "TITLE", bold=True, align="center")
    add_text(444.5, 62.5, "SIGN", 2.0, "TITLE", bold=True, align="center")
    add_text(457.5, 62.5, "DATE", 2.0, "TITLE", bold=True, align="center")
    for y, role in [(52.5, "DRAN"), (42.5, "CHK"), (32.5, "APPD.")]:
        add_text(406, y, role, 2.15, "TITLE", bold=True, align="center")
    add_text(427, 52.5, "RAM GAWAS", 1.75, "TITLE", align="center")
    add_text(457.5, 52.5, "14.7.26", 1.75, "TITLE", align="center")
    add_text(468, 56.5, "LINE  NO", 2.8, "HIGHLIGHT", bold=True)
    add_text(468, 44.0, '1"-SNA-424-1501-1-A82Y-A', 2.8, "HIGHLIGHT", bold=True)

    # Scale, first-angle projection, sheet and revision row.
    for x in [449, 487, 550]:
        add_line(x, 12, x, 30, "BORDER", 0.13)
    add_text(423, 19.5, "SCALE=NTS", 2.5, "TITLE", bold=True, align="center")
    add_line(455, 18, 466, 21, "SYMBOL", 0.18)
    add_line(455, 24, 466, 21, "SYMBOL", 0.18)
    add_line(455, 18, 455, 24, "SYMBOL", 0.18)
    add_circle(476, 21, 4.2, "SYMBOL", 0.18)
    add_circle(476, 21, 2.4, "SYMBOL", 0.18)
    add_line(469.5, 21, 482.5, 21, "SYMBOL", 0.13)
    add_line(476, 14.5, 476, 27.5, "SYMBOL", 0.13)
    add_text(518.5, 19.5, "SHEET NO.  2 OF 2", 2.4, "TITLE", bold=True, align="center")
    add_text(560.5, 24.0, "REV.", 2.0, "TITLE", bold=True, align="center")
    add_line(550, 20, 571, 20, "BORDER", 0.13)
    add_text(560.5, 13.8, "0", 2.3, "TITLE", bold=True, align="center")

    # Bottom revision-description table, matching the supplied DWG.
    rx, ry, rw, rh = 11, 12, 386, 18
    add_rect(rx, ry, rw, rh, "BORDER", 0.25)
    add_line(rx, 21, rx + rw, 21, "BORDER", 0.13)
    for x in [35, 300, 330, 360]:
        add_line(x, 12, x, 30, "BORDER", 0.13)
    add_text(23, 14.7, "REV.", 2.5, "TITLE", bold=True, align="center")
    add_text(167.5, 14.7, "DESCRIPTION", 2.5, "TITLE", bold=True, align="center")
    add_text(315, 14.7, "BY", 2.4, "TITLE", bold=True, align="center")
    add_text(345, 14.7, "CHD.", 2.4, "TITLE", bold=True, align="center")
    add_text(378.5, 14.7, "APPD", 2.4, "TITLE", bold=True, align="center")


LAYER_RGB = {
    "REVIEW": (0.85, 0.0, 0.0),
    "SOURCE_TRACE": (0.05, 0.05, 0.05),
    "SOURCE_PIPE": (0.0, 0.0, 0.0),
    "COMPANY": (0.0, 0.0, 0.0),
    "HIGHLIGHT": (0.0, 0.0, 0.0),
}


def render_pdf():
    c = canvas.Canvas(str(PDF_PATH), pagesize=landscape(A2))
    for entity in entities:
        color = LAYER_RGB.get(entity.get("layer"), (0.0, 0.0, 0.0))
        c.setStrokeColorRGB(*color)
        c.setFillColorRGB(*color)
        c.setLineWidth(entity.get("width", 0.18) * MM_TO_PT)
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
            c.circle(entity["x"] * MM_TO_PT, entity["y"] * MM_TO_PT, entity["r"] * MM_TO_PT, stroke=1, fill=0)
        elif kind == "text":
            font = "Helvetica-Bold" if entity.get("bold") else "Helvetica"
            size_pt = entity["size"] * MM_TO_PT
            value = entity["value"]
            width = stringWidth(value, font, size_pt)
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
    for name, color in {
        "BORDER": 7, "TITLE": 7, "TEXT": 7, "LABEL": 7, "TABLE": 7,
        "NOTES": 7, "SYMBOL": 2, "SOURCE_TRACE": 2, "SOURCE_PIPE": 4,
        "COMPANY": 4, "HIGHLIGHT": 3, "REVIEW": 1,
    }.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color)
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
        elif kind == "text":
            text = msp.add_text(entity["value"], dxfattribs={
                "height": entity["size"], "layer": layer, "rotation": entity.get("rotation", 0.0)
            })
            alignment = {
                "left": TextEntityAlignment.LEFT,
                "center": TextEntityAlignment.CENTER,
                "right": TextEntityAlignment.RIGHT,
            }[entity.get("align", "left")]
            text.set_placement((entity["x"], entity["y"]), align=alignment)
    doc.header["$INSUNITS"] = units.MM
    doc.saveas(DXF_PATH)


if __name__ == "__main__":
    build_sheet()
    render_pdf()
    render_dxf()
    print(PDF_PATH)
    print(DXF_PATH)
    print(f"entities={len(entities)}")
