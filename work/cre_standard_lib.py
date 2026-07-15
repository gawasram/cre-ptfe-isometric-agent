"""Page-neutral, validator-compliant CRE PTFE drawing primitives."""

from __future__ import annotations

import math
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

import pdfplumber
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "vendor"))

import ezdxf  # noqa: E402
from ezdxf import units  # noqa: E402
from ezdxf.enums import TextEntityAlignment  # noqa: E402


PAGE_W_MM = 420.0
PAGE_H_MM = 594.0
MM_TO_PT = 72.0 / 25.4

DIM_TEXT_HEIGHT = 2.1
DIM_ARROW_LENGTH = DIM_TEXT_HEIGHT
DIM_ARROW_BASE = DIM_ARROW_LENGTH / 3.0
DIM_EXT_OFFSET = DIM_TEXT_HEIGHT * 0.5
DIM_EXT_EXCEED = DIM_TEXT_HEIGHT * 0.5
DIM_TEXT_GAP = DIM_TEXT_HEIGHT * 0.4
ISOMETRIC_AXIS_TOLERANCE_DEG = 0.2
STANDARD_AXES = (30.0, 90.0, 150.0)

ARIAL_NARROW_PATH = Path("/System/Library/Fonts/Supplemental/Arial Narrow.ttf")
ARIAL_NARROW_BOLD_PATH = Path(
    "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"
)
ROMANS_PREVIEW_PATH = Path(
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
)

LAYER_SPECS = {
    "BORDER": (7, 35, "Continuous"),
    "TABLE": (7, 25, "Continuous"),
    "LABEL": (7, 20, "Continuous"),
    "TEXT": (7, 20, "Continuous"),
    "TITLE": (7, 20, "Continuous"),
    "NOTES": (7, 18, "Continuous"),
    "COMPANY": (4, 20, "Continuous"),
    "HIGHLIGHT": (3, 20, "Continuous"),
    "SYMBOL": (2, 20, "Continuous"),
    "PIPE": (4, 53, "Continuous"),
    "DIM": (2, 20, "Continuous"),
    "CALLOUT": (3, 35, "Continuous"),
    "COMPONENT": (4, 50, "Continuous"),
    "CENTER": (2, 20, "CENTER"),
}

LAYER_WIDTH_RANGES = {
    "PIPE": (0.53, 0.53),
    "COMPONENT": (0.35, 0.50),
    "DIM": (0.20, 0.25),
    "CALLOUT": (0.20, 0.35),
    "TABLE": (0.25, 0.25),
    "BORDER": (0.20, 0.35),
    "CENTER": (0.20, 0.20),
}

LAYER_DEFAULT_WIDTHS = {
    name: lineweight / 100.0
    for name, (_colour, lineweight, _linetype) in LAYER_SPECS.items()
}

AUTOCAD_CONSOLES = (
    Path(
        "/Applications/Autodesk/AutoCAD 2027/AutoCAD 2027.app/Contents/"
        "Helpers/AcCoreConsole.app/Contents/MacOS/accoreconsole"
    ),
    Path(
        "/Applications/Autodesk/AutoCAD 2026/AutoCAD 2026.app/Contents/"
        "Helpers/AcCoreConsole.app/Contents/MacOS/accoreconsole"
    ),
)
AUDIT_OK_RE = re.compile(r"Total\s+errors\s+found\s+0\s+fixed\s+0", re.I)


Point = tuple[float, float]


def move_point(point: Point, angle_deg: float, distance: float) -> Point:
    angle = math.radians(angle_deg)
    return (
        point[0] + math.cos(angle) * distance,
        point[1] + math.sin(angle) * distance,
    )


def midpoint(a: Point, b: Point) -> Point:
    return (float(a[0] + b[0]) / 2.0, float(a[1] + b[1]) / 2.0)


def angular_distance(a: float, b: float) -> float:
    delta = abs((a - b) % 180.0)
    return min(delta, 180.0 - delta)


def segment_axis(p1: Point, p2: Point) -> float:
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    if math.hypot(dx, dy) <= 1e-9:
        raise ValueError("zero-length geometry is not allowed")
    return math.degrees(math.atan2(dy, dx)) % 180.0


def get_default_oblique_angle(p1: Point, p2: Point) -> float:
    """Return the mandatory Group-Code-52 angle for a standard baseline."""
    angle = segment_axis(p1, p2)
    if math.isclose(angle, 30.0, abs_tol=ISOMETRIC_AXIS_TOLERANCE_DEG):
        return 150.0
    if math.isclose(angle, 90.0, abs_tol=ISOMETRIC_AXIS_TOLERANCE_DEG):
        return 30.0
    if math.isclose(angle, 150.0, abs_tol=ISOMETRIC_AXIS_TOLERANCE_DEG):
        return 30.0
    raise ValueError(
        f"dimension baseline is {angle:.6f} degrees; expected 30, 90 or 150. "
        "Pass oblique_angle explicitly only for a source-proven projection."
    )


def balloon_leader_start(bubble: Point, target: Point, radius: float) -> Point:
    """Return the exact circle-perimeter point for a straight leader."""
    dx, dy = target[0] - bubble[0], target[1] - bubble[1]
    distance = math.hypot(dx, dy)
    if distance <= float(radius) + 1e-9:
        raise ValueError("balloon leader target must lie outside the balloon perimeter")
    factor = float(radius) / distance
    return bubble[0] + dx * factor, bubble[1] + dy * factor


def _readable_dimension_angle(angle_deg: float) -> float:
    angle = ((angle_deg + 180.0) % 360.0) - 180.0
    if angle > 90.0:
        angle -= 180.0
    elif angle <= -90.0:
        angle += 180.0
    return angle


def _dimension_primitives(entity: dict) -> list[dict]:
    """Expand one live CAD dimension into equivalent PDF primitives."""
    p1, p2 = entity["p1"], entity["p2"]
    offset = float(entity["offset"])
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        return []
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux

    oblique = math.radians(float(entity["oblique_angle"]))
    ex, ey = math.cos(oblique), math.sin(oblique)
    dot = ex * nx + ey * ny
    if abs(dot) < 1e-4:
        raise ValueError("dimension oblique line is parallel to its baseline")
    shift = offset / dot
    a = (p1[0] + ex * shift, p1[1] + ey * shift)
    b = (p2[0] + ex * shift, p2[1] + ey * shift)

    e_len = math.hypot(ex, ey)
    ev_x, ev_y = ex / e_len, ey / e_len
    if offset < 0:
        ev_x, ev_y = -ev_x, -ev_y

    result = [
        {
            "kind": "line", "x1": a[0], "y1": a[1],
            "x2": b[0], "y2": b[1], "layer": "DIM", "width": 0.20,
        },
        {
            "kind": "line",
            "x1": p1[0] + ev_x * DIM_EXT_OFFSET,
            "y1": p1[1] + ev_y * DIM_EXT_OFFSET,
            "x2": a[0] + ev_x * DIM_EXT_EXCEED,
            "y2": a[1] + ev_y * DIM_EXT_EXCEED,
            "layer": "DIM", "width": 0.20,
        },
        {
            "kind": "line",
            "x1": p2[0] + ev_x * DIM_EXT_OFFSET,
            "y1": p2[1] + ev_y * DIM_EXT_OFFSET,
            "x2": b[0] + ev_x * DIM_EXT_EXCEED,
            "y2": b[1] + ev_y * DIM_EXT_EXCEED,
            "layer": "DIM", "width": 0.20,
        },
    ]

    half_base = DIM_ARROW_BASE / 2.0
    for tip, inward in ((a, (ux, uy)), (b, (-ux, -uy))):
        base = (
            tip[0] + inward[0] * DIM_ARROW_LENGTH,
            tip[1] + inward[1] * DIM_ARROW_LENGTH,
        )
        result.append(
            {
                "kind": "solid",
                "points": [
                    tip,
                    (base[0] + nx * half_base, base[1] + ny * half_base),
                    (base[0] - nx * half_base, base[1] - ny * half_base),
                ],
                "layer": "DIM",
                "width": 0.20,
            }
        )

    side = 1.0 if offset >= 0 else -1.0
    result.append(
        {
            "kind": "text",
            "x": midpoint(a, b)[0] + nx * side * DIM_TEXT_GAP,
            "y": midpoint(a, b)[1] + ny * side * DIM_TEXT_GAP,
            "value": entity["label"],
            "size": DIM_TEXT_HEIGHT,
            "layer": "DIM",
            "rotation": _readable_dimension_angle(math.degrees(math.atan2(dy, dx))),
            "bold": False,
            "align": "center",
        }
    )
    return result


class CREModelBuilder:
    """Build one clean, source-controlled CRE PTFE A2 drawing."""

    def __init__(
        self,
        page_name: str,
        output_dir: Path,
        *,
        allowed_pipe_axes: Iterable[float] = STANDARD_AXES,
    ) -> None:
        if not re.fullmatch(r"ISO_\d+_PTFE", page_name):
            raise ValueError("page_name must use the stable ISO_<number>_PTFE basename")
        self.page_name = page_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_path = self.output_dir / f"{page_name}.pdf"
        self.dxf_path = self.output_dir / f"{page_name}.dxf"
        self.dwg_path = self.output_dir / f"{page_name}.dwg"
        self.png_path = self.output_dir / f"{page_name}.png"
        self.allowed_pipe_axes = tuple(float(axis) % 180.0 for axis in allowed_pipe_axes)
        self.entities: list[dict] = []

    @staticmethod
    def _width(layer: str, requested: float | None) -> float:
        width = LAYER_DEFAULT_WIDTHS.get(layer, 0.18) if requested is None else float(requested)
        limits = LAYER_WIDTH_RANGES.get(layer)
        if limits and not limits[0] - 1e-9 <= width <= limits[1] + 1e-9:
            raise ValueError(
                f"{layer} lineweight {width:.2f} mm is outside "
                f"{limits[0]:.2f}-{limits[1]:.2f} mm"
            )
        return width

    def _check_pipe_segment(self, p1: Point, p2: Point) -> None:
        angle = segment_axis(p1, p2)
        deviation = min(angular_distance(angle, axis) for axis in self.allowed_pipe_axes)
        if deviation > ISOMETRIC_AXIS_TOLERANCE_DEG:
            raise ValueError(
                f"PIPE segment is {angle:.6f} degrees; allowed axes are "
                f"{self.allowed_pipe_axes}"
            )

    def add_line(
        self, x1: float, y1: float, x2: float, y2: float,
        layer: str = "TEXT", width: float | None = None,
    ) -> None:
        p1, p2 = (float(x1), float(y1)), (float(x2), float(y2))
        if math.dist(p1, p2) <= 1e-9:
            raise ValueError("zero-length line is not allowed")
        if layer == "PIPE":
            self._check_pipe_segment(p1, p2)
        self.entities.append(
            {
                "kind": "line", "x1": p1[0], "y1": p1[1],
                "x2": p2[0], "y2": p2[1], "layer": layer,
                "width": self._width(layer, width),
            }
        )

    def add_polyline(
        self, points: Sequence[Point], layer: str = "TEXT",
        width: float | None = None, closed: bool = False,
    ) -> None:
        clean = [(float(x), float(y)) for x, y in points]
        if len(clean) < 2:
            raise ValueError("a polyline needs at least two points")
        segments = list(zip(clean, clean[1:]))
        if closed:
            segments.append((clean[-1], clean[0]))
        if layer == "PIPE":
            for start, end in segments:
                self._check_pipe_segment(start, end)
        self.entities.append(
            {
                "kind": "polyline", "points": clean, "layer": layer,
                "width": self._width(layer, width), "closed": bool(closed),
            }
        )

    def add_circle(
        self, x: float, y: float, radius: float,
        layer: str = "TEXT", width: float | None = None,
    ) -> None:
        if radius <= 0:
            raise ValueError("circle radius must be positive")
        self.entities.append(
            {
                "kind": "circle", "x": float(x), "y": float(y),
                "r": float(radius), "layer": layer,
                "width": self._width(layer, width),
            }
        )

    def add_text(
        self, x: float, y: float, value: object, size: float = 2.5,
        layer: str = "TEXT", rotation: float = 0.0,
        bold: bool = False, align: str = "left",
    ) -> None:
        if align not in {"left", "center", "right"}:
            raise ValueError("text align must be left, center or right")
        if layer in {"CALLOUT", "TABLE", "TITLE", "NOTES", "COMPANY", "HIGHLIGHT"}:
            if abs(float(rotation) % 360.0) > 0.1:
                raise ValueError(f"{layer} text must remain horizontal")
        self.entities.append(
            {
                "kind": "text", "x": float(x), "y": float(y),
                "value": str(value), "size": float(size), "layer": layer,
                "rotation": float(rotation), "bold": bool(bold), "align": align,
            }
        )

    def add_rect(
        self, x: float, y: float, width: float, height: float,
        layer: str = "BORDER", lineweight: float | None = None,
    ) -> None:
        self.add_polyline(
            [(x, y), (x + width, y), (x + width, y + height), (x, y + height)],
            layer, lineweight, closed=True,
        )

    def draw_pipe(self, p1: Point, p2: Point) -> None:
        self.add_line(*p1, *p2, "PIPE", 0.53)

    def add_dimension_pair(
        self, p1: Point, p2: Point, labels: Sequence[object],
        offsets: Sequence[float] = (6.0, 11.0),
        *, oblique_angle: float | None = None,
    ) -> None:
        if len(labels) != len(offsets):
            raise ValueError("dimension labels and offsets must have equal counts")
        segment_axis(p1, p2)
        resolved_oblique = (
            get_default_oblique_angle(p1, p2)
            if oblique_angle is None else float(oblique_angle)
        )
        if not any(
            angular_distance(resolved_oblique, allowed) <= ISOMETRIC_AXIS_TOLERANCE_DEG
            for allowed in (30.0, 150.0)
        ):
            raise ValueError("dimension oblique angle must be 30 or 150 degrees")
        for label, offset in zip(labels, offsets):
            value = str(label).strip()
            if not re.fullmatch(r"\d+", value):
                raise ValueError("dimension label must be a source-verified integer millimetre value")
            self.entities.append(
                {
                    "kind": "dimension", "p1": tuple(map(float, p1)),
                    "p2": tuple(map(float, p2)), "label": value,
                    "offset": float(offset), "oblique_angle": resolved_oblique,
                    "layer": "DIM", "width": 0.20,
                }
            )

    def add_single_dimension(
        self, p1: Point, p2: Point, label: object, offset: float,
        *, oblique_angle: float | None = None,
    ) -> None:
        self.add_dimension_pair(
            p1, p2, (label,), (offset,), oblique_angle=oblique_angle
        )

    def add_small_callout(
        self, number: object, bubble: Point, target: Point, *, radius: float = 2.15,
    ) -> None:
        value = str(number).strip()
        if not re.fullmatch(r"\d+", value):
            raise ValueError("balloon number must contain digits only")
        if not 2.0 <= radius <= 2.35:
            raise ValueError("balloon diameter must remain within 4.0-4.7 mm")
        start = balloon_leader_start(bubble, target, radius)
        self.add_line(*start, *target, "CALLOUT", 0.20)
        self.add_circle(*bubble, radius, "CALLOUT", 0.35)
        self.add_text(
            bubble[0], bubble[1] - 0.90, value, 1.80,
            "CALLOUT", bold=True, align="center",
        )

    def add_balloon(
        self, x: float, y: float, label: object, target: Point,
        *, radius: float = 2.15,
    ) -> None:
        self.add_small_callout(label, (x, y), target, radius=radius)

    def add_table(
        self, x: float, y: float, widths: Sequence[float], row_height: float,
        rows_bottom_to_top: Sequence[Sequence[object]], font_size: float = 2.6,
    ) -> None:
        """Draw a BOM whose first supplied row is the physical bottom/header row."""
        if not rows_bottom_to_top:
            raise ValueError("table needs at least one row")
        if any(len(row) != len(widths) for row in rows_bottom_to_top):
            raise ValueError("each table row must match the column count")
        total_width = sum(widths)
        total_height = row_height * len(rows_bottom_to_top)
        self.add_rect(x, y, total_width, total_height, "TABLE", 0.25)
        cursor = x
        for column_width in widths[:-1]:
            cursor += column_width
            self.add_line(cursor, y, cursor, y + total_height, "TABLE", 0.25)
        for index in range(1, len(rows_bottom_to_top)):
            self.add_line(x, y + index * row_height, x + total_width, y + index * row_height, "TABLE", 0.25)

        for visual_row, row in enumerate(rows_bottom_to_top):
            baseline = y + visual_row * row_height + (row_height - font_size) / 2.0 + font_size * 0.18
            cursor = x
            for column, (value, column_width) in enumerate(zip(row, widths)):
                if column in {0, 2, 3, 4}:
                    self.add_text(cursor + column_width / 2.0, baseline, value, font_size, "TABLE", bold=visual_row == 0, align="center")
                else:
                    self.add_text(cursor + 1.0, baseline, value, font_size, "TABLE", bold=visual_row == 0)
                cursor += column_width

    def add_general_notes(
        self, notes: Sequence[str], *, x: float, heading_y: float,
        heading: str = "GENERAL NOTES :-", line_spacing: float = 5.1,
    ) -> None:
        self.add_text(x, heading_y, heading, 4.0, "TITLE", bold=True)
        self.add_line(x, heading_y - 1.6, x + 38.0, heading_y - 1.6, "TITLE", 0.20)
        for index, note in enumerate(notes):
            self.add_text(x, heading_y - 7.0 - index * line_spacing, note, 2.6, "NOTES")

    def add_flange(self, center: Point, angle_deg: float) -> None:
        angle = math.radians(angle_deg)
        ux, uy = math.cos(angle), math.sin(angle)
        if math.isclose(abs(angle_deg % 180.0), 90.0, abs_tol=1.0):
            fx, fy = math.cos(math.radians(30.0)), math.sin(math.radians(30.0))
        else:
            fx, fy = -uy, ux
        for offset in (-1.4, 1.4):
            cx, cy = center[0] + ux * offset, center[1] + uy * offset
            self.add_line(cx - fx * 4.0, cy - fy * 4.0, cx + fx * 4.0, cy + fy * 4.0, "COMPONENT", 0.35)

    def add_valve(self, center: Point, angle_deg: float, *, globe: bool = False) -> None:
        angle = math.radians(angle_deg)
        ux, uy = math.cos(angle), math.sin(angle)
        nx, ny = -uy, ux
        p1, p2 = move_point(center, angle_deg, -5.0), move_point(center, angle_deg, 5.0)
        top = (center[0] + nx * 4.0, center[1] + ny * 4.0)
        bottom = (center[0] - nx * 4.0, center[1] - ny * 4.0)
        self.add_polyline([p1, top, p2, bottom], "COMPONENT", 0.35, closed=True)
        self.add_circle(*center, 1.2, "COMPONENT", 0.35)
        if globe:
            stem_end = move_point(center, angle_deg + 90.0, 6.0)
            self.add_line(*center, *stem_end, "COMPONENT", 0.35)
            self.add_circle(*stem_end, 1.2, "COMPONENT", 0.35)

    def draw_flanged_valve(
        self, center: Point, angle_deg: float, *, draw_length: float = 14.0,
        globe: bool = False,
    ) -> tuple[Point, Point]:
        p1 = move_point(center, angle_deg, -draw_length / 2.0)
        p2 = move_point(center, angle_deg, draw_length / 2.0)
        self.add_flange(p1, angle_deg)
        self.add_flange(p2, angle_deg)
        self.add_line(*p1, *move_point(center, angle_deg, -5.0), "COMPONENT", 0.40)
        self.add_line(*move_point(center, angle_deg, 5.0), *p2, "COMPONENT", 0.40)
        self.add_valve(center, angle_deg, globe=globe)
        return p1, p2

    def add_tee_symbol(
        self, center: Point, run_angle: float, branch_angle: float, *, reach: float = 4.0,
    ) -> None:
        self.add_line(*move_point(center, run_angle, -reach), *move_point(center, run_angle, reach), "COMPONENT", 0.35)
        self.add_line(*center, *move_point(center, branch_angle, reach), "COMPONENT", 0.35)

    def add_weldolet(self, center: Point, branch_angle: float) -> None:
        self.add_circle(*center, 1.0, "COMPONENT", 0.35)
        self.add_line(*center, *move_point(center, branch_angle, 3.0), "COMPONENT", 0.35)

    def draw_reducer(
        self, p1: Point, p2: Point, *, large_width: float = 7.0,
        small_width: float = 3.8,
    ) -> None:
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length <= 1e-9:
            raise ValueError("reducer endpoints must differ")
        nx, ny = -dy / length, dx / length
        a1 = (p1[0] + nx * large_width / 2.0, p1[1] + ny * large_width / 2.0)
        a2 = (p1[0] - nx * large_width / 2.0, p1[1] - ny * large_width / 2.0)
        b1 = (p2[0] + nx * small_width / 2.0, p2[1] + ny * small_width / 2.0)
        b2 = (p2[0] - nx * small_width / 2.0, p2[1] - ny * small_width / 2.0)
        self.add_line(*a1, *b1, "COMPONENT", 0.35)
        self.add_line(*a2, *b2, "COMPONENT", 0.35)
        self.add_line(*p1, *p2, "COMPONENT", 0.40)

    def add_blind_flange(self, center: Point, angle_deg: float) -> None:
        self.add_flange(center, angle_deg)
        cap = move_point(center, angle_deg, 1.8)
        self.add_line(*move_point(cap, angle_deg + 90.0, -4.2), *move_point(cap, angle_deg + 90.0, 4.2), "COMPONENT", 0.35)

    def add_figure_eight(self, center: Point, angle_deg: float) -> None:
        normal = angle_deg + 90.0
        first = move_point(center, normal, -2.0)
        second = move_point(center, normal, 2.0)
        self.add_circle(*first, 2.0, "COMPONENT", 0.35)
        self.add_circle(*second, 2.0, "COMPONENT", 0.35)

    def add_title_block(
        self, *, line_number: str, sheet_number: str, drafter: str,
        drawing_date: str, revision: str, customer: str, project: str,
        include_north_arrow: bool,
        checker: str = "", approver: str = "",
    ) -> None:
        """Add the CRE frame/title block using only explicitly supplied metadata."""
        self.add_rect(8, 8, 404, 578, "BORDER", 0.35)
        self.add_rect(11, 11, 398, 572, "BORDER", 0.20)
        self.add_rect(11, 568, 112, 13, "BORDER", 0.20)
        self.add_text(67, 571.8, "IF IN ANY DOUBT PLS ASK", 3.75, "TITLE", bold=True, align="center")
        self.add_rect(309, 568, 100, 13, "BORDER", 0.20)
        self.add_text(359, 571.8, "DO NOT SCALE", 3.75, "TITLE", bold=True, align="center")

        tx, tw = 215.0, 190.0
        self.add_rect(tx, 12, tw, 79, "BORDER", 0.35)
        for y in (80, 69, 58, 43, 22):
            self.add_line(tx, y, tx + tw, y, "BORDER", 0.20)
        self.add_text(tx + tw / 2.0, 83.0, "CORROSION RESISTANT EQUIPMENT PVT LTD", 4.7, "COMPANY", bold=True, align="center")
        self.add_text(tx + 2, 72.2, f"CUSTOMER: {customer}", 2.8, "TITLE", bold=True)
        self.add_text(tx + 2, 61.2, f"PROJECT: {project}", 2.6, "TITLE", bold=True)

        grid_right = 287.0
        self.add_line(grid_right, 22, grid_right, 58, "BORDER", 0.20)
        for y in (31, 40, 49):
            self.add_line(tx, y, grid_right, y, "BORDER", 0.20)
        for x in (235, 260, 272):
            self.add_line(x, 22, x, 58, "BORDER", 0.20)
        for x, value in ((247.5, "NAME"), (266.0, "SIGN"), (279.5, "DATE")):
            self.add_text(x, 52.2, value, 2.3, "TITLE", bold=True, align="center")
        for y, role in ((43.2, "DRAN"), (34.2, "CHK"), (25.2, "APPD.")):
            self.add_text(225, y, role, 2.4, "TITLE", bold=True, align="center")
        self.add_text(247.5, 43.2, drafter, 2.0, "TITLE", align="center")
        self.add_text(279.5, 43.2, drawing_date, 2.0, "TITLE", align="center")
        if checker:
            self.add_text(247.5, 34.2, checker, 2.0, "TITLE", align="center")
        if approver:
            self.add_text(247.5, 25.2, approver, 2.0, "TITLE", align="center")

        self.add_text(292, 48.5, "LINE NO.", 3.1, "HIGHLIGHT", bold=True)
        self.add_text(292, 35.2, line_number, 2.9, "HIGHLIGHT", bold=True)
        for x in (265, 305, 375):
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

        self.add_rect(15, 12, 195, 19, "BORDER", 0.25)
        self.add_line(15, 22, 210, 22, "BORDER", 0.20)
        for x in (30.5, 171.4, 182.9, 197.3):
            self.add_line(x, 12, x, 31, "BORDER", 0.20)
        for x, value, size in (
            (22.75, "REV.", 2.7), (100.0, "DESCRIPTION", 2.7),
            (177.0, "BY", 2.5), (190.0, "CHD.", 2.4), (204.0, "APPD", 2.2),
        ):
            self.add_text(x, 15.0, value, size, "TITLE", bold=True, align="center")

        if include_north_arrow:
            north = (370.0, 540.0)
            self.add_rect(north[0] - 12, north[1] - 12, 24, 24, "BORDER", 0.35)
            self.add_line(north[0] - 8, north[1] - 8, north[0] + 6, north[1] + 6, "BORDER", 0.35)
            self.add_polyline(
                [(north[0] + 6, north[1] + 6), (north[0] + 1, north[1] + 5), (north[0] + 5, north[1] + 1)],
                "BORDER", 0.35, closed=True,
            )
            self.add_text(north[0] + 2, north[1] + 8, "N", 4.0, "TEXT", bold=True, align="center")

    def _render_entities(self) -> Iterable[dict]:
        for entity in self.entities:
            if entity["kind"] == "dimension":
                yield from _dimension_primitives(entity)
            else:
                yield entity

    @staticmethod
    def _register_pdf_fonts() -> None:
        registrations = (
            ("CREArialNarrow", ARIAL_NARROW_PATH),
            ("CREArialNarrowBold", ARIAL_NARROW_BOLD_PATH),
            ("CRERomansPreview", ROMANS_PREVIEW_PATH),
        )
        registered = set(pdfmetrics.getRegisteredFontNames())
        for name, path in registrations:
            if name not in registered and path.is_file():
                pdfmetrics.registerFont(TTFont(name, str(path)))

    def export_pdf_and_png(self) -> None:
        """Generate the PDF, then render that final PDF itself to the PNG."""
        self._register_pdf_fonts()
        registered = set(pdfmetrics.getRegisteredFontNames())
        drawing = canvas.Canvas(
            str(self.pdf_path),
            pagesize=(PAGE_W_MM * MM_TO_PT, PAGE_H_MM * MM_TO_PT),
        )
        for entity in self._render_entities():
            kind = entity["kind"]
            drawing.setStrokeColorRGB(0, 0, 0)
            drawing.setFillColorRGB(0, 0, 0)
            drawing.setLineWidth(float(entity.get("width", 0.18)) * MM_TO_PT)
            if entity.get("layer") == "CENTER":
                drawing.setDash([2.5 * MM_TO_PT, 0.5 * MM_TO_PT, 0.5 * MM_TO_PT, 0.5 * MM_TO_PT])
            else:
                drawing.setDash([])

            if kind == "line":
                drawing.line(entity["x1"] * MM_TO_PT, entity["y1"] * MM_TO_PT, entity["x2"] * MM_TO_PT, entity["y2"] * MM_TO_PT)
            elif kind == "polyline":
                path = drawing.beginPath()
                points = entity["points"]
                path.moveTo(points[0][0] * MM_TO_PT, points[0][1] * MM_TO_PT)
                for x, y in points[1:]:
                    path.lineTo(x * MM_TO_PT, y * MM_TO_PT)
                if entity.get("closed"):
                    path.close()
                drawing.drawPath(path, stroke=1, fill=0)
            elif kind == "circle":
                drawing.circle(entity["x"] * MM_TO_PT, entity["y"] * MM_TO_PT, entity["r"] * MM_TO_PT, stroke=1, fill=0)
            elif kind == "solid":
                path = drawing.beginPath()
                points = entity["points"]
                path.moveTo(points[0][0] * MM_TO_PT, points[0][1] * MM_TO_PT)
                for x, y in points[1:]:
                    path.lineTo(x * MM_TO_PT, y * MM_TO_PT)
                path.close()
                drawing.drawPath(path, stroke=0, fill=1)
            elif kind == "text":
                romans = entity.get("layer") in {"DIM", "CALLOUT"}
                preferred = "CRERomansPreview" if romans else (
                    "CREArialNarrowBold" if entity.get("bold") else "CREArialNarrow"
                )
                fallback = "Times-Roman" if romans else (
                    "Helvetica-Bold" if entity.get("bold") else "Helvetica"
                )
                font = preferred if preferred in registered else fallback
                size = entity["size"] * MM_TO_PT
                width = pdfmetrics.stringWidth(entity["value"], font, size)
                offset = 0.0
                if entity.get("align") == "center":
                    offset = -width / 2.0
                elif entity.get("align") == "right":
                    offset = -width
                drawing.saveState()
                drawing.translate(entity["x"] * MM_TO_PT, entity["y"] * MM_TO_PT)
                drawing.rotate(entity.get("rotation", 0.0))
                drawing.setFont(font, size)
                drawing.drawString(offset, 0, entity["value"])
                drawing.restoreState()

        drawing.showPage()
        drawing.save()
        with pdfplumber.open(self.pdf_path) as document:
            if len(document.pages) != 1:
                raise RuntimeError("CRE deliverable PDF must contain exactly one page")
            document.pages[0].to_image(resolution=300).save(self.png_path)
        print(f"Generated PDF: {self.pdf_path}")
        print(f"Rendered final PDF to PNG: {self.png_path}")

    def export_dxf(self) -> None:
        document = ezdxf.new("R2018", setup=True)
        document.units = units.MM
        if "CENTER" not in document.linetypes:
            document.linetypes.new(
                "CENTER",
                dxfattribs={
                    "description": "Center ____ _ ____",
                    "pattern": [1.25, 0.5, -0.25, 0.25, -0.25],
                },
            )
        for name, (colour, lineweight, linetype) in LAYER_SPECS.items():
            if name not in document.layers:
                document.layers.add(name, color=colour, lineweight=lineweight, linetype=linetype)
        if "VIEWPORTS" not in document.layers:
            document.layers.add("VIEWPORTS", color=8, lineweight=5, plot=False)

        if "CRE_ARIAL_NARROW" not in document.styles:
            document.styles.new("CRE_ARIAL_NARROW", dxfattribs={"font": "Arial Narrow.ttf"})
        if "CRE_ARIAL_NARROW_BOLD" not in document.styles:
            document.styles.new("CRE_ARIAL_NARROW_BOLD", dxfattribs={"font": "Arial Narrow Bold.ttf"})
        if "CRE_ROMANS" not in document.styles:
            document.styles.new("CRE_ROMANS", dxfattribs={"font": "romans.shx"})

        if "CRE_PTFE_DIM" not in document.dimstyles:
            document.dimstyles.new(
                "CRE_PTFE_DIM",
                dxfattribs={
                    "dimscale": 1.0, "dimasz": DIM_ARROW_LENGTH,
                    "dimtxt": DIM_TEXT_HEIGHT, "dimexo": DIM_EXT_OFFSET,
                    "dimexe": DIM_EXT_EXCEED, "dimgap": DIM_TEXT_GAP,
                    "dimtad": 1, "dimtofl": 1, "dimsoxd": 1,
                    "dimtix": 0, "dimtih": 0, "dimtoh": 0,
                    "dimdec": 0, "dimlunit": 2, "dimzin": 12,
                    "dimtsz": 0.0, "dimsah": 0,
                    "dimclrd": 2, "dimclre": 2, "dimclrt": 2,
                    "dimlwd": 20, "dimlwe": 20, "dimtxsty": "CRE_ROMANS",
                },
            )

        model = document.modelspace()
        for entity in self.entities:
            layer, kind = entity.get("layer", "0"), entity["kind"]
            created = None
            if kind == "line":
                created = model.add_line((entity["x1"], entity["y1"]), (entity["x2"], entity["y2"]), dxfattribs={"layer": layer})
            elif kind == "polyline":
                created = model.add_lwpolyline(entity["points"], close=entity.get("closed", False), dxfattribs={"layer": layer})
            elif kind == "circle":
                created = model.add_circle((entity["x"], entity["y"]), entity["r"], dxfattribs={"layer": layer})
            elif kind == "solid":
                points = entity["points"]
                created = model.add_solid(points[0], points[1], points[2], points[2], dxfattribs={"layer": layer})
            elif kind == "text":
                style = "CRE_ROMANS" if layer in {"CALLOUT", "DIM"} else (
                    "CRE_ARIAL_NARROW_BOLD" if entity.get("bold") else "CRE_ARIAL_NARROW"
                )
                created = model.add_text(
                    entity["value"],
                    dxfattribs={
                        "height": entity["size"], "layer": layer,
                        "rotation": entity.get("rotation", 0.0), "style": style,
                    },
                )
                created.set_placement(
                    (entity["x"], entity["y"]),
                    align={
                        "left": TextEntityAlignment.LEFT,
                        "center": TextEntityAlignment.CENTER,
                        "right": TextEntityAlignment.RIGHT,
                    }[entity.get("align", "left")],
                )
            elif kind == "dimension":
                dimension = model.add_aligned_dim(
                    p1=entity["p1"], p2=entity["p2"], distance=entity["offset"],
                    dimstyle="CRE_PTFE_DIM",
                    override={
                        "dimclrd": 2, "dimclre": 2, "dimclrt": 2,
                        "dimtxsty": "CRE_ROMANS",
                    },
                )
                dimension.dimension.dxf.layer = "DIM"
                dimension.dimension.dxf.lineweight = 20
                dimension.dimension.dxf.text = entity["label"]
                dimension.dimension.dxf.oblique_angle = entity["oblique_angle"]
                dimension.render()
                continue

            if created is not None and kind != "text":
                created.dxf.lineweight = round(float(entity.get("width", 0.18)) * 100)

        document.header["$INSUNITS"] = units.MM
        paper = document.layouts.get("Layout1")
        paper.page_setup(
            size=(PAGE_W_MM, PAGE_H_MM), margins=(0.0, 0.0, 0.0, 0.0),
            units="mm", scale=(1.0, 1.0), name="ISO_A2_PORTRAIT",
            device="DWG To PDF.pc3",
        )
        paper.add_viewport(
            center=(PAGE_W_MM / 2.0, PAGE_H_MM / 2.0),
            size=(PAGE_W_MM, PAGE_H_MM),
            view_center_point=(PAGE_W_MM / 2.0, PAGE_H_MM / 2.0),
            view_height=PAGE_H_MM, status=2,
            dxfattribs={"layer": "VIEWPORTS"},
        )
        document.saveas(self.dxf_path)
        print(f"Generated DXF: {self.dxf_path}")

    def compile_dwg_via_accoreconsole(self) -> None:
        if not self.dxf_path.is_file():
            raise FileNotFoundError(f"DXF must be generated first: {self.dxf_path}")
        if self.dwg_path.exists():
            raise FileExistsError(
                f"archive the existing same-basename DWG before rebuilding: {self.dwg_path}"
            )
        console = next((path for path in AUTOCAD_CONSOLES if path.is_file()), None)
        if console is None:
            raise FileNotFoundError("AutoCAD 2027/2026 Core Console was not found")

        script_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".scr", prefix="cre_convert_", delete=False,
                encoding="utf-8",
            ) as handle:
                handle.write(
                    "_.FILEDIA\n0\n_.CMDECHO\n1\n_.AUDIT\n_Y\n_.SAVEAS\n2018\n"
                    f"{self.dwg_path.resolve()}\n_.QUIT\n_N\n"
                )
                script_path = Path(handle.name)
            result = subprocess.run(
                [
                    str(console), "/i", str(self.dxf_path.resolve()),
                    "/s", str(script_path), "/l", "en-US",
                ],
                capture_output=True,
                text=True,
            )
        finally:
            if script_path is not None:
                script_path.unlink(missing_ok=True)

        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0 or not self.dwg_path.is_file():
            raise RuntimeError(f"AutoCAD DWG conversion failed:\n{output[-6000:]}")

        # DXF import can normalise the paper-space viewport layer once. The
        # required evidence is a second audit of the saved final DWG reporting
        # zero errors and zero fixes.
        audit_script: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".scr", prefix="cre_final_audit_", delete=False,
                encoding="utf-8",
            ) as handle:
                handle.write("_.FILEDIA\n0\n_.CMDECHO\n1\n_.AUDIT\n_Y\n_.QUIT\n_N\n")
                audit_script = Path(handle.name)
            audit_result = subprocess.run(
                [
                    str(console), "/i", str(self.dwg_path.resolve()),
                    "/s", str(audit_script), "/l", "en-US",
                ],
                capture_output=True,
                text=True,
            )
        finally:
            if audit_script is not None:
                audit_script.unlink(missing_ok=True)
        audit_output = f"{audit_result.stdout}\n{audit_result.stderr}"
        if audit_result.returncode != 0 or not AUDIT_OK_RE.search(audit_output):
            raise RuntimeError(
                "Final DWG did not report 'Total errors found 0 fixed 0'.\n"
                + audit_output[-6000:]
            )
        backup = self.dwg_path.with_suffix(".bak")
        if backup.is_file():
            archive = self.output_dir / "archive" / "audit_backups"
            archive.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup.replace(archive / f"{self.dwg_path.stem}_AUDIT_{stamp}.bak")
        print(f"Generated and audited DWG: {self.dwg_path}")
