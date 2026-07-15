---
name: cre-isometric-drawing
description: Automation skill for generating, validating, and managing Corrosion Resistant Equipment (CRE) PTFE spool isometric drawings and CAD deliverables (.dwg, .dxf, .pdf, .png).
---

# CRE PTFE Isometric Drawing Automation Skill

Use this skill whenever generating, auditing, or modifying CRE PTFE spool fabrication and isometric drawings.

## Architecture & Tools

- **CLI Entrypoint**: `python3 work/cre_agent.py`
  - Generate page: `python3 work/cre_agent.py generate --page <NUMBER>`
  - Validate DXF: `python3 work/cre_agent.py validate outputs/ISO_<NUMBER>_PTFE.dxf [--allow-axis <ANGLE>]`
  - Batch generate: `python3 work/cre_agent.py batch 70 71 72`
- **Standard Shared Library**: `work/cre_standard_lib.py` (Title blocks, 3rd angle projection cone/circle symbols, BOM tables, circular balloons, lineweight layers).
- **AutoCAD Engine**: `AcCoreConsole` (converts DXF to DWG and validates standard CAD compliance).

## Quality Rules

1. Treat `ISO_31_TO_35.dwg` as visual grammar authority:
   - Cyan ACI 4 Pipe lines (`0.53mm` lineweight)
   - Yellow ACI 2 Dimensions with closed filled arrows and 30°/150° oblique angles (`0.20mm` lineweight)
   - Green ACI 3 Circular balloons (`0.35mm` lineweight, radius `2.15mm`)
   - White ACI 7 Borders & Tables (`0.35mm` / `0.25mm` lineweight)
2. Every drawing must pass `python3 work/cre_agent.py validate outputs/ISO_<NUMBER>_PTFE.dxf` with **0 errors**.
