# CRE PTFE Isometric Drawing Agent

Apply these instructions to all future Corrosion Resistant Equipment (CRE) PTFE spool and piping isometric drawings in this workspace.

## Required references

Before creating or changing a drawing, read:

1. `drawing-agent/CRE_PTFE_ISOMETRIC_STANDARD.md`
2. `drawing-agent/ISO_31_TO_35_DWG_REFERENCE_PROFILE.md`
3. `drawing-agent/NEXT_DRAWING_INPUT.md`
4. `drawing-agent/VALIDATION_CHECKLIST.md`

Use `drawing-agent/ISO_70_VERIFIED_EXAMPLE.md` only as a worked example.
`drawing-agent/ISO_106_INPUT.md` is a useful complex tee/branch/valve input
example. Never copy either example's dimensions, topology or component
quantities into another drawing.

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
- Reposition NTS geometry to make the connection graph unambiguous. Unrelated
  runs must not cross, touch or nearly merge; a projected source crossing may
  be separated when no connection exists. Preserve connectivity and relative
  route logic, not source-page coordinates.
- Do not invent components, dimensions, continuation wording, approvals or callout mappings.
- Remove source weld numbers, elevation clutter, gasket codes, joint-group
  `F/G/B` tags, boxed inspection `H` marks, document-page labels and source
  metadata unless the client explicitly requests a separate weld, joint or
  inspection schedule.
- Use a new fabrication part schedule. Give each pipe piece its own row. Give repeated identical components one row with the total quantity, and place the same balloon at every occurrence.
- Treat source piece numbers and circled weld numbers as source references, not
  new fabrication balloons. Record the source-to-new-part mapping in the input
  specification and BOM. Omit duplicate source piece tags from the drawing
  when the new balloons already identify the pieces; if retained, keep them
  horizontal.
- Split components into separate rows when their fabrication lengths differ, even if the source uses one item number. Example: 300 mm and 600 mm orifice elements.
- Keep `CHK` and `APPD` blank until the client confirms approval. Do not sign for Lahu or another reviewer.
- Preserve the source sheet relationship. Use `2 OF 2` only when the drawing belongs with sheet 1.
- Copy the *visual grammar* of `ISO_31_TO_35.dwg`, not its raw coordinates: ACI 4 cyan spool lines, ACI 2 yellow dimensions with closed-filled arrows and 30/150-degree isometric extension line oblique angles (Group Code 52), ACI 3 green circular balloons with straight no-arrow leaders positioned clear of dimension lines, and ACI 7 white tables/borders.
- Use only 30-degree, 150-degree and vertical isometric axes for ordinary pipe runs. Do not introduce decorative bends or curves; the client DWG contains no model-space `ARC` or `SPLINE` pipe geometry.
- Keep ordinary notes, tables, balloon numbers and title text horizontal (validate both `TEXT` and `MTEXT` entities). Rotate only inline pipe-size/`NS` labels to follow the pipe axis. Verify that both text types in `DIM` and `CALLOUT` layers use the `CRE_ROMANS` style.
- Use true circular balloons in new work. Position balloon bubbles clear of dimension lines, extension lines, inline pipe labels, and component symbols. The reference DWG balloons became ellipses only because the old sheets were non-uniformly transformed.
- Start each balloon leader exactly at the circle perimeter and end it on the
  intended piece or component symbol. The validator's bubble/number/perimeter
  failures are blocking. Its possible leader-crossing list is advisory: remove
  every unrelated dimension/geometry crossing, then visually confirm any
  remaining hit is only the target's own multi-line symbol.
- Dimension offsets and the side of an aligned dimension are presentation
  choices. Flip or increase an offset to clear symbols and balloons without
  changing the source-verified label, endpoints or required Group Code 52
  oblique angle.
- Never derive fabrication lengths by measuring the client DWG. It is unitless, `SCALE=NTS`, and many dimension texts deliberately override the measured geometry.
- Do not copy dormant/exploded legacy blocks, green helper rectangles, stale anonymous dimension blocks or unused layer definitions from the reference.

## Required workflow

1. Archive any older same-basename deliverables before rebuilding; do not use
   them as a data source.
2. Render and inspect the split source PDF page and reference drawing. When the
   source says `x OF y` or `CONT. FROM/ON DRG n`, also render the linked sheet
   or sheets, verify line/size/connection continuity and record the evidence.
3. Complete a drawing specification using `NEXT_DRAWING_INPUT.md`, including
   source-to-new numbering, exclusions and exact component assembly order.
4. Reconcile topology and BOM quantities before drawing.
5. Lay out the clean NTS connection graph first. Check that unrelated routes do
   not cross before adding dimensions and balloons.
6. Create the drawing using the exact reference profile plus the clean A2 rules
   in the standard.
7. Render the final PDF itself to PNG and inspect both the full sheet and zoomed
   drawing/BOM/title-block crops. Do not rely only on a separately generated
   preview PNG.
8. Zoom-check dimension arrows, extension-line gaps, balloon centring, leader endpoints, pipe-axis angles and lineweight hierarchy.
9. Verify all balloon counts, cut lengths, overall dimensions, assembly order,
   connection notes and special notes.
10. Run `work/validate_cre_ptfe_dxf.py` on the generated DXF. Add an
   `--allow-axis` value only when its exception is recorded from the source.
   Require zero blocking errors and manually review every advisory crossing.
11. Open the final DWG with AutoCAD Core Console and run `AUDIT`; require
    `Total errors found 0 fixed 0`.
12. Deliver stable files named `ISO_<number>_PTFE.dwg`, `.dxf`, `.pdf` and
    `.png`. Archive conversion `.bak`/`.scr` files outside the delivery folder.

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

Run the CAD scripts with the Python 3.12 workspace runtime returned by the
Codex workspace-dependency loader. The vendored `ezdxf`/NumPy binaries are not
compatible with macOS `/usr/bin/python3` 3.9.

Never describe a drawing as fabrication-approved. State that it is ready for client review unless approval evidence is provided.
