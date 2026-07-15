"""
CRE Agent CLI Entrypoint
Unified tool to generate, validate, and batch process CRE PTFE isometric drawings.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def run_cmd(cmd: list[str]) -> int:
    res = subprocess.run(cmd, cwd=str(ROOT))
    return res.returncode


def generate_page(page: int) -> int:
    script = HERE / f"create_iso{page}_model.py"
    if not script.is_file():
        print(f"Error: Script not found for page {page}: {script}")
        return 1
    print(f"--- Generating Page {page} ---")
    return run_cmd([sys.executable, str(script)])


def validate_dxf(dxf_path: str, allow_axes: list[float]) -> int:
    script = HERE / "validate_cre_ptfe_dxf.py"
    cmd = [sys.executable, str(script), dxf_path]
    for axis in allow_axes:
        cmd.extend(["--allow-axis", str(axis)])
    print(f"--- Validating DXF: {dxf_path} ---")
    return run_cmd(cmd)


def main():
    parser = argparse.ArgumentParser(description="CRE Isometric Drawing Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate deliverables for a specific page")
    gen_parser.add_argument("--page", type=int, required=True, help="Page number (e.g. 70, 71, 72)")

    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate a DXF drawing against CRE standard")
    val_parser.add_argument("dxf_path", type=str, help="Path to DXF file")
    val_parser.add_argument("--allow-axis", type=float, action="append", default=[], help="Allowed non-standard pipe axes")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch process pages")
    batch_parser.add_argument("pages", type=int, nargs="+", help="Page numbers to generate")

    args = parser.parse_args()

    if args.command == "generate":
        sys.exit(generate_page(args.page))
    elif args.command == "validate":
        sys.exit(validate_dxf(args.dxf_path, args.allow_axis))
    elif args.command == "batch":
        for page in args.pages:
            ret = generate_page(page)
            if ret != 0:
                print(f"Batch execution failed on page {page}")
                sys.exit(ret)
        print("Batch processing complete!")


if __name__ == "__main__":
    main()
