from __future__ import annotations

import math
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work"
sys.path.insert(0, str(WORK))

from cre_standard_lib import (  # noqa: E402
    CREModelBuilder,
    balloon_leader_start,
    get_default_oblique_angle,
)
from validate_cre_ptfe_dxf import validate  # noqa: E402


class GeometryHelperTests(unittest.TestCase):
    def test_standard_dimension_oblique_mapping(self) -> None:
        self.assertEqual(get_default_oblique_angle((0, 0), (10, 10 / math.sqrt(3))), 150.0)
        self.assertEqual(get_default_oblique_angle((0, 0), (0, 10)), 30.0)
        self.assertEqual(get_default_oblique_angle((0, 0), (-10, 10 / math.sqrt(3))), 30.0)

    def test_off_axis_dimension_requires_explicit_source_exception(self) -> None:
        with self.assertRaises(ValueError):
            get_default_oblique_angle((0, 0), (10, 0))

    def test_balloon_leader_starts_on_perimeter(self) -> None:
        point = balloon_leader_start((10, 10), (20, 10), 2.15)
        self.assertAlmostEqual(point[0], 12.15, places=9)
        self.assertAlmostEqual(point[1], 10.0, places=9)
        with self.assertRaises(ValueError):
            balloon_leader_start((10, 10), (11, 10), 2.15)

    def test_pipe_helper_rejects_off_axis_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = CREModelBuilder("ISO_999_PTFE", Path(directory))
            with self.assertRaises(ValueError):
                builder.draw_pipe((0, 0), (10, 0))


class ValidatorSmokeTest(unittest.TestCase):
    def test_shared_library_generates_a_strictly_valid_minimal_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            builder = CREModelBuilder("ISO_999_PTFE", output)
            builder.add_title_block(
                line_number='2"-TEST-001-A82Y-G',
                sheet_number="1 OF 1",
                drafter="TEST DRAFTER",
                drawing_date="16.7.26",
                revision="0",
                customer="TEST CUSTOMER",
                project="VALIDATOR SMOKE TEST",
                include_north_arrow=True,
            )
            p1 = (100.0, 300.0)
            p2 = (220.0, 300.0 + 120.0 / math.sqrt(3.0))
            builder.draw_pipe(p1, p2)
            builder.add_dimension_pair(p1, p2, ("1000", "1100"), (-8.0, -14.0))
            target = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
            builder.add_small_callout("1", (160.0, 390.0), target)
            builder.export_dxf()

            result = validate(
                builder.dxf_path,
                extra_axes=[],
                axis_tolerance=0.2,
                allow_pipe_curves=False,
            )
            self.assertTrue(result["passed"], result["errors"])
            self.assertEqual(result["warnings"], [])
            self.assertEqual(result["evidence"]["dimension_count"], 2)
            self.assertEqual(result["evidence"]["balloon_circle_count"], 1)

            builder.export_pdf_and_png()
            self.assertTrue(builder.pdf_path.is_file())
            self.assertTrue(builder.png_path.is_file())

    @unittest.skipUnless(
        os.environ.get("CRE_TEST_AUTOCAD") == "1",
        "set CRE_TEST_AUTOCAD=1 to exercise AutoCAD Core Console",
    )
    def test_shared_library_compiles_and_audits_dwg(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = CREModelBuilder("ISO_998_PTFE", Path(directory))
            builder.add_title_block(
                line_number='2"-TEST-002-A82Y-G',
                sheet_number="1 OF 1",
                drafter="TEST DRAFTER",
                drawing_date="16.7.26",
                revision="0",
                customer="TEST CUSTOMER",
                project="AUTOCAD SMOKE TEST",
                include_north_arrow=True,
            )
            p1, p2 = (100.0, 300.0), (100.0, 380.0)
            builder.draw_pipe(p1, p2)
            builder.add_single_dimension(p1, p2, "800", -12.0)
            builder.add_small_callout("1", (140.0, 340.0), (100.0, 340.0))
            builder.export_dxf()
            builder.compile_dwg_via_accoreconsole()
            self.assertTrue(builder.dwg_path.is_file())
            self.assertFalse(builder.dwg_path.with_suffix(".bak").exists())


if __name__ == "__main__":
    unittest.main()
