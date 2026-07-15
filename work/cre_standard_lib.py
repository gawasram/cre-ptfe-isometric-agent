"""
CRE PTFE Standard Library
Unified drawing component library for CRE PTFE isometric drafting automation.
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import pdfplumber
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "vendor"))
import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment

PAGE_W_MM = 420.0
PAGE_H_MM = 594.0
MM_TO_PT = 72.0 / 25.4

DIM_TEXT_HEIGHT = 2.1
DIM_ARROW_LENGTH = DIM_TEXT_HEIGHT
DIM_ARROW_BASE = DIM_ARROW_LENGTH / 3.0
DIM_EXT_OFFSET = DIM_TEXT_HEIGHT * 0.5
DIM_EXT_EXCEED = DIM_TEXT_HEIGHT * 0.5
DIM_TEXT_GAP = DIM_TEXT_HEIGHT * 0.4


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
        {"kind": "line", "x1": ax, "y1": ay, "x2": bx, "y2": by, "layer": "DIM", "width": 0.20},
        {"kind": "line", "x1": p1[0] + ev_x * ext_off, "y1": p1[1] + ev_y * ext_off, "x2": ax + ev_x * ext_len, "y2": ay + ev_x * ext_len, "layer": "DIM", "width": 0.20},
        {"kind": "line", "x1": p2[0] + ev_x * ext_off, "y1": p2[1] + ev_y * ext_off, "x2": bx + ev_x * ext_len, "y2": by + ev_x * ext_len, "layer": "DIM", "width": 0.20},
    ]

    half_base = DIM_ARROW_BASE / 2.0
    for tip, inward in (((ax, ay), (ux, uy)), ((bx, by), (-ux, -uy))):
        base_center = (tip[0] + inward[0] * DIM_ARROW_LENGTH, tip[1] + inward[1] * DIM_ARROW_LENGTH)
        result.append({
            "kind": "solid",
            "points": [tip, (base_center[0] + nx * half_base, base_center[1] + ny * half_base), (base_center[0] - nx * half_base, base_center[1] - ny * half_base)],
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


class CREModelBuilder:
    def __init__(self, page_name: str, output_dir: Path):
        self.page_name = page_name
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.pdf_path = self.output_dir / f"{page_name}.pdf"
        self.dxf_path = self.output_dir / f"{page_name}.dxf"
        self.dwg_path = self.output_dir / f"{page_name}.dwg"
        self.png_path = self.output_dir / f"{page_name}.png"
        self.entities: list[dict] = []

    def add_line(self, x1, y1, x2, y2, layer="OBJECT", width=0.18):
        self.entities.append({
            "kind": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "layer": layer, "width": width
        })

    def add_polyline(self, points, layer="OBJECT", width=0.18, closed=False):
        if len(points) >= 2:
            self.entities.append({
                "kind": "polyline", "points": points, "layer": layer,
                "width": width, "closed": closed
            })

    def add_circle(self, x, y, r, layer="OBJECT", width=0.18):
        self.entities.append({
            "kind": "circle", "x": x, "y": y, "r": r,
            "layer": layer, "width": width
        })

    def add_text(self, x, y, value, size=2.5, layer="TEXT", rotation=0.0, bold=False, align="left"):
        self.entities.append({
            "kind": "text", "x": x, "y": y, "value": str(value),
            "size": size, "layer": layer, "rotation": rotation,
            "bold": bold, "align": align
        })

    def add_rect(self, x, y, w, h, layer="BORDER", width=0.18):
        self.add_polyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer, width, closed=True)

    def add_table(self, x, y, widths, row_h, rows, font_size=2.2):
        total_w = sum(widths)
        total_h = row_h * len(rows)
        self.add_rect(x, y, total_w, total_h, "TABLE", 0.25)
        cx = x
        for width in widths[:-1]:
            cx += width
            self.add_line(cx, y, cx, y + total_h, "TABLE", 0.25)
        for index in range(1, len(rows)):
            self.add_line(x, y + index * row_h, x + total_w, y + index * row_h, "TABLE", 0.25)
        for visual_row, row in enumerate(reversed(rows)):
            cy = y + (visual_row + 0.30) * row_h
            rx = x
            for c_idx, cell in enumerate(row):
                is_bold = (visual_row == len(rows) - 1)
                cell_w = widths[c_idx]
                if c_idx in (0, len(row) - 1):
                    self.add_text(rx + cell_w / 2.0, cy, cell, font_size, "TABLE", bold=is_bold, align="center")
                else:
                    self.add_text(rx + 2.0, cy, cell, font_size, "TABLE", bold=is_bold, align="left")
                rx += cell_w

    def add_balloon(self, x, y, label, radius=2.15):
        self.add_circle(x, y, radius, "CALLOUT", 0.35)
        self.add_text(x, y - 0.90, str(label), 2.2, "CALLOUT", bold=True, align="center")

    def add_small_callout(self, number, bubble, target):
        bx, by = bubble
        tx, ty = target
        self.add_line(bx, by, tx, ty, "CALLOUT", 0.20)
        self.add_circle(bx, by, 2.15, "CALLOUT", 0.35)
        self.add_text(bx, by - 0.90, str(number), 1.80, "CALLOUT", bold=True, align="center")

    def add_title_block(self, line_number: str, sheet_number="1 OF 1", drafter="RAM GAWAS", drawing_date="15.7.26", revision="0"):
        self.add_rect(8, 8, 404, 578, "BORDER", 0.35)
        self.add_rect(11, 11, 398, 572, "BORDER", 0.20)
        self.add_rect(11, 568, 112, 13, "BORDER", 0.20)
        self.add_text(67, 571.8, "IF IN ANY DOUBT PLS ASK", 3.75, "TITLE", bold=True, align="center")
        self.add_rect(309, 568, 100, 13, "BORDER", 0.20)
        self.add_text(359, 571.8, "DO NOT SCALE", 3.75, "TITLE", bold=True, align="center")

        tx, ty, tw, th = 215, 12, 190, 79
        self.add_rect(tx, ty, tw, th, "BORDER", 0.35)
        for y in [80, 69, 58, 43, 22]:
            self.add_line(tx, y, tx + tw, y, "BORDER", 0.20)
        self.add_text(tx + tw / 2, 83.0, "CORROSION RESISTANT EQUIPMENT PVT LTD", 4.7, "COMPANY", bold=True, align="center")
        self.add_text(tx + 2, 72.2, "CUSTOMER: ENGINEERS INDIA LTD, NEW DELHI", 2.8, "TITLE", bold=True)
        self.add_text(tx + 2, 61.2, "PROJECT: MIL PROJECT, TNT PLANT, HEF KHADKI, PUNE", 2.6, "TITLE", bold=True)

        grid_right = 287
        self.add_line(grid_right, 22, grid_right, 58, "BORDER", 0.20)
        for y in [31, 40, 49]:
            self.add_line(tx, y, grid_right, y, "BORDER", 0.20)
        for x in [235, 260, 272]:
            self.add_line(x, 22, x, 58, "BORDER", 0.20)
        self.add_text(247.5, 52.2, "NAME", 2.3, "TITLE", bold=True, align="center")
        self.add_text(266, 52.2, "SIGN", 2.3, "TITLE", bold=True, align="center")
        self.add_text(279.5, 52.2, "DATE", 2.3, "TITLE", bold=True, align="center")
        for y, role in [(43.2, "DRAN"), (34.2, "CHK"), (25.2, "APPD.")]:
            self.add_text(225, y, role, 2.4, "TITLE", bold=True, align="center")
        self.add_text(247.5, 43.2, drafter, 2.0, "TITLE", align="center")
        self.add_text(279.5, 43.2, drawing_date, 2.0, "TITLE", align="center")

        self.add_text(292, 48.5, "LINE NO.", 3.1, "HIGHLIGHT", bold=True)
        self.add_text(292, 35.2, line_number, 2.9, "HIGHLIGHT", bold=True)

        for x in [265, 305, 375]:
            self.add_line(x, 12, x, 22, "BORDER", 0.20)
        self.add_text(240, 15.0, "SCALE=NTS", 2.7, "TITLE", bold=True, align="center")

        self.add_line(270, 15, 280, 17, "SYMBOL", 0.20)
        self.add_line(270, 19, 280, 17, "SYMBOL", 0.20)
        self.add_line(270, 15, 270, 19, "SYMBOL", 0.20)
        self.add_circle(293, 17, 3.4, "SYMBOL", 0.20)
        self.add_circle(293, 17, 1.9, "SYMBOL", 0.20)
        self.add_line(287.5, 17, 298.5, 17, "CENTER", 0.20)
        self.add_line(293, 11.5, 293, 22.5, "CENTER", 0.20)

        self.add_text(340, 15.0, f"SHEET NO. {sheet_number}", 2.7, "TITLE", bold=True, align="center")
        self.add_text(390, 18.0, "REV.", 2.3, "TITLE", bold=True, align="center")
        self.add_line(375, 16, 405, 16, "BORDER", 0.20)
        self.add_text(390, 12.5, revision, 2.3, "TITLE", bold=True, align="center")

        rx, ry, rw, rh = 15, 12, 195, 19
        self.add_rect(rx, ry, rw, rh, "BORDER", 0.25)
        self.add_line(rx, 22, rx + rw, 22, "BORDER", 0.20)
        for x in [30.5, 171.4, 182.9, 197.3]:
            self.add_line(x, 12, x, 31, "BORDER", 0.20)
        self.add_text(22.75, 15.0, "REV.", 2.7, "TITLE", bold=True, align="center")
        self.add_text(100.0, 15.0, "DESCRIPTION", 2.7, "TITLE", bold=True, align="center")
        self.add_text(177.0, 15.0, "BY", 2.5, "TITLE", bold=True, align="center")
        self.add_text(190.0, 15.0, "CHD.", 2.4, "TITLE", bold=True, align="center")
        self.add_text(204.0, 15.0, "APPD", 2.2, "TITLE", bold=True, align="center")

        na_x, na_y = 370.0, 540.0
        self.add_rect(na_x - 12, na_y - 12, 24, 24, "BORDER", 0.35)
        self.add_line(na_x - 8, na_y - 8, na_x + 6, na_y + 6, "BORDER", 0.35)
        self.add_polyline([(na_x + 6, na_y + 6), (na_x + 1, na_y + 5), (na_x + 5, na_y + 1)], "BORDER", 0.35, closed=True)
        self.add_text(na_x + 2, na_y + 8, "N", 4.0, "TEXT", bold=True, align="center")

    def export_dxf(self):
        doc = ezdxf.new("R2018", setup=True)
        doc.units = units.MM

        if "CENTER" not in doc.linetypes:
            doc.linetypes.new("CENTER", dxfattribs={"description": "Center ____ _ ____", "pattern": [1.25, 0.5, -0.25, 0.25, -0.25]})

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

        msp = doc.modelspace()
        for entity in self.entities:
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
                pts = entity["points"]
                if len(pts) >= 3:
                    e = msp.add_solid(pts[0], pts[1], pts[2], pts[2], dxfattribs={"layer": layer})
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

        doc.header["$INSUNITS"] = units.MM
        paper = doc.layouts.get("Layout1")
        paper.page_setup(size=(PAGE_W_MM, PAGE_H_MM), margins=(0.0, 0.0, 0.0, 0.0), units="mm", scale=(1.0, 1.0), name="ISO_A2_PORTRAIT", device="DWG To PDF.pc3")
        paper.add_viewport(center=(PAGE_W_MM / 2.0, PAGE_H_MM / 2.0), size=(PAGE_W_MM, PAGE_H_MM), view_center_point=(PAGE_W_MM / 2.0, PAGE_H_MM / 2.0), view_height=PAGE_H_MM, status=2, dxfattribs={"layer": "VIEWPORTS"})

        doc.saveas(self.dxf_path)
        print(f"Generated DXF: {self.dxf_path}")

    def export_pdf_and_png(self):
        expanded_entities = []
        for entity in self.entities:
            if entity["kind"] == "dimension":
                expanded_entities.extend(_dimension_primitives(entity))
            else:
                expanded_entities.append(entity)

        c = canvas.Canvas(str(self.pdf_path), pagesize=(PAGE_W_MM * MM_TO_PT, PAGE_H_MM * MM_TO_PT))
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
        print(f"Generated PDF: {self.pdf_path}")

        with pdfplumber.open(self.pdf_path) as pdf:
            im = pdf.pages[0].to_image(resolution=300)
            im.save(self.png_path)
            print(f"Generated PNG: {self.png_path}")

    def compile_dwg_via_accoreconsole(self):
        scr_path = self.output_dir / f"conv_{self.page_name.lower()}.scr"
        scr_path.write_text(
            f'FILEDIA 0\nDXFIN "{self.dxf_path.resolve()}"\nSAVEAS 2018 "{self.dwg_path.resolve()}"\nQUIT Y\n'
        )
        for candidate in [
            Path("/Applications/Autodesk/AutoCAD 2026/AutoCAD 2026.app/Contents/Helpers/AcCoreConsole.app/Contents/MacOS/accoreconsole"),
            Path("/Applications/Autodesk/AutoCAD 2027/AutoCAD 2027.app/Contents/Helpers/AcCoreConsole.app/Contents/MacOS/accoreconsole"),
        ]:
            if candidate.exists():
                subprocess.run([str(candidate), "/i", str(self.dxf_path.resolve()), "/s", str(scr_path.resolve())],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"Generated DWG via AcCoreConsole: {self.dwg_path}")
                break
