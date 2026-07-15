#!/usr/bin/env python3
"""Validate a generated CRE PTFE DXF against the learned client profile."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "vendor"))

import ezdxf  # noqa: E402
from ezdxf import units  # noqa: E402


REQUIRED_LAYERS = {
    "PIPE": (4, 53, "Continuous"),
    "COMPONENT": (4, 50, "Continuous"),
    "DIM": (2, 20, "Continuous"),
    "CALLOUT": (3, 35, "Continuous"),
    "TABLE": (7, 25, "Continuous"),
    "BORDER": (7, 35, "Continuous"),
    "CENTER": (2, 20, "CENTER"),
}

ENTITY_WEIGHT_RANGES = {
    "PIPE": (53, 53),
    "COMPONENT": (35, 50),
    "DIM": (20, 25),
    "CALLOUT": (20, 35),
    "TABLE": (25, 25),
    "BORDER": (20, 35),
    "CENTER": (20, 20),
}

STANDARD_ISOMETRIC_AXES = (30.0, 90.0, 150.0)
STANDARD_OBLIQUE_BY_BASELINE = {
    30.0: (150.0,),
    90.0: (30.0,),
    150.0: (30.0,),
}
ROMANS_LAYERS = {"DIM", "CALLOUT"}
ARIAL_LAYERS = {"TABLE", "TITLE", "NOTES", "COMPANY", "HIGHLIGHT", "LABEL", "TEXT"}
HORIZONTAL_LAYERS = {"TABLE", "TITLE", "NOTES", "CALLOUT", "COMPANY", "HIGHLIGHT"}
BALLOON_CLEARANCE_MM = 0.15
BALLOON_ENDPOINT_TOLERANCE_MM = 0.08
MTEXT_FONT_OVERRIDE_RE = re.compile(r"\\[fF]([^;]+);")


def angle_180(start: Any, end: Any) -> float:
    return math.degrees(math.atan2(end.y - start.y, end.x - start.x)) % 180.0


def angular_distance(a: float, b: float) -> float:
    delta = abs((a - b) % 180.0)
    return min(delta, 180.0 - delta)


def rotation_distance(a: float, b: float = 0.0) -> float:
    """Shortest directed-text rotation distance on a full 360-degree turn."""
    delta = abs((a - b) % 360.0)
    return min(delta, 360.0 - delta)


def _xy(point: Any) -> tuple[float, float]:
    return float(point.x), float(point.y)


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _point_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-18:
        return _distance(point, start)
    t = (
        (point[0] - start[0]) * dx + (point[1] - start[1]) * dy
    ) / length_sq
    t = min(1.0, max(0.0, t))
    nearest = (start[0] + t * dx, start[1] + t * dy)
    return _distance(point, nearest)


def _segment_intersection_parameters(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> tuple[float, float] | None:
    """Return segment parameters for a proper 2-D intersection."""
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    denominator = r[0] * s[1] - r[1] * s[0]
    if abs(denominator) <= 1e-9:
        return None
    qmp = (c[0] - a[0], c[1] - a[1])
    t = (qmp[0] * s[1] - qmp[1] * s[0]) / denominator
    u = (qmp[0] * r[1] - qmp[1] * r[0]) / denominator
    if -1e-9 <= t <= 1.0 + 1e-9 and -1e-9 <= u <= 1.0 + 1e-9:
        return t, u
    return None


def _text_rotation(entity: Any) -> float:
    """Read TEXT and MTEXT rotation without treating MTEXT as zero."""
    if entity.dxftype() == "MTEXT":
        try:
            return float(entity.get_rotation()) % 360.0
        except (AttributeError, TypeError, ValueError):
            direction = entity.dxf.get("text_direction", None)
            if direction is not None:
                return math.degrees(math.atan2(direction.y, direction.x)) % 360.0
    return float(entity.dxf.get("rotation", 0.0)) % 360.0


def _plain_text(entity: Any) -> str:
    try:
        value = entity.plain_text()
    except (AttributeError, TypeError):
        value = entity.dxf.get("text", "")
    return str(value).replace("\\P", "\n")


def _mtext_font_overrides(entity: Any) -> list[str]:
    if entity.dxftype() != "MTEXT":
        return []
    raw = str(getattr(entity, "text", entity.dxf.get("text", "")))
    fonts = []
    for specification in MTEXT_FONT_OVERRIDE_RE.findall(raw):
        family = specification.split("|")[0].strip()
        if family:
            fonts.append(family)
    return fonts


def _text_height(entity: Any) -> float:
    if entity.dxftype() == "MTEXT":
        return float(entity.dxf.get("char_height", 0.0))
    return float(entity.dxf.get("height", 0.0))


def _text_anchor(entity: Any) -> tuple[float, float]:
    if entity.dxftype() == "TEXT":
        try:
            _alignment, point, _second = entity.get_placement()
            return _xy(point)
        except (AttributeError, TypeError, ValueError):
            return _xy(entity.dxf.insert)
    return _xy(entity.dxf.insert)


def _text_visual_center(entity: Any) -> tuple[float, float]:
    """Approximate the visual centre used to validate balloon centring."""
    anchor = _text_anchor(entity)
    height = _text_height(entity)
    rotation = math.radians(_text_rotation(entity))
    if entity.dxftype() == "MTEXT":
        # Attachment point 5 is MIDDLE_CENTER. Other attachments are rejected
        # for balloon numbers, so their insertion point is still the useful
        # nearest-candidate location for diagnostics.
        return anchor
    return (
        anchor[0] - math.sin(rotation) * height * 0.5,
        anchor[1] + math.cos(rotation) * height * 0.5,
    )


def _text_is_center_aligned(entity: Any) -> bool:
    if entity.dxftype() == "MTEXT":
        return int(entity.dxf.get("attachment_point", 1)) == 5
    try:
        alignment, _point, _second = entity.get_placement()
        return getattr(alignment, "name", str(alignment)) in {
            "CENTER",
            "MIDDLE",
            "MIDDLE_CENTER",
        }
    except (AttributeError, TypeError, ValueError):
        return False


def _text_box(entity: Any) -> list[tuple[float, float]]:
    """Return a conservative rotated text rectangle in drawing millimetres."""
    value = _plain_text(entity)
    lines = value.splitlines() or [value]
    height = max(_text_height(entity), 0.01)
    width = max((len(line) for line in lines), default=1) * height * 0.55
    total_height = height * max(1, len(lines))
    anchor = _text_anchor(entity)

    if entity.dxftype() == "MTEXT":
        attachment = int(entity.dxf.get("attachment_point", 1))
        column = (attachment - 1) % 3
        row = (attachment - 1) // 3
        x0 = (0.0, -width / 2.0, -width)[column]
        y1 = (0.0, total_height / 2.0, total_height)[row]
        y0 = y1 - total_height
    else:
        try:
            alignment, _point, _second = entity.get_placement()
            name = getattr(alignment, "name", str(alignment))
        except (AttributeError, TypeError, ValueError):
            name = "LEFT"
        if "RIGHT" in name:
            x0 = -width
        elif "CENTER" in name or name == "MIDDLE":
            x0 = -width / 2.0
        else:
            x0 = 0.0
        y0 = 0.0
        y1 = total_height

    angle = math.radians(_text_rotation(entity))
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    corners = []
    for x, y in ((x0, y0), (x0 + width, y0), (x0 + width, y1), (x0, y1)):
        corners.append(
            (
                anchor[0] + x * cos_a - y * sin_a,
                anchor[1] + x * sin_a + y * cos_a,
            )
        )
    return corners


def _point_polygon_distance(
    point: tuple[float, float], polygon: list[tuple[float, float]]
) -> float:
    inside = False
    px, py = point
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        if (start[1] > py) != (end[1] > py):
            crossing_x = (
                (end[0] - start[0]) * (py - start[1])
                / (end[1] - start[1])
                + start[0]
            )
            if px < crossing_x:
                inside = not inside
    if inside:
        return 0.0
    return min(
        _point_segment_distance(point, polygon[i], polygon[(i + 1) % len(polygon)])
        for i in range(len(polygon))
    )


def _mtext_override_matches_role(font: str, expected_role: str) -> bool:
    normalised = Path(font).name.lower().replace(" ", "")
    if expected_role == "romans":
        return normalised in {"romans", "romans.shx"}
    return "arialnarrow" in normalised


def validate(
    path: Path,
    *,
    extra_axes: list[float],
    axis_tolerance: float,
    allow_pipe_curves: bool,
) -> dict[str, Any]:
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    errors: list[str] = []
    warnings: list[str] = []
    evidence: dict[str, Any] = {}

    auditor = doc.audit()
    evidence["dxf_audit_errors"] = len(auditor.errors)
    evidence["dxf_audit_fixes"] = len(auditor.fixes)
    if auditor.errors or auditor.fixes:
        errors.append(
            f"DXF audit is not clean: {len(auditor.errors)} errors, "
            f"{len(auditor.fixes)} fixes"
        )

    evidence["insunits"] = doc.header.get("$INSUNITS")
    if doc.header.get("$INSUNITS") != units.MM:
        errors.append("$INSUNITS must be millimetres (4)")

    layer_evidence = {}
    for name, expected in REQUIRED_LAYERS.items():
        if name not in doc.layers:
            errors.append(f"required layer is missing: {name}")
            continue
        layer = doc.layers.get(name)
        actual = (layer.color, layer.dxf.lineweight, layer.dxf.linetype)
        layer_evidence[name] = actual
        if actual != expected:
            errors.append(f"layer {name} is {actual}, expected {expected}")
    evidence["layers"] = layer_evidence

    a2_layouts = []
    a2_full_sheet_viewports = []
    for layout in doc.layouts:
        if layout.name == "Model":
            continue
        dxf = layout.dxf_layout.dxf
        width = float(dxf.get("paper_width", 0.0))
        height = float(dxf.get("paper_height", 0.0))
        if abs(width - 420.0) <= 1.0 and abs(height - 594.0) <= 1.0:
            a2_layouts.append(layout.name)
            for viewport in layout.query("VIEWPORT"):
                # ID 1 is AutoCAD's required paperspace control viewport. A
                # separate viewport must map the complete model sheet at 1:1.
                if int(viewport.dxf.get("id", 1)) == 1:
                    continue
                center = viewport.dxf.center
                view_center = viewport.dxf.view_center_point
                viewport_width = float(viewport.dxf.get("width", 0.0))
                viewport_height = float(viewport.dxf.get("height", 0.0))
                view_height = float(viewport.dxf.get("view_height", 0.0))
                if (
                    math.isclose(viewport_width, 420.0, abs_tol=0.05)
                    and math.isclose(viewport_height, 594.0, abs_tol=0.05)
                    and math.isclose(view_height, 594.0, abs_tol=0.05)
                    and math.isclose(float(center.x), 210.0, abs_tol=0.05)
                    and math.isclose(float(center.y), 297.0, abs_tol=0.05)
                    and math.isclose(float(view_center.x), 210.0, abs_tol=0.05)
                    and math.isclose(float(view_center.y), 297.0, abs_tol=0.05)
                ):
                    a2_full_sheet_viewports.append(layout.name)
    evidence["a2_portrait_layouts"] = a2_layouts
    evidence["a2_full_sheet_1to1_viewports"] = a2_full_sheet_viewports
    if not a2_layouts:
        errors.append("no 420 x 594 mm A2 portrait paper-space setup found")
    elif not a2_full_sheet_viewports:
        errors.append("no full-sheet 420 x 594 mm A2 viewport at 1:1 found")

    expected_text_styles = {
        "CRE_ARIAL_NARROW": "arial narrow.ttf",
        "CRE_ARIAL_NARROW_BOLD": "arial narrow bold.ttf",
        "CRE_ROMANS": "romans.shx",
    }
    text_style_evidence = {}
    for name, expected_font in expected_text_styles.items():
        if name not in doc.styles:
            errors.append(f"required text style is missing: {name}")
            continue
        actual_font = str(doc.styles.get(name).dxf.get("font", ""))
        text_style_evidence[name] = actual_font
        if Path(actual_font).name.lower() != expected_font:
            errors.append(
                f"text style {name} uses {actual_font!r}, expected {expected_font!r}"
            )
    evidence["text_styles"] = text_style_evidence

    dimensions = list(msp.query("DIMENSION"))
    evidence["dimension_count"] = len(dimensions)
    if not dimensions:
        errors.append("no editable DIMENSION entities found")
    arrow_count = 0
    bad_dimension_labels = []
    bad_dimension_styles = []
    bad_oblique_dimensions = []
    bad_virtual_dimension_text = []
    virtual_dimension_texts: list[tuple[Any, str]] = []
    virtual_dimension_lines: list[dict[str, Any]] = []
    allowed_dimension_axes = list(STANDARD_ISOMETRIC_AXES) + [
        axis % 180.0 for axis in extra_axes
    ]
    for dimension in dimensions:
        label = dimension.dxf.get("text", "")
        if not re.fullmatch(r"\s*\d+\s*", label or ""):
            bad_dimension_labels.append(
                {"handle": dimension.dxf.handle, "text": label}
            )

        baseline_angle = None
        try:
            baseline_angle = angle_180(
                dimension.dxf.defpoint2, dimension.dxf.defpoint3
            )
        except (AttributeError, TypeError, ValueError):
            pass
        oblique_angle = float(dimension.dxf.get("oblique_angle", 0.0)) % 180.0
        baseline_axis = None
        if baseline_angle is not None:
            matches = [
                axis
                for axis in allowed_dimension_axes
                if angular_distance(baseline_angle, axis) <= axis_tolerance
            ]
            if matches:
                baseline_axis = min(
                    matches, key=lambda axis: angular_distance(baseline_angle, axis)
                )

        expected_obliques: tuple[float, ...] = ()
        if baseline_axis is not None:
            standard_match = next(
                (
                    axis
                    for axis in STANDARD_ISOMETRIC_AXES
                    if angular_distance(baseline_axis, axis) <= axis_tolerance
                ),
                None,
            )
            if standard_match is not None:
                expected_obliques = STANDARD_OBLIQUE_BY_BASELINE[standard_match]
            else:
                # A source-proven projection axis still has to use one of the
                # client's two isometric extension-line directions.
                expected_obliques = (30.0, 150.0)

        if baseline_axis is None or not any(
            angular_distance(oblique_angle, expected) <= axis_tolerance
            for expected in expected_obliques
        ):
            bad_oblique_dimensions.append(
                {
                    "handle": dimension.dxf.handle,
                    "baseline_angle": (
                        None if baseline_angle is None else round(baseline_angle, 6)
                    ),
                    "matched_baseline_axis": baseline_axis,
                    "oblique_angle": round(oblique_angle, 6),
                    "expected_oblique": list(expected_obliques),
                }
            )
        try:
            style = dimension.get_dim_style()
            style_values = {
                "dimasz": float(style.dxf.get("dimasz", 0.0)),
                "dimtxt": float(style.dxf.get("dimtxt", 0.0)),
                "dimexo": float(style.dxf.get("dimexo", 0.0)),
                "dimexe": float(style.dxf.get("dimexe", 0.0)),
                "dimgap": float(style.dxf.get("dimgap", 0.0)),
                "dimtad": int(style.dxf.get("dimtad", 0)),
                "dimdec": int(style.dxf.get("dimdec", 0)),
                "dimtsz": float(style.dxf.get("dimtsz", 0.0)),
            }
            if not (
                2.0 <= style_values["dimtxt"] <= 2.2
                and math.isclose(
                    style_values["dimasz"], style_values["dimtxt"], abs_tol=0.05
                )
                and math.isclose(
                    style_values["dimexo"], style_values["dimtxt"] * 0.5, abs_tol=0.06
                )
                and math.isclose(
                    style_values["dimexe"], style_values["dimtxt"] * 0.5, abs_tol=0.06
                )
                and math.isclose(
                    style_values["dimgap"], style_values["dimtxt"] * 0.4, abs_tol=0.06
                )
                and style_values["dimtad"] == 1
                and style_values["dimdec"] == 0
                and math.isclose(style_values["dimtsz"], 0.0, abs_tol=1e-9)
                and style.dxf.get("dimtxsty", "") == "CRE_ROMANS"
            ):
                bad_dimension_styles.append(
                    {"handle": dimension.dxf.handle, "style": style.dxf.name, **style_values}
                )
        except Exception as exc:
            bad_dimension_styles.append(
                {"handle": dimension.dxf.handle, "error": str(exc)}
            )

        try:
            block = doc.blocks.get(dimension.dxf.geometry)
            closed = [
                insert
                for insert in block.query("INSERT")
                if "CLOSED" in insert.dxf.name.upper()
            ]
            solids = list(block.query("SOLID"))
            arrow_count += len(closed) + len(solids)
            if len(closed) + len(solids) < 2:
                errors.append(
                    f"dimension {dimension.dxf.handle} lacks two closed-filled arrows"
                )
        except Exception as exc:
            errors.append(
                f"cannot inspect arrows for dimension {dimension.dxf.handle}: {exc}"
            )

        try:
            virtual_entities = list(dimension.virtual_entities())
        except Exception as exc:
            bad_virtual_dimension_text.append(
                {"handle": dimension.dxf.handle, "error": str(exc)}
            )
            virtual_entities = []

        dimension_text = [
            entity
            for entity in virtual_entities
            if entity.dxftype() in {"TEXT", "MTEXT"}
            and re.search(r"\d", _plain_text(entity))
        ]
        virtual_dimension_texts.extend(
            (entity, str(dimension.dxf.handle)) for entity in dimension_text
        )
        for index, entity in enumerate(virtual_entities):
            if entity.dxftype() == "LINE":
                virtual_dimension_lines.append(
                    {
                        "handle": f"{dimension.dxf.handle}:V{index}",
                        "start": _xy(entity.dxf.start),
                        "end": _xy(entity.dxf.end),
                        "layer": "DIM",
                    }
                )

        if not dimension_text:
            bad_virtual_dimension_text.append(
                {"handle": dimension.dxf.handle, "error": "no rendered dimension text"}
            )
        else:
            rendered_labels = {_plain_text(entity).strip() for entity in dimension_text}
            if str(label).strip() not in rendered_labels:
                bad_virtual_dimension_text.append(
                    {
                        "handle": dimension.dxf.handle,
                        "error": "rendered text does not match explicit source label",
                        "rendered": sorted(rendered_labels),
                        "expected": str(label).strip(),
                    }
                )
            for entity in dimension_text:
                style_name = str(entity.dxf.get("style", ""))
                font_overrides = _mtext_font_overrides(entity)
                rotation = _text_rotation(entity)
                height = _text_height(entity)
                reasons = []
                if style_name != "CRE_ROMANS":
                    reasons.append(f"style={style_name!r}")
                if any(
                    not _mtext_override_matches_role(font, "romans")
                    for font in font_overrides
                ):
                    reasons.append(f"font_overrides={font_overrides!r}")
                if not 2.0 <= height <= 2.2:
                    reasons.append(f"height={height:.3f}")
                if baseline_angle is None or angular_distance(
                    rotation, baseline_angle
                ) > 1.0:
                    reasons.append(
                        f"rotation={rotation:.3f}, baseline={baseline_angle!r}"
                    )
                if reasons:
                    bad_virtual_dimension_text.append(
                        {
                            "handle": dimension.dxf.handle,
                            "virtual_type": entity.dxftype(),
                            "reasons": reasons,
                        }
                    )

    evidence["closed_filled_arrow_count"] = arrow_count
    evidence["bad_dimension_labels"] = bad_dimension_labels
    evidence["bad_dimension_styles"] = bad_dimension_styles
    evidence["bad_oblique_dimensions"] = bad_oblique_dimensions
    evidence["virtual_dimension_text_count"] = len(virtual_dimension_texts)
    evidence["bad_virtual_dimension_text"] = bad_virtual_dimension_text
    if bad_dimension_labels:
        errors.append(
            f"{len(bad_dimension_labels)} dimensions lack explicit integer source labels"
        )
    if bad_dimension_styles:
        errors.append(
            f"{len(bad_dimension_styles)} dimensions do not match the CRE ratio/style"
        )
    if bad_oblique_dimensions:
        errors.append(
            f"{len(bad_oblique_dimensions)} dimensions have an invalid baseline/Group-Code-52 oblique pairing"
        )
    if bad_virtual_dimension_text:
        errors.append(
            f"{len(bad_virtual_dimension_text)} rendered dimension-text checks failed"
        )

    allowed_axes = [30.0, 90.0, 150.0] + [axis % 180.0 for axis in extra_axes]
    bad_pipe_axes = []
    pipe_lines = list(msp.query('LINE[layer=="PIPE"]'))
    for line in pipe_lines:
        angle = angle_180(line.dxf.start, line.dxf.end)
        deviation = min(angular_distance(angle, axis) for axis in allowed_axes)
        if deviation > axis_tolerance:
            bad_pipe_axes.append(
                {
                    "handle": line.dxf.handle,
                    "angle": round(angle, 6),
                    "deviation": round(deviation, 6),
                }
            )
    pipe_polyline_segments = 0
    for polyline in msp.query('LWPOLYLINE[layer=="PIPE"]'):
        points = [(float(x), float(y)) for x, y, *_rest in polyline.get_points()]
        if polyline.closed and points:
            points.append(points[0])
        for index, (start, end) in enumerate(zip(points, points[1:])):
            pipe_polyline_segments += 1
            if _distance(start, end) <= 1e-9:
                bad_pipe_axes.append(
                    {
                        "handle": f"{polyline.dxf.handle}:S{index}",
                        "angle": None,
                        "deviation": None,
                        "reason": "zero-length PIPE polyline segment",
                    }
                )
                continue
            angle = math.degrees(
                math.atan2(end[1] - start[1], end[0] - start[0])
            ) % 180.0
            deviation = min(angular_distance(angle, axis) for axis in allowed_axes)
            if deviation > axis_tolerance:
                bad_pipe_axes.append(
                    {
                        "handle": f"{polyline.dxf.handle}:S{index}",
                        "angle": round(angle, 6),
                        "deviation": round(deviation, 6),
                    }
                )
    evidence["pipe_line_count"] = len(pipe_lines)
    evidence["pipe_polyline_segment_count"] = pipe_polyline_segments
    evidence["allowed_pipe_axes"] = allowed_axes
    evidence["bad_pipe_axes"] = bad_pipe_axes
    if bad_pipe_axes:
        errors.append(f"{len(bad_pipe_axes)} PIPE lines are off the allowed axes")

    pipe_curves = [
        entity
        for entity in msp
        if entity.dxf.get("layer", "0") == "PIPE"
        and entity.dxftype() in {"ARC", "SPLINE", "ELLIPSE"}
    ]
    evidence["pipe_curve_count"] = len(pipe_curves)
    if pipe_curves and not allow_pipe_curves:
        errors.append(
            f"{len(pipe_curves)} PIPE curves found without --allow-pipe-curves"
        )

    callout_ellipses = list(msp.query('ELLIPSE[layer=="CALLOUT"]'))
    evidence["callout_ellipse_count"] = len(callout_ellipses)
    if callout_ellipses:
        errors.append("CALLOUT balloons must be true circles, not ellipses")

    balloon_circles = list(msp.query('CIRCLE[layer=="CALLOUT"]'))
    bad_balloons = [
        {
            "handle": circle.dxf.handle,
            "diameter": round(float(circle.dxf.radius) * 2.0, 3),
        }
        for circle in balloon_circles
        if not 4.0 <= float(circle.dxf.radius) * 2.0 <= 4.7
    ]
    evidence["balloon_circle_count"] = len(balloon_circles)
    evidence["bad_balloon_diameters"] = bad_balloons
    if not balloon_circles:
        errors.append("no true-circle CALLOUT balloons found")
    if bad_balloons:
        errors.append(f"{len(bad_balloons)} balloon circles are outside 4.0-4.7 mm")

    callout_texts = [
        entity
        for entity in msp.query("TEXT MTEXT")
        if str(entity.dxf.get("layer", "0")) == "CALLOUT"
    ]
    callout_lines = list(msp.query('LINE[layer=="CALLOUT"]'))
    bad_balloon_numbers = []
    bad_balloon_leaders = []
    balloon_matches: dict[str, dict[str, Any]] = {}
    assigned_number_handles: set[str] = set()

    for circle in balloon_circles:
        circle_handle = str(circle.dxf.handle)
        center = _xy(circle.dxf.center)
        radius = float(circle.dxf.radius)

        number_candidates = []
        for text_entity in callout_texts:
            value = _plain_text(text_entity).strip()
            if not re.fullmatch(r"\d+", value):
                continue
            visual_center = _text_visual_center(text_entity)
            distance = _distance(center, visual_center)
            if distance <= radius + 0.5:
                number_candidates.append((distance, text_entity, visual_center))
        number_candidates.sort(key=lambda item: item[0])

        matched_number = number_candidates[0][1] if number_candidates else None
        if matched_number is None:
            bad_balloon_numbers.append(
                {"circle": circle_handle, "reason": "no numeric CALLOUT text in bubble"}
            )
        else:
            number_handle = str(matched_number.dxf.handle)
            distance = number_candidates[0][0]
            height = _text_height(matched_number)
            rotation = _text_rotation(matched_number)
            style = str(matched_number.dxf.get("style", ""))
            overrides = _mtext_font_overrides(matched_number)
            reasons = []
            if number_handle in assigned_number_handles:
                reasons.append("same number text matched to another balloon")
            assigned_number_handles.add(number_handle)
            if distance > 0.20:
                reasons.append(f"visual centre offset={distance:.3f} mm")
            if not _text_is_center_aligned(matched_number):
                reasons.append("text is not centre-aligned")
            if not 1.7 <= height <= 1.9:
                reasons.append(f"height={height:.3f} mm")
            if style != "CRE_ROMANS":
                reasons.append(f"style={style!r}")
            if any(
                not _mtext_override_matches_role(font, "romans")
                for font in overrides
            ):
                reasons.append(f"font_overrides={overrides!r}")
            if rotation_distance(rotation) > 0.1:
                reasons.append(f"rotation={rotation:.3f} degrees")
            if reasons:
                bad_balloon_numbers.append(
                    {
                        "circle": circle_handle,
                        "text": number_handle,
                        "value": _plain_text(matched_number).strip(),
                        "reasons": reasons,
                    }
                )

        leader_candidates = []
        for line in callout_lines:
            start = _xy(line.dxf.start)
            end = _xy(line.dxf.end)
            start_delta = abs(_distance(center, start) - radius)
            end_delta = abs(_distance(center, end) - radius)
            if (
                start_delta <= BALLOON_ENDPOINT_TOLERANCE_MM
                and _distance(center, end) > radius + BALLOON_ENDPOINT_TOLERANCE_MM
            ):
                leader_candidates.append((start_delta, line, start, end, "start"))
            elif (
                end_delta <= BALLOON_ENDPOINT_TOLERANCE_MM
                and _distance(center, start) > radius + BALLOON_ENDPOINT_TOLERANCE_MM
            ):
                leader_candidates.append((end_delta, line, end, start, "end"))
        leader_candidates.sort(key=lambda item: item[0])
        if not leader_candidates:
            bad_balloon_leaders.append(
                {
                    "circle": circle_handle,
                    "reason": "no straight CALLOUT leader endpoint on perimeter",
                }
            )
            matched_leader = None
        else:
            matched_leader = leader_candidates[0]
            if len(leader_candidates) > 1:
                bad_balloon_leaders.append(
                    {
                        "circle": circle_handle,
                        "reason": "multiple leaders terminate on one balloon",
                        "leaders": [str(item[1].dxf.handle) for item in leader_candidates],
                    }
                )

        balloon_matches[circle_handle] = {
            "center": center,
            "radius": radius,
            "number": matched_number,
            "leader": matched_leader,
        }

    evidence["bad_balloon_numbers"] = bad_balloon_numbers
    evidence["bad_balloon_leaders"] = bad_balloon_leaders
    if bad_balloon_numbers:
        errors.append(
            f"{len(bad_balloon_numbers)} balloon number size/style/centring/upright checks failed"
        )
    if bad_balloon_leaders:
        errors.append(
            f"{len(bad_balloon_leaders)} balloon leader perimeter checks failed"
        )

    # Build real and virtual linework once for practical bubble/path clearance
    # checks. Virtual dimension lines matter because an editable DIMENSION does
    # not expose its rendered lines directly in model space.
    geometry_segments: list[dict[str, Any]] = []
    for line in msp.query("LINE"):
        layer = str(line.dxf.get("layer", "0"))
        if layer in {"PIPE", "COMPONENT", "DIM", "CALLOUT"}:
            geometry_segments.append(
                {
                    "handle": str(line.dxf.handle),
                    "start": _xy(line.dxf.start),
                    "end": _xy(line.dxf.end),
                    "layer": layer,
                }
            )
    for polyline in msp.query("LWPOLYLINE"):
        layer = str(polyline.dxf.get("layer", "0"))
        if layer not in {"PIPE", "COMPONENT", "DIM", "CALLOUT"}:
            continue
        points = [(float(x), float(y)) for x, y, *_rest in polyline.get_points()]
        if polyline.closed and points:
            points.append(points[0])
        for index, (start, end) in enumerate(zip(points, points[1:])):
            geometry_segments.append(
                {
                    "handle": f"{polyline.dxf.handle}:S{index}",
                    "start": start,
                    "end": end,
                    "layer": layer,
                }
            )
    geometry_segments.extend(virtual_dimension_lines)

    clearance_texts: list[tuple[Any, str]] = [
        (entity, str(entity.dxf.handle)) for entity in msp.query("TEXT MTEXT")
    ] + virtual_dimension_texts
    virtual_dimension_parent_handles = {
        parent_handle for _entity, parent_handle in virtual_dimension_texts
    }
    balloon_clearance_issues = []
    leader_path_issues = []

    for circle in balloon_circles:
        circle_handle = str(circle.dxf.handle)
        match = balloon_matches[circle_handle]
        center = match["center"]
        radius = match["radius"]
        own_leader = match["leader"]
        own_leader_handle = (
            str(own_leader[1].dxf.handle) if own_leader is not None else None
        )
        own_number_handle = (
            str(match["number"].dxf.handle) if match["number"] is not None else None
        )

        for segment in geometry_segments:
            if segment["handle"] == own_leader_handle:
                continue
            clearance = _point_segment_distance(
                center, segment["start"], segment["end"]
            ) - radius
            if clearance < BALLOON_CLEARANCE_MM:
                balloon_clearance_issues.append(
                    {
                        "circle": circle_handle,
                        "obstacle": segment["handle"],
                        "layer": segment["layer"],
                        "clearance": round(clearance, 3),
                    }
                )

        for other_circle in balloon_circles:
            other_handle = str(other_circle.dxf.handle)
            if other_handle == circle_handle:
                continue
            clearance = (
                _distance(center, _xy(other_circle.dxf.center))
                - radius
                - float(other_circle.dxf.radius)
            )
            if clearance < BALLOON_CLEARANCE_MM:
                balloon_clearance_issues.append(
                    {
                        "circle": circle_handle,
                        "obstacle": other_handle,
                        "layer": "CALLOUT",
                        "clearance": round(clearance, 3),
                    }
                )

        for text_entity, contextual_handle in clearance_texts:
            if contextual_handle == own_number_handle:
                continue
            layer = str(text_entity.dxf.get("layer", "0"))
            if contextual_handle in virtual_dimension_parent_handles:
                layer = "DIM"
            if layer not in {"DIM", "CALLOUT", "LABEL", "TEXT"}:
                continue
            clearance = _point_polygon_distance(
                center, _text_box(text_entity)
            ) - radius
            if clearance < BALLOON_CLEARANCE_MM:
                balloon_clearance_issues.append(
                    {
                        "circle": circle_handle,
                        "obstacle": contextual_handle,
                        "layer": layer,
                        "clearance": round(clearance, 3),
                        "kind": "text",
                    }
                )

        if own_leader is None:
            continue
        _delta, line, perimeter_point, target, _endpoint_name = own_leader
        leader_length = _distance(perimeter_point, target)
        if leader_length <= 1e-9:
            continue
        target_handles = {
            segment["handle"]
            for segment in geometry_segments
            if segment["handle"] != str(line.dxf.handle)
            and _point_segment_distance(
                target, segment["start"], segment["end"]
            ) <= 0.35
        }
        # Ignore the own leader, its intended target geometry, and the final
        # 1 mm contact zone. This is the key false-positive guard: the target
        # is supposed to intersect the leader, unrelated crossings are not.
        final_contact_fraction = min(0.25, 1.0 / leader_length)
        for segment in geometry_segments:
            if (
                segment["handle"] == str(line.dxf.handle)
                or segment["handle"] in target_handles
            ):
                continue
            intersection = _segment_intersection_parameters(
                perimeter_point, target, segment["start"], segment["end"]
            )
            if intersection is None:
                continue
            t, _u = intersection
            if 0.02 < t < 1.0 - final_contact_fraction:
                leader_path_issues.append(
                    {
                        "circle": circle_handle,
                        "leader": str(line.dxf.handle),
                        "crosses": segment["handle"],
                        "layer": segment["layer"],
                    }
                )

    # Collapse duplicate reports caused by a virtual dimension line sharing a
    # rendered endpoint; one obstacle per balloon is enough for diagnosis.
    unique_clearance = {
        (item["circle"], item["obstacle"], item.get("kind", "geometry")): item
        for item in balloon_clearance_issues
    }
    unique_path = {
        (item["circle"], item["leader"], item["crosses"]): item
        for item in leader_path_issues
    }
    balloon_clearance_issues = list(unique_clearance.values())
    leader_path_issues = list(unique_path.values())
    evidence["balloon_clearance_mm"] = BALLOON_CLEARANCE_MM
    evidence["balloon_clearance_issues"] = balloon_clearance_issues
    evidence["leader_path_issues"] = leader_path_issues
    if balloon_clearance_issues:
        errors.append(
            f"{len(balloon_clearance_issues)} balloon-to-geometry/text clearance checks failed"
        )
    if leader_path_issues:
        warnings.append(
            f"{len(leader_path_issues)} possible balloon-leader crossings need visual review"
        )

    bad_entity_weights = []
    for entity in msp:
        layer = entity.dxf.get("layer", "0")
        if layer not in ENTITY_WEIGHT_RANGES:
            continue
        if entity.dxftype() not in {"LINE", "CIRCLE", "ARC", "ELLIPSE", "LWPOLYLINE", "SOLID"}:
            continue
        lineweight = int(entity.dxf.get("lineweight", -1))
        if lineweight < 0:
            continue
        low, high = ENTITY_WEIGHT_RANGES[layer]
        if not low <= lineweight <= high:
            bad_entity_weights.append(
                {
                    "handle": entity.dxf.handle,
                    "layer": layer,
                    "lineweight": lineweight,
                    "allowed": [low, high],
                }
            )
    evidence["bad_entity_lineweights"] = bad_entity_weights
    if bad_entity_weights:
        errors.append(
            f"{len(bad_entity_weights)} entities violate semantic lineweight ranges"
        )

    center_lines = list(msp.query('LINE[layer=="CENTER"]'))
    evidence["center_line_count"] = len(center_lines)
    if len(center_lines) < 2:
        errors.append("client projection symbol needs at least two CENTER-axis lines")

    rotated_upright_text = []
    bad_role_text_styles = []
    for entity in msp.query("TEXT MTEXT"):
        layer = str(entity.dxf.get("layer", "0"))
        style_name = str(entity.dxf.get("style", ""))
        overrides = _mtext_font_overrides(entity)
        if layer in ROMANS_LAYERS:
            reasons = []
            if style_name != "CRE_ROMANS":
                reasons.append(f"style={style_name!r}")
            bad_overrides = [
                font
                for font in overrides
                if not _mtext_override_matches_role(font, "romans")
            ]
            if bad_overrides:
                reasons.append(f"font_overrides={bad_overrides!r}")
            if reasons:
                bad_role_text_styles.append(
                    {
                        "handle": entity.dxf.handle,
                        "type": entity.dxftype(),
                        "layer": layer,
                        "reasons": reasons,
                    }
                )
        elif layer in ARIAL_LAYERS:
            reasons = []
            if style_name not in {"CRE_ARIAL_NARROW", "CRE_ARIAL_NARROW_BOLD"}:
                reasons.append(f"style={style_name!r}")
            bad_overrides = [
                font
                for font in overrides
                if not _mtext_override_matches_role(font, "arial")
            ]
            if bad_overrides:
                reasons.append(f"font_overrides={bad_overrides!r}")
            if reasons:
                bad_role_text_styles.append(
                    {
                        "handle": entity.dxf.handle,
                        "type": entity.dxftype(),
                        "layer": layer,
                        "reasons": reasons,
                    }
                )

        rotation = _text_rotation(entity)
        value = _plain_text(entity).upper()
        requires_upright = layer in HORIZONTAL_LAYERS
        if layer in {"LABEL", "TEXT"} and rotation_distance(rotation) > 0.1:
            if "NS" not in value:
                requires_upright = True
            else:
                axis_deviation = min(
                    angular_distance(rotation, axis)
                    for axis in allowed_dimension_axes
                )
                if axis_deviation > axis_tolerance:
                    rotated_upright_text.append(
                        {
                            "handle": entity.dxf.handle,
                            "type": entity.dxftype(),
                            "layer": layer,
                            "rotation": rotation,
                            "reason": "inline NS label is off an allowed pipe axis",
                        }
                    )
                continue
        if requires_upright and rotation_distance(rotation) > 0.1:
            rotated_upright_text.append(
                {
                    "handle": entity.dxf.handle,
                    "type": entity.dxftype(),
                    "layer": layer,
                    "rotation": rotation,
                    "reason": "ordinary text must remain upright",
                }
            )
    evidence["rotated_upright_text"] = rotated_upright_text
    evidence["bad_role_text_styles"] = bad_role_text_styles
    if rotated_upright_text:
        errors.append(
            f"{len(rotated_upright_text)} normally upright text entities are rotated"
        )
    if bad_role_text_styles:
        errors.append(
            f"{len(bad_role_text_styles)} text entities have a wrong semantic style or MTEXT font override"
        )

    return {
        "file": str(path.resolve()),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "evidence": evidence,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dxf", type=Path)
    parser.add_argument(
        "--allow-axis",
        type=float,
        action="append",
        default=[],
        help="source-supported additional pipe axis in degrees; repeat as needed",
    )
    parser.add_argument("--axis-tolerance", type=float, default=0.2)
    parser.add_argument("--allow-pipe-curves", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate(
        args.dxf,
        extra_axes=args.allow_axis,
        axis_tolerance=args.axis_tolerance,
        allow_pipe_curves=args.allow_pipe_curves,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("PASS" if result["passed"] else "FAIL", result["file"])
        for message in result["errors"]:
            print(f"ERROR: {message}")
        for message in result["warnings"]:
            print(f"WARNING: {message}")
        print(json.dumps(result["evidence"], indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
