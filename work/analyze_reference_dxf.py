#!/usr/bin/env python3
"""Inspect an AutoCAD DXF and print a reproducible drafting-style report.

The report deliberately separates table defaults (layers, text styles and
dimension styles) from the properties actually used by model-space entities.
That distinction matters for legacy drawings, where dimensions and leaders
are often exploded into LINE, SOLID and TEXT primitives.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "vendor"))

import ezdxf  # noqa: E402
from ezdxf import bbox  # noqa: E402


DEFAULT_DXF = HERE.parent / "tmp" / "ISO_31_TO_35_CONVERTED.dxf"


def json_value(value: Any) -> Any:
    """Convert DXF values, vectors and colors to JSON-safe values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "x") and hasattr(value, "y"):
        result = [round(float(value.x), 6), round(float(value.y), 6)]
        if hasattr(value, "z"):
            result.append(round(float(value.z), 6))
        return result
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, Iterable):
        try:
            return [json_value(item) for item in value]
        except TypeError:
            pass
    return str(value)


def top(counter: Counter, limit: int = 40) -> list[dict[str, Any]]:
    return [
        {"value": json_value(value), "count": count}
        for value, count in counter.most_common(limit)
    ]


def rounded(value: float, digits: int = 3) -> float:
    return round(float(value), digits)


def entity_attr(entity: Any, name: str, default: Any = None) -> Any:
    try:
        return entity.dxf.get(name, default)
    except Exception:
        return default


def line_angle_deg(start: Any, end: Any) -> float:
    dx = float(end.x) - float(start.x)
    dy = float(end.y) - float(start.y)
    angle = math.degrees(math.atan2(dy, dx)) % 180.0
    if math.isclose(angle, 180.0, abs_tol=1e-6):
        angle = 0.0
    return rounded(angle, 2)


def line_length(start: Any, end: Any) -> float:
    return math.hypot(float(end.x) - float(start.x), float(end.y) - float(start.y))


def layer_table(doc: Any) -> list[dict[str, Any]]:
    rows = []
    for layer in doc.layers:
        rows.append(
            {
                "name": layer.dxf.name,
                "color_aci": layer.color,
                "true_color": json_value(layer.dxf.get("true_color")),
                "linetype": layer.dxf.linetype,
                "lineweight_hundredths_mm": layer.dxf.lineweight,
                "plot": bool(layer.dxf.get("plot", 1)),
                "on": layer.is_on(),
                "frozen": layer.is_frozen(),
                "locked": layer.is_locked(),
                "transparency": json_value(getattr(layer, "transparency", 0.0)),
            }
        )
    return sorted(rows, key=lambda row: row["name"].casefold())


def linetype_table(doc: Any) -> list[dict[str, Any]]:
    rows = []
    for lt in doc.linetypes:
        tags = list(lt.pattern_tags.tags)
        pattern = [float(tag.value) for tag in tags if tag.code == 49]
        pattern_length = next(
            (float(tag.value) for tag in tags if tag.code == 40),
            0.0,
        )
        rows.append(
            {
                "name": lt.dxf.name,
                "description": lt.dxf.get("description", ""),
                "pattern_length": rounded(pattern_length, 6),
                "pattern": json_value(pattern),
            }
        )
    return sorted(rows, key=lambda row: row["name"].casefold())


def text_style_table(doc: Any) -> list[dict[str, Any]]:
    rows = []
    for style in doc.styles:
        rows.append(
            {
                "name": style.dxf.name,
                "font": style.dxf.get("font", ""),
                "bigfont": style.dxf.get("bigfont", ""),
                "fixed_height": rounded(style.dxf.get("height", 0.0), 6),
                "width_factor": rounded(style.dxf.get("width", 1.0), 6),
                "oblique_angle": rounded(style.dxf.get("oblique", 0.0), 6),
                "flags": style.dxf.get("flags", 0),
            }
        )
    return sorted(rows, key=lambda row: row["name"].casefold())


DIMSTYLE_FIELDS = (
    "dimpost",
    "dimapost",
    "dimscale",
    "dimasz",
    "dimexo",
    "dimdli",
    "dimexe",
    "dimrnd",
    "dimdle",
    "dimtp",
    "dimtm",
    "dimtxt",
    "dimcen",
    "dimtsz",
    "dimaltf",
    "dimlfac",
    "dimtvp",
    "dimtfac",
    "dimgap",
    "dimaltrnd",
    "dimtol",
    "dimlim",
    "dimtih",
    "dimtoh",
    "dimse1",
    "dimse2",
    "dimtad",
    "dimzin",
    "dimazin",
    "dimalt",
    "dimaltd",
    "dimtofl",
    "dimsah",
    "dimtix",
    "dimsoxd",
    "dimclrd",
    "dimclre",
    "dimclrt",
    "dimadec",
    "dimunit",
    "dimdec",
    "dimtdec",
    "dimaltu",
    "dimalttd",
    "dimaunit",
    "dimfrac",
    "dimlunit",
    "dimdsep",
    "dimtmove",
    "dimjust",
    "dimsd1",
    "dimsd2",
    "dimtolj",
    "dimtzin",
    "dimaltz",
    "dimalttz",
    "dimfit",
    "dimupt",
    "dimatfit",
    "dimfxlon",
    "dimtxtdirection",
    "dimlwd",
    "dimlwe",
    "dimfxl",
    "dimjogang",
    "dimblk",
    "dimblk1",
    "dimblk2",
    "dimldrblk",
    "dimtxsty",
    "dimltype",
    "dimltex1",
    "dimltex2",
)


def dimstyle_table(doc: Any) -> list[dict[str, Any]]:
    rows = []
    for style in doc.dimstyles:
        values = {"name": style.dxf.name}
        for field in DIMSTYLE_FIELDS:
            if style.dxf.hasattr(field):
                values[field] = json_value(style.dxf.get(field))
        rows.append(values)
    return sorted(rows, key=lambda row: row["name"].casefold())


def block_table(doc: Any) -> list[dict[str, Any]]:
    insert_counts = Counter()
    for layout in doc.layouts:
        for insert in layout.query("INSERT"):
            insert_counts[insert.dxf.name] += 1

    rows = []
    for block in doc.blocks:
        type_counts = Counter(entity.dxftype() for entity in block)
        try:
            block_extents = bbox.extents(block)
            extents = {
                "min": json_value(block_extents.extmin) if block_extents.has_data else None,
                "max": json_value(block_extents.extmax) if block_extents.has_data else None,
                "size": json_value(block_extents.size) if block_extents.has_data else None,
            }
        except Exception as exc:
            extents = {"error": str(exc)}
        rows.append(
            {
                "name": block.name,
                "base_point": json_value(block.block.dxf.get("base_point")),
                "flags": block.block.dxf.get("flags", 0),
                "entity_count": sum(type_counts.values()),
                "entity_types": dict(sorted(type_counts.items())),
                "insert_count": insert_counts[block.name],
                "extents": extents,
            }
        )
    return sorted(rows, key=lambda row: row["name"].casefold())


def layout_report(layout: Any) -> dict[str, Any]:
    type_counts = Counter(entity.dxftype() for entity in layout)
    try:
        extents = bbox.extents(layout)
        bounds = {
            "min": json_value(extents.extmin) if extents.has_data else None,
            "max": json_value(extents.extmax) if extents.has_data else None,
            "size": json_value(extents.size) if extents.has_data else None,
        }
    except Exception as exc:
        bounds = {"error": str(exc)}
    return {
        "name": layout.name,
        "entity_count": sum(type_counts.values()),
        "entity_types": dict(sorted(type_counts.items())),
        "extents": bounds,
    }


def modelspace_report(msp: Any) -> dict[str, Any]:
    entity_types: Counter = Counter()
    layers: Counter = Counter()
    entity_colors: Counter = Counter()
    entity_lineweights: Counter = Counter()
    entity_linetypes: Counter = Counter()
    layer_type_counts: dict[str, Counter] = defaultdict(Counter)
    entity_style_combinations: Counter = Counter()

    line_angles: Counter = Counter()
    line_lengths: Counter = Counter()
    line_angles_by_layer: dict[str, Counter] = defaultdict(Counter)
    line_lengths_by_layer: dict[str, Counter] = defaultdict(Counter)

    circle_radii: Counter = Counter()
    circle_radii_by_layer: dict[str, Counter] = defaultdict(Counter)
    arc_radii: Counter = Counter()
    arc_spans: Counter = Counter()
    arc_radii_by_layer: dict[str, Counter] = defaultdict(Counter)
    ellipse_axes: Counter = Counter()
    ellipse_ratios: Counter = Counter()
    ellipse_spans: Counter = Counter()

    text_heights: Counter = Counter()
    text_rotations: Counter = Counter()
    text_styles: Counter = Counter()
    text_by_layer: dict[str, Counter] = defaultdict(Counter)
    text_samples: list[dict[str, Any]] = []

    polyline_bulges: Counter = Counter()
    polyline_closed = Counter()
    polyline_vertex_counts: Counter = Counter()
    polyline_widths: Counter = Counter()
    solid_triangle_sizes: Counter = Counter()
    dimension_overrides: Counter = Counter()
    dimension_arrow_solids: Counter = Counter()
    dimension_arrow_inserts: Counter = Counter()
    dimensions: list[dict[str, Any]] = []
    leaders: list[dict[str, Any]] = []
    green_line_candidates: list[dict[str, Any]] = []
    green_balloon_ellipses: list[dict[str, Any]] = []

    for entity in msp:
        kind = entity.dxftype()
        layer = entity_attr(entity, "layer", "0")
        entity_types[kind] += 1
        layers[layer] += 1
        layer_type_counts[layer][kind] += 1
        color = entity_attr(entity, "color", 256)
        lineweight = entity_attr(entity, "lineweight", -1)
        linetype = entity_attr(entity, "linetype", "BYLAYER")
        entity_colors[color] += 1
        entity_lineweights[lineweight] += 1
        entity_linetypes[linetype] += 1
        entity_style_combinations[(kind, layer, color, lineweight, linetype)] += 1

        if kind == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            angle = line_angle_deg(start, end)
            length = rounded(line_length(start, end), 1)
            line_angles[angle] += 1
            line_lengths[length] += 1
            line_angles_by_layer[layer][angle] += 1
            line_lengths_by_layer[layer][length] += 1
            if color == 3:
                green_line_candidates.append(
                    {
                        "handle": entity_attr(entity, "handle", ""),
                        "start": start,
                        "end": end,
                        "length": length,
                        "angle": angle,
                        "layer": layer,
                        "lineweight": lineweight,
                    }
                )
        elif kind == "CIRCLE":
            radius = rounded(entity.dxf.radius, 3)
            circle_radii[radius] += 1
            circle_radii_by_layer[layer][radius] += 1
        elif kind == "ARC":
            radius = rounded(entity.dxf.radius, 3)
            span = (float(entity.dxf.end_angle) - float(entity.dxf.start_angle)) % 360.0
            arc_radii[radius] += 1
            arc_spans[rounded(span, 2)] += 1
            arc_radii_by_layer[layer][radius] += 1
        elif kind == "ELLIPSE":
            major_radius = math.hypot(entity.dxf.major_axis.x, entity.dxf.major_axis.y)
            ratio = float(entity.dxf.ratio)
            span = (float(entity.dxf.end_param) - float(entity.dxf.start_param)) % (2.0 * math.pi)
            if math.isclose(span, 0.0, abs_tol=1e-9):
                span = 2.0 * math.pi
            ellipse_axes[(rounded(major_radius, 3), rounded(major_radius * ratio, 3))] += 1
            ellipse_ratios[rounded(ratio, 6)] += 1
            ellipse_spans[rounded(math.degrees(span), 2)] += 1
            if color == 3 and math.isclose(span, 2.0 * math.pi, abs_tol=1e-6):
                green_balloon_ellipses.append(
                    {
                        "handle": entity_attr(entity, "handle", ""),
                        "center": entity.dxf.center,
                        "major_radius": major_radius,
                        "minor_radius": major_radius * ratio,
                    }
                )
        elif kind == "LWPOLYLINE":
            polyline_closed[bool(entity.closed)] += 1
            points = list(entity.get_points("xyseb"))
            polyline_vertex_counts[len(points)] += 1
            for point in points:
                polyline_widths[(rounded(point[2], 3), rounded(point[3], 3))] += 1
                bulge = rounded(point[4], 6)
                if not math.isclose(bulge, 0.0, abs_tol=1e-9):
                    polyline_bulges[bulge] += 1
        elif kind == "SOLID":
            vertices = [entity.dxf.vtx0, entity.dxf.vtx1, entity.dxf.vtx2]
            distances = sorted(
                line_length(vertices[index], vertices[(index + 1) % 3])
                for index in range(3)
            )
            solid_triangle_sizes[tuple(rounded(value, 3) for value in distances)] += 1
        elif kind in {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}:
            height = entity_attr(entity, "height", entity_attr(entity, "char_height", 0.0))
            rotation = entity_attr(entity, "rotation", 0.0)
            style = entity_attr(entity, "style", "STANDARD")
            text_heights[rounded(height, 3)] += 1
            text_rotations[rounded(rotation % 360.0, 2)] += 1
            text_styles[style] += 1
            text_by_layer[layer][rounded(height, 3)] += 1
            raw_text = entity.plain_text() if kind == "MTEXT" else entity_attr(entity, "text", "")
            text_samples.append(
                {
                    "handle": entity_attr(entity, "handle", ""),
                    "kind": kind,
                    "layer": layer,
                    "text": str(raw_text).replace("\n", " "),
                    "height": rounded(height, 3),
                    "rotation": rounded(rotation % 360.0, 2),
                    "style": style,
                    "insert": json_value(entity_attr(entity, "insert")),
                    "color": entity_attr(entity, "color", 256),
                }
            )
        elif kind == "DIMENSION":
            try:
                dimstyle = entity.get_dim_style()
                override = entity.get_acad_dstyle(dimstyle)
                dimension_overrides[tuple(sorted((key, str(value)) for key, value in override.items()))] += 1
            except Exception:
                override = {}
            try:
                measurement = rounded(entity.get_measurement(), 6)
            except Exception:
                measurement = None
            geometry = entity_attr(entity, "geometry", "")
            try:
                dimension_block = msp.doc.blocks.get(geometry)
            except Exception:
                dimension_block = None
            if dimension_block is not None:
                for solid in dimension_block.query("SOLID"):
                    vertices = [solid.dxf.vtx0, solid.dxf.vtx1, solid.dxf.vtx2]
                    edges = sorted(
                        line_length(vertices[index], vertices[(index + 1) % 3])
                        for index in range(3)
                    )
                    dimension_arrow_solids[
                        tuple(rounded(value, 3) for value in edges)
                    ] += 1
                for insert in dimension_block.query("INSERT"):
                    if "CLOSED" in insert.dxf.name.upper():
                        dimension_arrow_inserts[
                            (
                                insert.dxf.name,
                                rounded(insert.dxf.xscale, 3),
                                rounded(insert.dxf.yscale, 3),
                            )
                        ] += 1
            dimensions.append(
                {
                    "handle": entity_attr(entity, "handle", ""),
                    "layer": layer,
                    "dimstyle": entity_attr(entity, "dimstyle", ""),
                    "dimtype": entity_attr(entity, "dimtype", 0),
                    "measurement": measurement,
                    "text": entity_attr(entity, "text", ""),
                    "defpoint": json_value(entity_attr(entity, "defpoint")),
                    "text_midpoint": json_value(entity_attr(entity, "text_midpoint")),
                    "geometry_block": geometry,
                    "overrides": json_value(override),
                }
            )
        elif kind in {"LEADER", "MLEADER"}:
            vertices = []
            try:
                vertices = [json_value(vertex) for vertex in entity.vertices]
            except Exception:
                pass
            leaders.append(
                {
                    "kind": kind,
                    "layer": layer,
                    "style": entity_attr(entity, "dimstyle", entity_attr(entity, "style", "")),
                    "vertices": vertices,
                }
            )

    # The supplied DWG uses ordinary green LINE entities instead of
    # LEADER/MLEADER objects. Identify reproducible leader candidates by an
    # endpoint falling on or inside a green balloon ellipse.
    manual_balloon_leaders: list[dict[str, Any]] = []
    for line in green_line_candidates:
        matched = None
        endpoint_name = ""
        for name in ("start", "end"):
            point = line[name]
            for balloon in green_balloon_ellipses:
                center = balloon["center"]
                radius = max(balloon["major_radius"], balloon["minor_radius"])
                distance = math.hypot(point.x - center.x, point.y - center.y)
                if distance <= radius * 1.25:
                    matched = balloon
                    endpoint_name = name
                    break
            if matched is not None:
                break
        if matched is not None:
            manual_balloon_leaders.append(
                {
                    "line_handle": line["handle"],
                    "balloon_handle": matched["handle"],
                    "balloon_endpoint": endpoint_name,
                    "start": json_value(line["start"]),
                    "end": json_value(line["end"]),
                    "length": line["length"],
                    "angle": line["angle"],
                    "layer": line["layer"],
                    "lineweight": line["lineweight"],
                }
            )

    return {
        "entity_types": dict(sorted(entity_types.items())),
        "layers_used": top(layers, 200),
        "entity_colors": top(entity_colors),
        "entity_lineweights": top(entity_lineweights),
        "entity_linetypes": top(entity_linetypes),
        "entity_types_by_layer": {
            layer: dict(sorted(counts.items()))
            for layer, counts in sorted(layer_type_counts.items())
        },
        "entity_style_combinations": [
            {
                "entity_type": key[0],
                "layer": key[1],
                "color_aci": key[2],
                "lineweight_hundredths_mm": key[3],
                "linetype": key[4],
                "count": count,
            }
            for key, count in entity_style_combinations.most_common()
        ],
        "line_angles_degrees_top": top(line_angles, 80),
        "line_lengths_top": top(line_lengths, 100),
        "line_angles_by_layer": {
            layer: top(counts, 40) for layer, counts in sorted(line_angles_by_layer.items())
        },
        "line_lengths_by_layer": {
            layer: top(counts, 40) for layer, counts in sorted(line_lengths_by_layer.items())
        },
        "circle_radii_top": top(circle_radii, 80),
        "circle_radii_by_layer": {
            layer: top(counts, 40) for layer, counts in sorted(circle_radii_by_layer.items())
        },
        "arc_radii_top": top(arc_radii, 80),
        "arc_spans_degrees_top": top(arc_spans, 80),
        "arc_radii_by_layer": {
            layer: top(counts, 40) for layer, counts in sorted(arc_radii_by_layer.items())
        },
        "ellipse_axes_top": top(ellipse_axes, 80),
        "ellipse_ratios_top": top(ellipse_ratios, 80),
        "ellipse_spans_degrees_top": top(ellipse_spans, 80),
        "polyline_nonzero_bulges": top(polyline_bulges, 80),
        "polyline_closed": top(polyline_closed),
        "polyline_vertex_counts": top(polyline_vertex_counts, 80),
        "polyline_widths": top(polyline_widths, 80),
        "solid_triangle_edge_lengths_top": top(solid_triangle_sizes, 80),
        "dimension_block_arrow_solid_edges_top": top(dimension_arrow_solids, 80),
        "dimension_block_closed_arrow_inserts_top": top(dimension_arrow_inserts, 80),
        "text_heights_top": top(text_heights, 80),
        "text_rotations_top": top(text_rotations, 80),
        "text_styles_used": top(text_styles, 80),
        "text_heights_by_layer": {
            layer: top(counts, 40) for layer, counts in sorted(text_by_layer.items())
        },
        "text_samples": text_samples,
        "dimension_entities": dimensions,
        "dimension_override_groups": [
            {
                "overrides": {key: value for key, value in pattern},
                "count": count,
            }
            for pattern, count in dimension_overrides.most_common()
        ],
        "leader_entities": leaders,
        "manual_balloon_leader_candidates": manual_balloon_leaders,
    }


def document_report(path: Path) -> dict[str, Any]:
    doc = ezdxf.readfile(path)
    header_names = (
        "$ACADVER",
        "$DWGCODEPAGE",
        "$INSUNITS",
        "$MEASUREMENT",
        "$LUNITS",
        "$LUPREC",
        "$AUNITS",
        "$AUPREC",
        "$EXTMIN",
        "$EXTMAX",
        "$LIMMIN",
        "$LIMMAX",
        "$LTSCALE",
        "$CELTSCALE",
        "$DIMSCALE",
        "$TEXTSIZE",
        "$CLAYER",
        "$CELTYPE",
        "$CELWEIGHT",
    )
    header = {name: json_value(doc.header.get(name)) for name in header_names}
    return {
        "source": str(path.resolve()),
        "header": header,
        "layouts": [layout_report(layout) for layout in doc.layouts],
        "layers": layer_table(doc),
        "linetypes": linetype_table(doc),
        "text_styles": text_style_table(doc),
        "dimension_styles": dimstyle_table(doc),
        "blocks": block_table(doc),
        "modelspace": modelspace_report(doc.modelspace()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dxf", nargs="?", type=Path, default=DEFAULT_DXF)
    parser.add_argument("--compact", action="store_true", help="omit pretty indentation")
    args = parser.parse_args()
    report = document_report(args.dxf)
    print(json.dumps(report, indent=None if args.compact else 2, sort_keys=False))


if __name__ == "__main__":
    main()
