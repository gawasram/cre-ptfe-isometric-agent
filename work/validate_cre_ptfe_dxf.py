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


def angle_180(start: Any, end: Any) -> float:
    return math.degrees(math.atan2(end.y - start.y, end.x - start.x)) % 180.0


def angular_distance(a: float, b: float) -> float:
    delta = abs((a - b) % 180.0)
    return min(delta, 180.0 - delta)


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
    for dimension in dimensions:
        label = dimension.dxf.get("text", "")
        if not re.fullmatch(r"\s*\d+\s*", label or ""):
            bad_dimension_labels.append(
                {"handle": dimension.dxf.handle, "text": label}
            )
        oblique_angle = float(dimension.dxf.get("oblique_angle", 0.0)) % 180.0
        if not any(math.isclose(oblique_angle, valid, abs_tol=1.0) for valid in (30.0, 150.0)):
            bad_oblique_dimensions.append(
                {"handle": dimension.dxf.handle, "oblique_angle": oblique_angle}
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

    evidence["closed_filled_arrow_count"] = arrow_count
    evidence["bad_dimension_labels"] = bad_dimension_labels
    evidence["bad_dimension_styles"] = bad_dimension_styles
    evidence["bad_oblique_dimensions"] = bad_oblique_dimensions
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
            f"{len(bad_oblique_dimensions)} dimensions lack mandatory 30/150-degree isometric extension line oblique angles"
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
    evidence["pipe_line_count"] = len(pipe_lines)
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
    if bad_balloons:
        errors.append(f"{len(bad_balloons)} balloon circles are outside 4.0-4.7 mm")

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

    horizontal_layers = {"TABLE", "TITLE", "NOTES", "CALLOUT", "COMPANY", "HIGHLIGHT"}
    rotated_upright_text = []
    bad_role_text_styles = []
    for entity in msp.query("TEXT MTEXT"):
        if (
            entity.dxf.layer in {"DIM", "CALLOUT"}
            and entity.dxf.get("style", "") != "CRE_ROMANS"
        ):
            bad_role_text_styles.append(
                {
                    "handle": entity.dxf.handle,
                    "layer": entity.dxf.layer,
                    "style": entity.dxf.get("style", ""),
                }
            )
        if entity.dxf.layer not in horizontal_layers:
            continue
        rotation = float(entity.dxf.get("rotation", 0.0)) % 360.0
        if not (math.isclose(rotation, 0.0, abs_tol=0.1) or math.isclose(rotation, 360.0, abs_tol=0.1)):
            rotated_upright_text.append(
                {"handle": entity.dxf.handle, "layer": entity.dxf.layer, "rotation": rotation}
            )
    evidence["rotated_upright_text"] = rotated_upright_text
    evidence["bad_role_text_styles"] = bad_role_text_styles
    if rotated_upright_text:
        errors.append(
            f"{len(rotated_upright_text)} normally upright text entities are rotated"
        )
    if bad_role_text_styles:
        errors.append(
            f"{len(bad_role_text_styles)} DIM/CALLOUT text entities do not use CRE_ROMANS"
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
