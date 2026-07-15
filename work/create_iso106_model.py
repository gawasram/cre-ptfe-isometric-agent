#!/usr/bin/env python3
"""Build the clean CRE fabrication drawing for source viewer page 106.

Fabrication values come only from the split source PDF/page image and the
completed drawing-agent/ISO_106_INPUT.md specification.  ISO_31_TO_35.dwg
controls presentation, not geometry scale or fabrication values.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import create_iso70_model as base


BASENAME = "ISO_106_PTFE"
SOURCE_PDF = Path(
    "/Users/ram/Downloads/ilovepdf_extracted-pages/"
    "ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150-106.pdf"
)


def move(point: tuple[float, float], angle_deg: float, distance: float):
    return base.move_point(point, angle_deg, distance)


def midpoint(p1: tuple[float, float], p2: tuple[float, float]):
    return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)


def toward(origin, target, distance):
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return origin
    return (origin[0] + dx / length * distance, origin[1] + dy / length * distance)


def configure_output(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    base.SOURCE_PDF = SOURCE_PDF
    base.SOURCE_PAGE_INDEX = 0
    base.PDF_PATH = output_dir / f"{BASENAME}.pdf"
    base.DXF_PATH = output_dir / f"{BASENAME}.dxf"
    base.DWG_PATH = output_dir / f"{BASENAME}.dwg"
    base.PNG_PATH = output_dir / f"{BASENAME}.png"


def add_frame() -> None:
    base.add_rect(8, 8, 404, 578, "BORDER", 0.35)
    base.add_rect(11, 11, 398, 572, "BORDER", 0.18)
    base.add_rect(11, 568, 112, 13, "BORDER", 0.22)
    base.add_text(
        67, 571.8, "IF IN ANY DOUBT PLS ASK", 3.75,
        "TITLE", bold=True, align="center",
    )
    base.add_rect(309, 568, 100, 13, "BORDER", 0.22)
    base.add_text(
        359, 571.8, "DO NOT SCALE", 3.75,
        "TITLE", bold=True, align="center",
    )


def add_north_arrow() -> None:
    base.add_rect(374, 516, 25, 30, "BORDER", 0.22)
    base.add_text(386.5, 538.0, "N", 3.4, "TITLE", bold=True, align="center")
    tail = (380.0, 521.0)
    tip = (393.0, 534.0)
    base.add_line(*tail, *tip, "SYMBOL", 0.30)
    base.add_line(tip[0], tip[1], tip[0] - 5.2, tip[1] - 1.2, "SYMBOL", 0.30)
    base.add_line(tip[0], tip[1], tip[0] - 1.2, tip[1] - 5.2, "SYMBOL", 0.30)


def draw_elbow(previous, center, following) -> None:
    """Overlay a compact straight schematic elbow at a pipe corner."""
    entry = toward(center, previous, 4.0)
    exit_point = toward(center, following, 4.0)
    base.add_polyline([entry, center, exit_point], "COMPONENT", 0.50)


def draw_ball_valve_assembly(lower, upper, *, blind_upper=False) -> None:
    """Draw one flanged vertical ball-valve assembly."""
    center = midpoint(lower, upper)
    base.add_flange(*lower, 90)
    base.add_flange(*upper, 90)
    base.add_line(lower[0], lower[1], center[0], center[1] - 5.0,
                  "COMPONENT", 0.42)
    base.add_line(center[0], center[1] + 5.0, upper[0], upper[1],
                  "COMPONENT", 0.42)
    base.add_valve(*center, 90)

    # Source valve notes specify spindle west; show a compact west-facing stem.
    stem_end = (center[0] - 7.0, center[1])
    base.add_line(center[0], center[1], stem_end[0], stem_end[1],
                  "COMPONENT", 0.24)
    base.add_line(stem_end[0], stem_end[1] - 2.4,
                  stem_end[0], stem_end[1] + 2.4, "COMPONENT", 0.24)

    if blind_upper:
        cap_center = move(upper, 90, 2.8)
        cap_a = move(cap_center, 30, -4.3)
        cap_b = move(cap_center, 30, 4.3)
        base.add_line(*cap_a, *cap_b, "COMPONENT", 0.38)


def draw_figure_eight(center) -> None:
    """Compact source-supported ASME B16.48 figure-8 symbol."""
    a = move(center, 30, -1.55)
    b = move(center, 30, 1.55)
    base.add_circle(a[0], a[1], 1.45, "COMPONENT", 0.32)
    base.add_circle(b[0], b[1], 1.45, "COMPONENT", 0.32)
    base.add_line(*a, *b, "COMPONENT", 0.28)


def add_connection_text(x, y, lines, target, *, leader_from="right") -> None:
    for index, (value, bold) in enumerate(lines):
        base.add_text(x, y - index * 4.5, value, 2.15, "LABEL", bold=bold)
    leader_x = x + (36.0 if leader_from == "right" else 0.0)
    base.add_line(leader_x, y + 1.0, target[0], target[1], "LABEL", 0.22)


def add_bom() -> None:
    header = ["PART NO", "DESCRIPTION", "SIZE", "LENGTH MM", "QTY."]
    rows = [
        ["1", "PIPE SPOOL <9>", '2"', "6287", "01NO"],
        ["2", "PIPE SPOOL <10>", '2"', "273", "01NO"],
        ["3", "PIPE SPOOL <11>", '2"', "340", "01NO"],
        ["4", "PIPE SPOOL <12>", '2"', "1670", "01NO"],
        ["5", "PIPE SPOOL <13>", '2"', "220", "01NO"],
        ["6", "PIPE SPOOL <14>", '3/4"', "100", "01NO"],
        ["7", "PIPE SPOOL <15>", '2"', "1041", "01NO"],
        ["8", "PIPE SPOOL <16>", '2"', "160", "01NO"],
        ["9", "EQUAL TEE", '2"x2"', "--", "02NO"],
        ["10", "WELDOLET", '2"x3/4"', "--", "01NO"],
        ["11", "90 DEG ELBOW", '2"', "--", "04NO"],
        ["12", "FIGURE-8 FLANGE CL150", '2"', "--", "01NO"],
        ["13", "WN FLANGE CL150", '2"', "--", "03NO"],
        ["14", "WN FLANGE CL150", '3/4"', "--", "01NO"],
        ["15", "BLIND FLANGE CL150", '3/4"', "--", "01NO"],
        ["16", "BALL VALVE", '2"', "178", "01NO"],
        ["17", "BALL VALVE", '3/4"', "118", "01NO"],
    ]
    table_rows = list(reversed(rows)) + [header]
    base.add_table(
        15, 34, [22.1, 68.5, 40.1, 33.1, 26.2], 7.30,
        table_rows, 2.35,
    )


def build_iso106_sheet() -> None:
    add_frame()
    add_north_arrow()

    # Clean NTS display nodes. All ordinary pipe segments are exact 30, 150
    # or vertical axes. Fabrication labels remain source overrides.
    lower_tee = (220.0, 240.0)
    drg1 = move(lower_tee, 30, 190.0)
    lower_side = move(lower_tee, 210, 24.0)
    upper_tee = (220.0, 320.0)
    upper_side = move(upper_tee, 150, 35.0)
    lower_elbow = move(upper_tee, 330, 55.0)

    valve_lower = (lower_elbow[0], 390.0)
    valve_upper = (lower_elbow[0], 410.0)
    upper_elbow = (lower_elbow[0], 452.0)
    weldolet = move(upper_elbow, 330, 45.0)
    final_elbow_1 = move(upper_elbow, 330, 100.0)
    final_elbow_2 = move(final_elbow_1, 210, 32.0)
    equipment_flange = (final_elbow_2[0], final_elbow_2[1] - 20.0)

    branch_flange = (weldolet[0], 464.0)
    branch_blind = (weldolet[0], 486.0)

    # Eight source cut pieces.
    base.draw_pipe(lower_tee, drg1)
    base.draw_pipe(lower_tee, upper_tee)
    base.draw_pipe(upper_tee, lower_elbow)
    base.draw_pipe(lower_elbow, valve_lower)
    base.draw_pipe(valve_upper, upper_elbow)
    base.draw_pipe(upper_elbow, weldolet)
    base.draw_pipe(weldolet, final_elbow_1)
    base.draw_pipe(final_elbow_1, final_elbow_2)
    base.draw_pipe(weldolet, branch_flange, 0.42)

    # External continuation stubs are context, not new cut-piece rows.
    base.add_line(*lower_side, *lower_tee, "COMPONENT", 0.50)
    base.add_line(*upper_side, *upper_tee, "COMPONENT", 0.50)

    # Two equal tees and four elbows.
    base.add_circle(lower_tee[0], lower_tee[1], 1.0, "COMPONENT", 0.42)
    base.add_circle(upper_tee[0], upper_tee[1], 1.0, "COMPONENT", 0.42)
    draw_elbow(upper_tee, lower_elbow, valve_lower)
    draw_elbow(valve_upper, upper_elbow, weldolet)
    draw_elbow(weldolet, final_elbow_1, final_elbow_2)
    draw_elbow(final_elbow_1, final_elbow_2, equipment_flange)

    # Main valve: two 2-inch WN flanges, ball valve and upper figure-8.
    draw_ball_valve_assembly(valve_lower, valve_upper)
    figure_eight = move(valve_upper, 90, 3.4)
    draw_figure_eight(figure_eight)

    # 3/4-inch weldolet, WN flange, ball valve and blind flange branch.
    base.add_circle(weldolet[0], weldolet[1], 1.25, "COMPONENT", 0.38)
    draw_ball_valve_assembly(branch_flange, branch_blind, blind_upper=True)

    # Final elbow connects directly to the equipment WN flange assembly.
    base.add_line(*final_elbow_2, *equipment_flange, "COMPONENT", 0.45)
    base.add_flange(*equipment_flange, 90)

    # Cut and source overall/reference dimensions.
    base.add_dimension_pair(lower_tee, drg1, ("6287", "6351"), offsets=(-8.0, -14.0))
    base.add_dimension_pair(lower_tee, upper_tee, ("273", "400"), offsets=(-8.0, -14.0))
    base.add_dimension_pair(upper_tee, lower_elbow, ("340", "480"), offsets=(-8.0, -14.0))
    base.add_dimension_pair(lower_elbow, valve_lower, ("1670", "1810"), offsets=(-8.0, -14.0))
    base.add_dimension_pair(valve_upper, upper_elbow, ("220", "359"), offsets=(-8.0, -14.0))
    base.add_dimension_pair(weldolet, branch_flange, ("100", "210"), offsets=(8.0, 14.0))
    base.add_dimension_pair(upper_elbow, final_elbow_1, ("1041", "1162"), offsets=(8.0, 14.0))
    base.add_dimension_pair(final_elbow_1, final_elbow_2, ("160", "305"), offsets=(-8.0, -14.0))
    base.add_single_dimension(valve_lower, valve_upper, "178", 16.0)
    base.add_single_dimension(branch_flange, branch_blind, "118", 16.0)
    base.add_single_dimension(final_elbow_2, equipment_flange, "140", 8.0)
    base.add_single_dimension(lower_side, lower_tee, "63", 7.0)
    base.add_single_dimension(upper_side, upper_tee, "122", -7.0)

    # The new fabrication balloons 1-8 identify the eight cut pieces.  The
    # model drawing deliberately avoids duplicating the old <9>-<16> source
    # tags on the pipework; their mapping remains explicit in the BOM.

    # Exact source connection wording and coordinates.
    add_connection_text(
        356.0, 365.0,
        [("CONT. FROM DRG 1", True), ('2" NS', True), ("13 DEG", False)],
        drg1, leader_from="left",
    )
    add_connection_text(
        145.0, 229.0,
        [
            ("CONT. ON", True),
            ('2"-WNA-418-1401-1-A82Y-G', True),
            ("E 676931", False), ("N 602970", False), ("EL +101830", True),
        ],
        lower_side,
    )
    add_connection_text(
        130.0, 343.0,
        [
            ("CONT. ON", True),
            ('2"-WNA-418-1402-A82Y-G', True),
            ("E 676884", False), ("N 603047", False), ("EL +102230", True),
        ],
        upper_side,
    )
    add_connection_text(
        337.0, 374.0,
        [
            ("CONN. TO 418-T-102B/F", True),
            ("E 678505", False), ("N 602352", False), ("EL +104450", True),
            ("13.1 DEG", False),
        ],
        equipment_flange,
    )

    # Source-supported orientation/elevation notes; erection group tags and
    # weld numbers are intentionally omitted.
    base.add_text(222.0, 424.0, "SPINDLE W 12.99 N", 2.2, "LABEL", bold=True)
    base.add_line(257.0, 425.0, valve_lower[0] - 7.0, 400.0, "LABEL", 0.20)
    base.add_text(313.0, 501.0, "SPINDLE W 12.99 N", 2.2, "LABEL", bold=True)
    base.add_line(327.0, 499.0, branch_flange[0] - 7.0, 475.0, "LABEL", 0.20)
    base.add_text(218.0, 415.5, "TAIL N 12.99 E", 2.15, "LABEL", bold=True)
    base.add_line(248.0, 416.5, figure_eight[0], figure_eight[1], "LABEL", 0.20)
    base.add_text(220.0, 458.0, "EL +104593", 2.25, "LABEL", bold=True)
    base.add_text(weldolet[0] + 5.0, weldolet[1] - 4.0,
                  '2"x3/4" NS', 2.15, "LABEL", bold=True)

    # New fabrication balloons. Repeated components reuse one part number.
    callouts = [
        ("1", (303.0, 300.0), midpoint(lower_tee, drg1)),
        ("2", (205.0, 280.0), midpoint(lower_tee, upper_tee)),
        ("3", (252.0, 314.0), midpoint(upper_tee, lower_elbow)),
        ("4", (254.0, 341.0), midpoint(lower_elbow, valve_lower)),
        ("5", (258.0, 437.0), midpoint(valve_upper, upper_elbow)),
        ("6", (318.0, 448.0), midpoint(weldolet, branch_flange)),
        ("7", (336.0, 407.0), midpoint(weldolet, final_elbow_1)),
        ("8", (350.0, 395.0), midpoint(final_elbow_1, final_elbow_2)),
        ("9", (207.0, 244.0), lower_tee),
        ("9", (225.0, 332.0), upper_tee),
        ("10", (297.0, 426.0), weldolet),
        ("11", (257.0, 286.0), lower_elbow),
        ("11", (259.0, 460.0), upper_elbow),
        ("11", (367.0, 390.0), final_elbow_1),
        ("11", (318.0, 375.0), final_elbow_2),
        ("12", (271.0, 424.0), figure_eight),
        ("13", (258.0, 387.0), valve_lower),
        ("13", (261.0, 411.0), valve_upper),
        ("13", (319.0, 358.0), equipment_flange),
        ("14", (318.0, 458.0), branch_flange),
        ("15", (295.0, 495.0), branch_blind),
        (
            "16", (248.0, 400.0),
            (valve_lower[0] - 7.0, (valve_lower[1] + valve_upper[1]) / 2.0),
        ),
        ("17", (322.0, 475.0), midpoint(branch_flange, branch_blind)),
    ]
    for number, bubble, target in callouts:
        base.add_small_callout(number, bubble, target)

    add_bom()
    base.add_reference_notes()
    base.add_title_block(
        line_number='2"-WNA-418-1401-A82Y-G',
        sheet_number="2 OF 2",
        drafter="RAM GAWAS",
        drawing_date="15.7.26",
        revision="-1",
    )


def compile_dwg() -> None:
    """Use the installed AutoCAD core console for the final DWG."""
    executable = Path(
        "/Applications/Autodesk/AutoCAD 2027/AutoCAD 2027.app/Contents/"
        "Helpers/AcCoreConsole.app/Contents/MacOS/accoreconsole"
    )
    if not executable.is_file():
        raise FileNotFoundError(f"AutoCAD core console not found: {executable}")
    script_path = base.DXF_PATH.parent / "conv_iso106.scr"
    script_path.write_text(
        "_.FILEDIA\n0\n_.CMDECHO\n1\n_.AUDIT\n_Y\n_.SAVEAS\n2018\n"
        f"{base.DWG_PATH.resolve()}\n_Y\n_.QUIT\n_N\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            str(executable), "/i", str(base.DXF_PATH.resolve()),
            "/s", str(script_path.resolve()), "/l", "en-US",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not base.DWG_PATH.is_file():
        raise RuntimeError(
            "AutoCAD DWG conversion failed.\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    parser.add_argument("--no-dwg", action="store_true")
    args = parser.parse_args()

    configure_output(args.output_dir.resolve())
    base.entities.clear()
    base.validate_split_source()
    build_iso106_sheet()
    base.render_pdf()
    base.render_dxf()
    base.render_png()
    if not args.no_dwg:
        compile_dwg()

    print(base.PDF_PATH)
    print(base.DXF_PATH)
    print(base.DWG_PATH if not args.no_dwg else "DWG skipped")
    print(base.PNG_PATH)
    print(f"source={SOURCE_PDF}")
    print(f"entities={len(base.entities)}")


if __name__ == "__main__":
    main()
