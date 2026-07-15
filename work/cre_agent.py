#!/usr/bin/env python3
"""Runtime-safe CLI for generating and validating CRE PTFE drawings."""

from __future__ import annotations

import argparse
from datetime import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BUNDLED_PYTHON = Path(
    "/Users/ram/.cache/codex-runtimes/codex-primary-runtime/"
    "dependencies/python/bin/python3"
)
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
COMBINED_SOURCE_PDF = Path(
    "/Users/ram/Downloads/ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150.pdf"
)
AUDIT_OK_RE = re.compile(r"Total\s+errors\s+found\s+0\s+fixed\s+0", re.I)
VERIFIED_LEGACY_GENERATORS = {70, 71, 106}
INPUT_FIELD_ALIASES = {
    "Split source PDF": ("Split source PDF",),
    "Viewer page number": ("Viewer page number",),
    "Source line number": ("Source line number",),
    "Source sheet number": ("Source sheet number",),
    "Output ISO number": ("Output ISO number",),
    "Output filename": ("Output filename",),
    "Source title-block revision": ("Source title-block revision",),
    "Customer": ("Customer (exact source/client wording)", "Customer"),
    "Project": ("Project (exact source/client wording)", "Project"),
    "Drafter": ("Drafter",),
    "Date": ("Date",),
    "Sheet number": ("Sheet number",),
    "Line number": ("Line number",),
}


def run_cmd(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=capture,
        text=True,
    )


def _runtime_candidates() -> list[Path]:
    values: list[Path] = []
    if os.environ.get("CRE_PYTHON"):
        values.append(Path(os.environ["CRE_PYTHON"]).expanduser())
    if sys.version_info[:2] == (3, 12):
        values.append(Path(sys.executable))
    values.append(BUNDLED_PYTHON)
    python312 = shutil.which("python3.12")
    if python312:
        values.append(Path(python312))

    unique: list[Path] = []
    seen: set[str] = set()
    for value in values:
        key = str(value.resolve()) if value.exists() else str(value)
        if key not in seen:
            unique.append(value)
            seen.add(key)
    return unique


def _probe_runtime(executable: Path) -> tuple[bool, str]:
    if not executable.is_file():
        return False, "not found"
    probe = (
        "import sys; "
        f"sys.path.insert(0, {str(HERE / 'vendor')!r}); "
        "assert sys.version_info[:2] == (3, 12), sys.version; "
        "import ezdxf, numpy, pdfplumber, reportlab; "
        "print(sys.version.split()[0])"
    )
    try:
        result = subprocess.run(
            [str(executable), "-c", probe],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    detail = (result.stdout or result.stderr).strip().splitlines()
    return result.returncode == 0, detail[-1] if detail else "probe failed"


def resolve_python_runtime() -> Path:
    failures = []
    for candidate in _runtime_candidates():
        valid, detail = _probe_runtime(candidate)
        if valid:
            return candidate.resolve()
        failures.append(f"- {candidate}: {detail}")
    raise RuntimeError(
        "No compatible CRE Python runtime was found. CPython 3.12 with the "
        "workspace CAD dependencies is required. Set CRE_PYTHON to that "
        "executable.\n" + "\n".join(failures)
    )


def find_autocad_console() -> Path | None:
    return next((path for path in AUTOCAD_CONSOLES if path.is_file()), None)


def source_candidates(page: int) -> list[Path]:
    filename = f"ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150-{page}.pdf"
    return [
        Path("/Users/ram/Downloads/ilovepdf_extracted-pages") / filename,
        ROOT / "ilovepdf_extracted-pages" / filename,
    ]


def incomplete_input_fields(path: Path) -> list[str]:
    if not path.is_file():
        return list(INPUT_FIELD_ALIASES)
    text = path.read_text(encoding="utf-8")
    missing = []
    for logical_name, aliases in INPUT_FIELD_ALIASES.items():
        values = []
        for alias in aliases:
            match = re.search(
                rf"(?m)^-[ \t]+{re.escape(alias)}:[ \t]*([^\r\n]*)[ \t]*$",
                text,
            )
            if match:
                values.append(match.group(1).strip().strip("`"))
        value = next((candidate for candidate in values if candidate), "")
        if (
            not value
            or "____" in value
            or "<NUMBER>" in value
            or value.lower() in {"yes / no", "blank"}
        ):
            missing.append(logical_name)
    return missing


def generator_uses_current_api(page: int, path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "generator missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "cre_standard_lib" in text and "CREModelBuilder" in text:
        return True, "current CREModelBuilder API"
    if page in VERIFIED_LEGACY_GENERATORS:
        return True, "verified legacy generator; strict output pipeline still required"
    return False, "generator does not use the current CREModelBuilder API"


def scaffold_page(page: int) -> int:
    input_path = ROOT / "drawing-agent" / f"ISO_{page}_INPUT.md"
    generator_path = HERE / f"create_iso{page}_model.py"
    existing = [str(path) for path in (input_path, generator_path) if path.exists()]
    if existing:
        print("Error: scaffold will not overwrite existing files:\n- " + "\n- ".join(existing))
        return 1

    source_path = source_candidates(page)[0]
    input_text = (ROOT / "drawing-agent" / "NEXT_DRAWING_INPUT.md").read_text(
        encoding="utf-8"
    )
    replacements = {
        "- Split source PDF:\n": f"- Split source PDF: `{source_path}`\n",
        "- Fallback combined PDF:\n": f"- Fallback combined PDF: `{COMBINED_SOURCE_PDF}`\n",
        "- Viewer page number:\n": f"- Viewer page number: `{page}`\n",
        "- Output ISO number:\n": f"- Output ISO number: `{page}`\n",
        "- Output filename: `ISO____PTFE`\n": f"- Output filename: `ISO_{page}_PTFE`\n",
    }
    for old, new in replacements.items():
        input_text = input_text.replace(old, new, 1)
    input_path.write_text(input_text, encoding="utf-8")

    generator_text = (HERE / "templates" / "create_iso_builder.py.template").read_text(
        encoding="utf-8"
    )
    generator_text = generator_text.replace("__PAGE_NUMBER__", str(page))
    generator_text = generator_text.replace("__SOURCE_PDF__", str(source_path))
    generator_path.write_text(generator_text, encoding="utf-8")
    generator_path.chmod(0o755)
    print(f"Created input scaffold: {input_path}")
    print(f"Created source-safe generator scaffold: {generator_path}")
    print("Next: inspect the PDF, complete every input field, reconcile the graph/BOM, then replace build_sheet().")
    return 0


def doctor() -> int:
    print(f"Workspace: {ROOT}")
    try:
        runtime = resolve_python_runtime()
    except RuntimeError as exc:
        print(f"Python runtime: FAIL\n{exc}")
        return 1
    valid, version = _probe_runtime(runtime)
    print(f"Python runtime: {'PASS' if valid else 'FAIL'} — {runtime} ({version})")

    console = find_autocad_console()
    print(f"AutoCAD Core Console: {'PASS — ' + str(console) if console else 'FAIL — not found'}")
    references = (
        Path("/Users/ram/Downloads/ISO_31_TO_35.dwg"),
        Path("/Users/ram/Downloads/ISO_06-Model.pdf"),
    )
    missing = [str(path) for path in references if not path.is_file()]
    if missing:
        print("Client references: FAIL\n- " + "\n- ".join(missing))
    else:
        print("Client references: PASS")
    return 0 if valid and console and not missing else 1


def preflight(page: int) -> int:
    source = next((path for path in source_candidates(page) if path.is_file()), None)
    print(f"split source PDF: {'PASS' if source else 'MISSING'} — {source or source_candidates(page)[0]}")
    if source is None:
        fallback = COMBINED_SOURCE_PDF if COMBINED_SOURCE_PDF.is_file() else None
        print(
            "combined PDF fallback: "
            f"{'AVAILABLE — extract/verify the requested page before drafting' if fallback else 'MISSING'}"
            f"{(' — ' + str(fallback)) if fallback else ''}"
        )
    else:
        fallback = COMBINED_SOURCE_PDF if COMBINED_SOURCE_PDF.is_file() else None
    input_path = ROOT / "drawing-agent" / f"ISO_{page}_INPUT.md"
    generator_path = HERE / f"create_iso{page}_model.py"
    checks = {
        "page input specification": input_path,
        "page generator": generator_path,
    }
    failed = source is None and fallback is None
    for label, path in checks.items():
        present = bool(path and path.is_file())
        print(f"{label}: {'PASS' if present else 'MISSING'} — {path or 'not found'}")
        failed = failed or not present
    if input_path.is_file():
        incomplete = incomplete_input_fields(input_path)
        if incomplete:
            print("input structural completeness: INCOMPLETE — " + ", ".join(incomplete))
            failed = True
        else:
            print("input structural completeness: PASS — manual source/BOM reconciliation still required")
    api_ok, api_detail = generator_uses_current_api(page, generator_path)
    print(f"generator API: {'PASS' if api_ok else 'FAIL'} — {api_detail}")
    failed = failed or not api_ok
    try:
        runtime = resolve_python_runtime()
        print(f"Python 3.12 runtime: PASS — {runtime}")
    except RuntimeError as exc:
        print(f"Python 3.12 runtime: MISSING — {exc}")
        failed = True
    console = find_autocad_console()
    print(f"AutoCAD Core Console: {'PASS — ' + str(console) if console else 'MISSING'}")
    failed = failed or console is None
    return 1 if failed else 0


def validate_dxf(dxf_path: str | Path, allow_axes: list[float]) -> int:
    runtime = resolve_python_runtime()
    script = HERE / "validate_cre_ptfe_dxf.py"
    cmd = [str(runtime), str(script), str(Path(dxf_path))]
    for axis in allow_axes:
        cmd.extend(["--allow-axis", str(axis)])
    print(f"--- Validating DXF: {dxf_path} ---")
    return run_cmd(cmd).returncode


def audit_dwg(dwg_path: str | Path) -> int:
    path = Path(dwg_path).resolve()
    if not path.is_file():
        print(f"Error: DWG not found: {path}")
        return 1
    console = find_autocad_console()
    if console is None:
        print("Error: AutoCAD Core Console 2027/2026 not found")
        return 1

    script_text = (
        "_.FILEDIA\n0\n_.CMDECHO\n1\n_.AUDIT\n_Y\n_.QUIT\n_N\n"
    )
    script_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".scr", prefix="cre_audit_", delete=False,
            encoding="utf-8",
        ) as handle:
            handle.write(script_text)
            script_path = Path(handle.name)
        result = run_cmd(
            [str(console), "/i", str(path), "/s", str(script_path), "/l", "en-US"],
            capture=True,
        )
    finally:
        if script_path is not None:
            script_path.unlink(missing_ok=True)

    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0 or not AUDIT_OK_RE.search(output):
        print("AutoCAD AUDIT failed or did not report 'Total errors found 0 fixed 0'.")
        print(output[-6000:])
        return 1
    backup = path.with_suffix(".bak")
    if backup.is_file():
        archive = ROOT / "outputs" / "archive" / "audit_backups"
        archive.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_backup = archive / f"{path.stem}_AUDIT_{stamp}.bak"
        backup.replace(archived_backup)
        print(f"Archived AutoCAD backup: {archived_backup}")
    print(f"AutoCAD AUDIT: PASS — {path.name} — Total errors found 0 fixed 0")
    return 0


def _required_outputs(page: int) -> list[Path]:
    basename = f"ISO_{page}_PTFE"
    return [ROOT / "outputs" / f"{basename}.{suffix}" for suffix in ("dwg", "dxf", "pdf", "png")]


def generate_page(page: int, allow_axes: list[float]) -> int:
    script = HERE / f"create_iso{page}_model.py"
    input_spec = ROOT / "drawing-agent" / f"ISO_{page}_INPUT.md"
    outputs = _required_outputs(page)
    existing = [str(path) for path in outputs if path.exists()]
    if existing:
        print(
            "Error: archive the existing same-basename deliverables before "
            "rebuilding; they will not be overwritten:\n- " + "\n- ".join(existing)
        )
        return 1
    if not input_spec.is_file():
        print(f"Error: complete the page input specification first: {input_spec}")
        return 1
    if not script.is_file():
        print(
            f"Error: page generator not found: {script}\n"
            "Inspect the split PDF and create the source-controlled generator; "
            "the agent does not infer new page data automatically."
        )
        return 1
    incomplete = incomplete_input_fields(input_spec)
    if incomplete:
        print(
            "Error: page input specification is structurally incomplete: "
            + ", ".join(incomplete)
        )
        return 1
    api_ok, api_detail = generator_uses_current_api(page, script)
    if not api_ok:
        print(f"Error: {api_detail}: {script}")
        return 1

    runtime = resolve_python_runtime()
    print(f"--- Generating CRE page {page} with {runtime} ---")
    result = run_cmd([str(runtime), str(script)])
    if result.returncode != 0:
        return result.returncode

    missing = [str(path) for path in outputs if not path.is_file()]
    if missing:
        print("Error: generator completed without all stable deliverables:\n- " + "\n- ".join(missing))
        return 1
    if validate_dxf(outputs[1], allow_axes) != 0:
        return 1
    if audit_dwg(outputs[0]) != 0:
        return 1
    print(f"Generation pipeline: PASS — ISO_{page}_PTFE is ready for visual client review")
    return 0


def convert_png(pages: list[int] | None) -> int:
    runtime = resolve_python_runtime()
    cmd = [str(runtime), str(HERE / "convert_all_pdfs_to_png.py")]
    if pages:
        cmd.extend(["--pages", *[str(page) for page in pages]])
    return run_cmd(cmd).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="CRE PTFE isometric drawing agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check the Python, CAD and client-reference prerequisites")

    preflight_parser = subparsers.add_parser("preflight", help="Check the prerequisites for one page")
    preflight_parser.add_argument("--page", type=int, required=True)

    scaffold_parser = subparsers.add_parser(
        "scaffold", help="Create a non-overwriting input and CREModelBuilder scaffold"
    )
    scaffold_parser.add_argument("--page", type=int, required=True)

    png_parser = subparsers.add_parser("convert-png", help="Render split PDF pages to PNG")
    png_parser.add_argument("--pages", type=int, nargs="*")

    gen_parser = subparsers.add_parser("generate", help="Generate, validate and audit one reviewed page")
    gen_parser.add_argument("--page", type=int, required=True)
    gen_parser.add_argument("--allow-axis", type=float, action="append", default=[])

    val_parser = subparsers.add_parser("validate", help="Validate a DXF against the CRE standard")
    val_parser.add_argument("dxf_path")
    val_parser.add_argument("--allow-axis", type=float, action="append", default=[])

    audit_parser = subparsers.add_parser("audit-dwg", help="Require a clean AutoCAD audit on a DWG")
    audit_parser.add_argument("dwg_path")

    batch_parser = subparsers.add_parser("batch", help="Generate only already-reviewed page generators")
    batch_parser.add_argument("pages", type=int, nargs="+")

    args = parser.parse_args()
    try:
        if args.command == "doctor":
            return doctor()
        if args.command == "preflight":
            return preflight(args.page)
        if args.command == "scaffold":
            return scaffold_page(args.page)
        if args.command == "convert-png":
            return convert_png(args.pages)
        if args.command == "generate":
            return generate_page(args.page, args.allow_axis)
        if args.command == "validate":
            return validate_dxf(args.dxf_path, args.allow_axis)
        if args.command == "audit-dwg":
            return audit_dwg(args.dwg_path)
        if args.command == "batch":
            for page in args.pages:
                # Pages with source-proven nonstandard axes must be generated
                # individually so an exception cannot leak into other pages.
                result = generate_page(page, [])
                if result != 0:
                    print(f"Batch stopped on page {page}")
                    return result
            print("Batch pipeline: PASS")
            return 0
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
