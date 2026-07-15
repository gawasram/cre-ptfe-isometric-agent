from __future__ import annotations

import py_compile
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


WORKSPACE = Path(__file__).resolve().parents[2]
WORK = WORKSPACE / "work"
sys.path.insert(0, str(WORK))

import cre_agent  # noqa: E402


class AgentPreflightTests(unittest.TestCase):
    def test_verified_iso106_input_is_structurally_complete(self) -> None:
        input_path = WORKSPACE / "drawing-agent" / "ISO_106_INPUT.md"
        self.assertEqual(cre_agent.incomplete_input_fields(input_path), [])

    def test_scaffold_is_guarded_current_api_and_non_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            work = root / "work"
            drawing_agent = root / "drawing-agent"
            templates = work / "templates"
            templates.mkdir(parents=True)
            drawing_agent.mkdir(parents=True)
            shutil.copyfile(
                WORKSPACE / "drawing-agent" / "NEXT_DRAWING_INPUT.md",
                drawing_agent / "NEXT_DRAWING_INPUT.md",
            )
            shutil.copyfile(
                WORK / "templates" / "create_iso_builder.py.template",
                templates / "create_iso_builder.py.template",
            )

            with (
                mock.patch.object(cre_agent, "ROOT", root),
                mock.patch.object(cre_agent, "HERE", work),
            ):
                self.assertEqual(cre_agent.scaffold_page(999), 0)
                input_path = drawing_agent / "ISO_999_INPUT.md"
                generator_path = work / "create_iso999_model.py"
                self.assertTrue(input_path.is_file())
                self.assertTrue(generator_path.is_file())
                self.assertIn("Source line number", cre_agent.incomplete_input_fields(input_path))
                self.assertEqual(
                    cre_agent.generator_uses_current_api(999, generator_path),
                    (True, "current CREModelBuilder API"),
                )
                py_compile.compile(str(generator_path), doraise=True)
                self.assertEqual(cre_agent.scaffold_page(999), 1)


if __name__ == "__main__":
    unittest.main()
