---
name: cre-isometric-drawing
description: Generate, revise, audit, and validate Corrosion Resistant Equipment (CRE) PTFE spool isometric fabrication drawings from client PDF pages and CAD references. Use for CRE page extraction, source-to-BOM reconciliation, topology redrafting, DWG/DXF/PDF/PNG delivery, or checking an existing CRE drawing against the learned ISO_31_TO_35 drafting profile.
---

# CRE PTFE Isometric Drawing

Use this workflow for every CRE PTFE spool drawing. Treat each drawing as a
new source-controlled fabrication topology, never as a visual copy of a prior
page.

## Load the governing context

Before editing or generating anything, read:

1. `AGENTS.md`
2. `drawing-agent/CRE_PTFE_ISOMETRIC_STANDARD.md`
3. `drawing-agent/ISO_31_TO_35_DWG_REFERENCE_PROFILE.md`
4. `drawing-agent/NEXT_DRAWING_INPUT.md`
5. `drawing-agent/VALIDATION_CHECKLIST.md`

Read the page-specific `drawing-agent/ISO_<page>_INPUT.md` when it exists.
Use `drawing-agent/ISO_70_VERIFIED_EXAMPLE.md` and
`drawing-agent/ISO_106_INPUT.md` only as worked examples. Never copy their
dimensions, geometry, quantities, line number, revision, or approvals.

Apply this authority order when evidence conflicts:

1. Split source PDF: topology, dimensions, sizes, quantities, connections,
   line number and sheet relationship.
2. `ISO_31_TO_35.dwg`: CRE visual grammar and CAD construction style.
3. `ISO_06-Model.pdf`: clean fabrication presentation.

## Check the runtime

Resolve the target viewer page from the user's request or supplied split-PDF
filename. Never assume that “next” means the numerically next file or latest
output. If no page can be established from evidence, ask for it before
creating files.

Start with:

```sh
python3 work/cre_agent.py doctor
```

The CAD dependencies require CPython 3.12. `work/cre_agent.py` resolves the
workspace runtime for child commands. Set `CRE_PYTHON` only to an executable
that is actually Python 3.12.

Within Codex, commands that launch AutoCAD Core Console (`generate`,
`audit-dwg`, or the opt-in AutoCAD smoke test) require local-app execution
permission. `doctor`, `preflight` and DXF-only `validate` remain read-only and
sandbox-safe.

Useful commands:

```sh
python3 work/cre_agent.py scaffold --page <NUMBER>
python3 work/cre_agent.py preflight --page <NUMBER>
python3 work/cre_agent.py generate --page <NUMBER>
python3 work/cre_agent.py validate outputs/ISO_<NUMBER>_PTFE.dxf
```

Add `--allow-axis <ANGLE>` only when the page input records source evidence
for that nonstandard display axis.

`generate` does not interpret a new PDF automatically. It runs an existing
`work/create_iso<page>_model.py`. For a new page, inspect the source, complete
the input specification, reconcile the data, and create the page generator
before running the command. `scaffold` creates a non-overwriting input copy and
a guarded `CREModelBuilder` orchestration shell; it deliberately refuses to
draw until `build_sheet()` is replaced with source-reconciled data. Do not
batch unreviewed pages.

## Execute the drawing workflow

1. Archive superseded same-basename outputs and conversion `.bak`/`.scr`
   files under `outputs/archive/` or another workspace archive. Exclude that
   archive and internal specifications from the four-file client handoff.
2. Render and inspect the one-page split PDF. Use the combined PDF only for
   missing-page or neighbouring-page context. If the page says `x OF y` or
   `CONT. FROM/ON DRG n`, render the linked sheet and verify line, size and
   connection continuity.
3. Copy `NEXT_DRAWING_INPUT.md` to `ISO_<page>_INPUT.md` and complete every
   applicable field. Record every open endpoint, linked-sheet evidence,
   source-to-new part mapping, pipe-allowance reconciliation, source bearings,
   exclusions, exact assembly order, both revision fields and unresolved
   questions.
4. Reconcile the connection graph, cut pieces, components, BOM quantities,
   balloons and all verified dimensions before drawing.
5. Lay out a clean NTS connection graph first. Separate unrelated projected
   runs so they do not cross, touch or look connected. Preserve every real
   junction, continuation and component order.
6. Build page-neutral geometry with `work/cre_standard_lib.py` where possible.
   Replace all page-specific nodes, dimensions, labels, callouts and BOM rows.
7. Generate DXF, PDF and PNG; compile the final DWG with AutoCAD Core Console.
8. Render the final PDF itself to PNG. Inspect the whole sheet plus enlarged
   drawing, BOM and title-block regions.
9. Run the strict DXF validator. Fix every blocking error. Review every
   advisory leader crossing and leave only a confirmed intersection with the
   target's own multi-line component symbol.
10. Run AutoCAD `AUDIT` on the final DWG and require
    `Total errors found 0 fixed 0`.
11. Deliver only `ISO_<number>_PTFE.dwg`, `.dxf`, `.pdf` and `.png` with the
    same stable basename.

## Enforce the non-negotiable rules

- Never invent a component, dimension, callout mapping, continuation,
  revision, customer/project field, north arrow, checker or approver.
- Treat the topology as a connection graph. Source-page coordinates may move
  for clarity; connectivity and relative route logic may not.
- Enlarge crowded valve/flange/figure-8/blind assemblies and preserve their
  exact internal order after reconciling the BOM.
- Give each cut pipe piece a new fabrication row. Combine only repeated,
  identical components and balloon every occurrence.
- Treat source piece tags and weld numbers as source references, not new
  fabrication balloons. Preserve the mapping in the input/BOM and normally
  omit duplicate source tags from the drawing.
- Use cyan 30-degree, 150-degree or vertical pipe axes unless a documented
  exception exists. Do not add decorative pipe arcs or splines.
- Use live editable dimensions, source-verified manual labels, closed-filled
  arrows and the required Group Code 52 oblique pairing. A dimension offset
  may be flipped for clarity without changing endpoints, label or baseline.
- Use true green circular balloons. Keep the Romans number horizontal,
  centred and 1.7-1.9 mm high. Start the straight no-arrow leader exactly at
  the circle perimeter and end it on the intended item.
- Use Arial Narrow for ordinary labels, notes, tables and title fields. Use
  Romans only for DIM and CALLOUT text. Rotate only inline pipe-size/`NS`
  labels; keep source piece tags horizontal if intentionally retained.
- Leave `CHK` and `APPD` blank without client approval evidence.
- Keep title-block revision and footer/document revision separate.
- Never describe an output as fabrication-approved. Say it is ready for
  client review unless approval evidence is supplied.

## Interpret validation correctly

`work/validate_cre_ptfe_dxf.py` treats layer/style, A2 setup, DXF audit,
dimension construction, pipe-axis, text-role and balloon geometry failures as
blocking. Its possible leader-path crossings are advisory because a valid
leader may terminate inside a multi-line component symbol. Visual review is
mandatory; an unrelated geometry or dimension crossing is still a defect.

If validation fails, correct the generator and rebuild all four deliverables.
Do not patch only the PDF or silence a validator with an undocumented axis
exception.
