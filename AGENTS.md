# CRE PTFE Isometric Drawing Agent

Apply these instructions to all future Corrosion Resistant Equipment (CRE) PTFE spool and piping isometric drawings in this workspace.

## Required references

Before creating or changing a drawing, read:

1. `drawing-agent/CRE_PTFE_ISOMETRIC_STANDARD.md`
2. `drawing-agent/ISO_31_TO_35_DWG_REFERENCE_PROFILE.md`
3. `drawing-agent/NEXT_DRAWING_INPUT.md`
4. `drawing-agent/VALIDATION_CHECKLIST.md`

Use `drawing-agent/ISO_70_VERIFIED_EXAMPLE.md` only as a worked example. Never copy its dimensions or component quantities into another drawing.

Use these client files as visual references when available:

- `/Users/ram/Downloads/ilovepdf_extracted-pages/ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150-<page>.pdf`
- `/Users/ram/Downloads/ISO_06-Model.pdf`
- `/Users/ram/Downloads/ISO_31_TO_35.dwg`
- `/Users/ram/Downloads/ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150.pdf`

Prefer the one-page split PDF for the requested viewer page. Use the combined PDF only as a fallback or for neighbouring-page context.

## Operating rules

- Treat the source isometric as the authority for topology, dimensions, item quantities, line number, connections and sheet number.
- Treat `ISO_31_TO_35.dwg` as the authority for CRE drafting style.
- Treat `ISO_06-Model.pdf` as the authority for clean fabrication presentation.
- Redraw the spool as a clean NTS fabrication topology. Do not paste the source isometric into the final drawing.
- Do not invent components, dimensions, continuation wording, approvals or callout mappings.
- Remove source weld numbers, elevation clutter, gasket codes, document-page labels and source metadata unless the client explicitly requests them.
- Use a new fabrication part schedule. Give each pipe piece its own row. Give repeated identical components one row with the total quantity, and place the same balloon at every occurrence.
- Split components into separate rows when their fabrication lengths differ, even if the source uses one item number. Example: 300 mm and 600 mm orifice elements.
- Keep `CHK` and `APPD` blank until the client confirms approval. Do not sign for Lahu or another reviewer.
- Preserve the source sheet relationship. Use `2 OF 2` only when the drawing belongs with sheet 1.
- Copy the *visual grammar* of `ISO_31_TO_35.dwg`, not its raw coordinates: ACI 4 cyan spool lines, ACI 2 yellow dimensions with closed-filled arrows and 30/150-degree isometric extension line oblique angles (Group Code 52), ACI 3 green circular balloons with straight no-arrow leaders positioned clear of dimension lines, and ACI 7 white tables/borders.
- Use only 30-degree, 150-degree and vertical isometric axes for ordinary pipe runs. Do not introduce decorative bends or curves; the client DWG contains no model-space `ARC` or `SPLINE` pipe geometry.
- Keep ordinary notes, tables, balloon numbers and title text horizontal (validate both `TEXT` and `MTEXT` entities). Rotate only inline pipe-size/`NS` labels to follow the pipe axis. Verify that both text types in `DIM` and `CALLOUT` layers use the `CRE_ROMANS` style.
- Use true circular balloons in new work. Position balloon bubbles clear of dimension lines, extension lines, inline pipe labels, and component symbols. The reference DWG balloons became ellipses only because the old sheets were non-uniformly transformed.
- Never derive fabrication lengths by measuring the client DWG. It is unitless, `SCALE=NTS`, and many dimension texts deliberately override the measured geometry.
- Do not copy dormant/exploded legacy blocks, green helper rectangles, stale anonymous dimension blocks or unused layer definitions from the reference.

## Required workflow

1. Render and inspect the split source PDF page and reference drawing.
2. Complete a drawing specification using `NEXT_DRAWING_INPUT.md`.
3. Reconcile topology and BOM quantities before drawing.
4. Create the simplified drawing using the exact reference profile plus the clean A2 rules in the standard.
5. Render the latest PDF to PNG and visually inspect it.
6. Zoom-check dimension arrows, extension-line gaps, balloon centring, leader endpoints, pipe-axis angles and lineweight hierarchy.
7. Verify all balloon counts, cut lengths, overall dimensions and special notes.
8. Run `work/validate_cre_ptfe_dxf.py` on the generated DXF. Add an
   `--allow-axis` value only when its exception is recorded from the source.
9. Audit the final DWG with AutoCAD `AUDIT`.
10. Deliver stable files named `ISO_<number>_PTFE.dwg`, `.dxf`, `.pdf` and `.png`.

## Reference-audit tool

`work/analyze_reference_dxf.py` produces a reproducible JSON audit of layers,
entity overrides, text/dimension styles, top-level and dimension-block arrow
geometry, curves, block extents, true leaders and LINE-based balloon-leader
candidates. Run it again whenever Lahu supplies a revised reference DWG; do
not silently carry an old style profile into a new client standard.

`work/validate_cre_ptfe_dxf.py` enforces the learned output profile: semantic
layers/weights, A2 paper setup with a full-sheet 1:1 viewport, CRE text roles,
editable dimensions and closed arrows,
dimension ratios, pipe axes, true-circle balloons, CENTER symbol axes, text
orientation and a clean DXF audit.

Never describe a drawing as fabrication-approved. State that it is ready for client review unless approval evidence is provided.
