# CRE PTFE Isometric Drafting Standard

## 1. Source hierarchy

Use this priority when information conflicts:

1. Source isometric page: topology, sizes, quantities, dimensions, connection notes, line number and sheet relationship.
2. `ISO_31_TO_35.dwg`: CRE layer colours, balloons, dimensions, BOM arrangement and title block.
3. `ISO_06-Model.pdf`: clean fabrication layout, notes and overall readability.

The exact evidence extracted from the client DWG is recorded in
`ISO_31_TO_35_DWG_REFERENCE_PROFILE.md`. Read it before drafting. It separates
active client conventions from unused legacy layers, blocks and non-uniformly
scaled sheet geometry.

Prefer the one-page split source PDFs in `/Users/ram/Downloads/ilovepdf_extracted-pages/` when available. Their page index is always 0; the original combined PDF page index is only used when a split page is missing. When a sheet number or continuation note links another drawing sheet, render that companion sheet too and verify the line size, line number and connection continuity before drafting.

Never infer a fabrication value from the NTS drawn length. Dimension labels are manually overridden with the verified source values.

## 2. Sheet and layout

- Sheet: true A2 portrait, 420 x 594 mm.
- Paper space: 420 x 594 mm, with a centred 420 x 594 mm full-sheet viewport
  and 594 mm view height (1:1). Do not shrink or crop the model frame.
- Outer frame: approximately 8 mm from the page edge.
- Inner frame: approximately 11 mm from the page edge.
- Top-left boxed warning: `IF IN ANY DOUBT PLS ASK`.
- Top-right boxed warning: `DO NOT SCALE`.
- Drawing zone: upper portion of the sheet.
- BOM: lower-left, above the revision strip.
- General notes and inspection: lower-centre/right.
- CRE title block: lower-right.
- Revision strip: lower-left, aligned with the title block bottom row.

The supplied `ISO_31_TO_35.dwg` contains five differently scaled, unitless NTS
frames; its ISO 35 frame is not an A2 aspect ratio. Copy its drafting style,
but reframe the result on true A2 unless the client explicitly requests the
original custom sheet. Never copy the large green helper rectangles.

## 3. AutoCAD layers and appearance

| Layer | ACI colour | Target lineweight | Linetype | Use |
|---|---:|---:|---|---|
| `PIPE` | 4 cyan | 0.53 mm | Continuous | Main spool centreline/topology; exact client heavy line |
| `COMPONENT` | 4 cyan | 0.35-0.50 mm | Continuous | Valves, flanges, reducers and instruments |
| `DIM` | 2 yellow | 0.20-0.25 mm | Continuous | Dimension/extension lines and text |
| `CALLOUT` | 3 green | 0.20-0.35 mm | Continuous | Circular balloons, numbers and straight leaders |
| `TABLE` | 7 white | 0.20-0.25 mm | Continuous | BOM grid and text |
| `BORDER` | 7 white | 0.20-0.35 mm | Continuous | Frames and title-block grid |
| `TITLE` / `NOTES` | 7 white | 0.13-0.20 mm | Continuous | Notes and headings |
| `COMPANY` | 4 cyan | 0.20 mm | Continuous | Company heading |
| `HIGHLIGHT` | 3 green | 0.20 mm | Continuous | Line number heading/value |
| `CENTER` | 2 yellow | 0.20 mm | CENTER | Client projection-symbol axes only |

Use black output for the client PDF unless colour plotting is requested. Keep AutoCAD model-space colours as listed above.

The client reference places active geometry almost entirely on layers `0` and
`TEXT` and then overrides individual entities. That is legacy structure, not a
template. New drawings must use the semantic layers above so future revisions
remain easy.

## 4. Text and symbols

- Preferred text: Arial Narrow for notes/tables/title fields; Romans for
  balloons and dimensions.
- Company heading: approximately 5.0-5.3 mm.
- Top warnings: approximately 4.0-4.6 mm.
- General-notes heading: approximately 5.0-5.7 mm.
- Notes: approximately 3.2-3.8 mm where space permits.
- BOM body: approximately 2.5-2.8 mm.
- Title-block main fields: approximately 2.7-4.2 mm, fitted to their cells.
- Line number: approximately 3.2-4.5 mm, green in AutoCAD.
- Continuation note: approximately 2.0-2.6 mm.
- Inline pipe-size text: approximately 1.4-1.8 mm.
- Dimension text: approximately 2.0-2.2 mm.
- Balloon number: approximately 1.7-1.9 mm.
- Balloon diameter: approximately 4.0-4.7 mm.

Keep ordinary MTEXT, tables, title fields and balloon numbers horizontal.
Rotate only inline pipe-size/`NS` labels so they follow the 30-degree,
150-degree or vertical pipe axis. Place balloon numbers upright and centred.
A straight green leader must touch the exact pipe piece/component, stop at the
balloon perimeter and normally have no arrowhead.

Source cut-piece tags such as `<9>` and source circled weld numbers are not the
new fabrication numbering system. Preserve their mapping in the drawing input
and BOM. Do not duplicate source tags on the pipework when the new part
balloons already identify each piece. If a source piece tag is deliberately
shown, keep it horizontal; only the adjacent size/`NS` text may rotate.

## 5. Simplified topology rules

- Draw one clean connected single-line network.
- A split-and-rejoin system must show both routes joining the correct tees.
- Keep every valve, flange, reducer, elbow, tee and instrument visibly connected.
- Use exact 30-degree, 150-degree and vertical isometric runs. Geometry is NTS
  and may be repositioned for clarity.
- Treat the drawing as a connection graph before treating it as a picture.
  Non-connected projected runs must not cross, touch or pass so close that they
  look joined. Separate a source-page projection crossing when necessary while
  preserving every real connection, branch and relative route relationship.
- Preserve the exact internal order of crowded assemblies. Reconcile each
  flange, valve, figure-8, blind and branch fitting against both the source BOM
  quantity and the enlarged source symbol before simplifying it.
- A printed compass bearing or orientation note describes the plant route or
  component orientation; it does not by itself permit an off-axis schematic
  pipe run. Keep the clean drawing on 30/150/90-degree axes unless the source
  proves that the displayed fabrication geometry itself requires an exception.
- Use compact, recognisable symbols:
  - flange: two close parallel lines perpendicular to the pipe;
  - valve: bow-tie/diamond body between flange faces;
  - globe valve: valve body plus stem/handwheel indication;
  - eccentric reducer: tapered transition and exact offset note;
  - orifice element: two flange faces, spool/plate indication and tag when supplied;
  - blind flange: flange pair with an outer cap line.
- Do not import source weld circles, elevations, gasket identifiers, joint-group
  `F/G/B` tags, boxed inspection `H` marks or the source title block unless the
  client requests a separate weld, joint or inspection schedule.
- The reference has no pipe `ARC` or `SPLINE` entities. Do not add decorative
  curves, fillets or image-traced wobble. Use crisp connected lines and compact
  schematic elbow symbols. Use a curve only for a source-supported component
  detail.
- A `PIPE` polyline is not an axis-check bypass: every segment must still lie
  on an allowed source-recorded axis, and the validator checks each segment.
- Use true `CIRCLE` entities for new balloons. Do not reproduce the reference
  balloon ellipse ratio; it is an old non-uniform scaling artefact.

## 6. Fabrication numbering and BOM

Use the reference five-column table:

`PART NO | DESCRIPTION | SIZE | LENGTH MM | QTY.`

Formatting rules:

- Put the header row at the bottom.
- Stack part rows upward; the highest part number appears at the top.
- Use `01NO`, `02NO`, `06NO`, etc.
- Give every cut pipe piece a separate fabrication part number.
- Use one row for repeated identical components and place that part balloon at every occurrence.
- Use separate rows when length or fabrication differs. Do not combine 300 mm and 600 mm instruments into one ambiguous row.
- Typical entries include pipe spool, eccentric reducer, equal tee, reducing tee, 90 DEG ELBOW, WN FLANGE CL150, BLIND FLANGE CL150, GLOBE VALVE, BALL VALVE and ORIFICE FLOW ELEMENT.
- Keep erection gaskets and studs out of the fabrication BOM unless the client requests a separate joint schedule.

When laying out the table, start from the client column-width proportions:

`11.63% | 36.04% | 21.13% | 17.41% | 13.80%`

for part number, description, size, length and quantity. Adjust only enough to
prevent real content from colliding with cell borders.

Before drawing, reconcile the number of balloon occurrences with the BOM quantity.

Also sum verified cut lengths by size and material/specification and compare
them with any source fabrication-material pipe allowance. Record the source
rounding or variance. Never alter a verified cut length merely to force the
sum to equal a rounded bulk allowance.

## 7. Dimensions and labels

Use a clean A2 dimension style that preserves the behaviour of the reference
`CHEM@123` style:

- ACI 2 yellow dimension and extension lines;
- Romans text, 2.0-2.2 mm high;
- integer millimetres with no automatic alternate units or tolerances;
- text above and parallel to the dimension line;
- AutoCAD default closed-filled arrow at both ends, never slash/tick ends;
- arrow length equal to text height and base width approximately one-third of
  arrow length;
- extension origin offset and extension beyond each approximately 0.5 x text
  height;
- text gap approximately 0.4 x text height;
- use aligned dimensions on isometric runs and linear dimensions only for a
  true horizontal/vertical projection need;
- assign mandatory 30-degree or 150-degree isometric extension line oblique angles (DXF Group Code 52) to all aligned dimensions so extension lines follow true isometric projection axes (30° / 150°) rather than flat perpendicular ticks;
- keep dimensions associative/editable in CAD whenever practical.

The old DWG uses per-sheet raw DIMSCALE values from 10 to 60 because its sheets
were transformed differently. Do not copy those raw values into a true-mm A2
drawing.

Show both values where the client model shows a cut/overall pair:

- cut pipe length;
- centre-to-centre or face-to-centre overall length.

Also show:

- valve face-to-face length;
- instrument face-to-face length;
- short centre-to-face legs around tees and elbows;
- external connection dimension and reducer offset;
- continuation dimension at a real sheet boundary.

Do not normalise similar dimensions. For example, preserve 93 mm and 94 mm as separate verified values when the source differs.

Never accept AutoCAD's measured NTS geometry as the fabrication label. Use a
manual text override only for a value verified from the source PDF, and record
that source value in the drawing specification.

Continuation wording must come from the source, such as `CONT. FROM DRG 1`. Do not invent another line number or continuation direction.

Record every physical open endpoint, including side continuations at tees and
equipment nozzles—not only a nominal start and end. Capture exact wording,
size, printed E/N/EL coordinates and continuation dimension; explicitly mark
an absent or illegible value rather than inventing one. Verify linked-sheet
continuity whenever a continuation names another drawing.

The dimension label and endpoints are source-controlled; the plotted side and
offset are not. Choose or flip the offset so extension lines, text and arrows
remain clear of components and balloons. Increasing or reversing an offset is
allowed for readability only when the source value, endpoints, baseline axis
and required Group Code 52 oblique angle remain unchanged.

## 8. Title block

Use the CRE title block with:

- `CORROSION RESISTANT EQUIPMENT PVT LTD`;
- customer and project rows;
- `NAME | SIGN | DATE`;
- `DRAN`, `CHK`, `APPD.`;
- green `LINE NO` field;
- `SCALE=NTS`;
- client-supplied projection symbol (cone/circle orientation as shown by the client);
- `SHEET NO. x OF y`;
- `REV.`;
- left revision strip `REV. | DESCRIPTION | BY | CHD. | APPD`.

Use the actual drafter name. Leave check and approval fields blank until confirmed by the client.

Supply customer and project wording explicitly from source/client evidence;
never inherit them from a prior page or a code default. Include a north arrow
only when the source page or governing client model shows one, and preserve its
orientation. Do not let a generic title-block helper invent plant orientation.

Populate `REV.` only from the matching source title-block revision field.
Record a footer/document revision separately and do not substitute it for the
drawing revision. Keep the chosen output revision and its exact evidence in
the page input specification.

The client projection symbol is required. Preserve the supplied cone/circle
orientation; do not label its projection method without client or model
evidence. Use yellow geometry with CENTRE/CENTER axes and keep it centred
inside its title-block cell.

## 9. Reusable implementation

Use `work/cre_standard_lib.py` for page-neutral pipe-axis guards, component
symbols, title block, bottom-up BOM, live dimensions, perimeter-start balloons,
role-aware PDF preview, DXF export and audited DWG conversion. Use
`work/create_iso70_model.py` only as a historical complex-layout code-pattern
reference for:

- A2 PDF/DXF generation;
- layer creation;
- flange, valve, reducer, blind-flange and orifice helpers;
- aligned dimensions with manual values;
- bottom-up BOM construction;
- title-block construction;
- PDF and DXF output.

Its reusable dimension helper must produce closed-filled arrows, not the short
crossing ticks used by an earlier trial version. Use
`work/analyze_reference_dxf.py` to re-audit any replacement client reference
before changing this standard.

Before delivery, run the runtime-safe agent wrapper:

```sh
python3 work/cre_agent.py validate outputs/ISO_<number>_PTFE.dxf
```

For a source-proven nonstandard display axis, record the evidence in the input
sheet and pass it explicitly, for example `--allow-axis 0`. Do not use an
exception merely to silence an accidental off-axis line.

Use the Python 3.12 workspace runtime returned by the Codex dependency loader.
The vendored CAD libraries are compiled for CPython 3.12 and do not run under
macOS `/usr/bin/python3` 3.9. `work/cre_agent.py` selects the compatible runtime
for its child commands and reports a clear error when none is available.

Do not recreate the removed legacy source-vector import path. A
generated PDF/PNG is a visual preview; the DXF/DWG and an AutoCAD plot using
the installed Arial Narrow/romans fonts are authoritative for final typography.
The PDF/PNG preview must still keep the role distinction: use Arial Narrow for
notes/tables/title fields and a distinct Romans-style surrogate for dimensions
and balloon numbers.
The CAD file must include an A2 paper-space page setup in addition to the A2
model-space frame.

For a new drawing, replace all page-specific nodes, dimensions, labels, callout lists and BOM rows. Do not copy ISO 70 geometry into another design.

The validator treats balloon-circle, number, perimeter and clearance failures
as blocking. Possible leader-path crossings are advisory because a leader that
ends on a multi-line flange or valve can intersect the target symbol itself.
Remove every unrelated dimension, pipe or component crossing and visually
document the remaining target-symbol-only cases before delivery.

Render the final PDF itself to a separate PNG for the last visual check. Keep
temporary conversion scripts and AutoCAD `.bak` files out of the delivery
folder; archive them with any superseded same-basename outputs.

Run `work/tests/test_cre_standard_lib.py` after changing the shared primitives.
The smoke test must still generate a strict-validator-clean DXF and a PDF-derived
PNG. Run it with `CRE_TEST_AUTOCAD=1` when changing DWG conversion; the final
saved DWG must pass a second AutoCAD audit with zero errors and zero fixes.

## 10. Required quality gate

Do not deliver until all of these are true:

- topology matches the source;
- component and flange counts reconcile with the BOM;
- every repeated component is ballooned at every occurrence;
- every cut piece and verified dimension is present;
- dimension arrows are closed-filled and extension-line/text spacing matches
  the profile;
- ordinary pipe runs use exact 30/150/90-degree axes;
- unrelated projected runs do not create false visual connections;
- balloons are true circles, upright and centred, with straight no-arrow
  leaders starting at the perimeter and terminating correctly;
- only inline pipe-size labels rotate with the isometric axis;
- special reducer/instrument/connection notes are retained;
- no invented source metadata remains;
- A2 PDF renders without clipping or unreadable text;
- DXF audit reports zero errors;
- automated CRE DXF validation passes with only documented source exceptions;
- every advisory leader crossing has been visually classified and any
  unrelated crossing removed;
- the final PDF render, not only the generator preview, passes visual review;
- AutoCAD `AUDIT` on the final DWG reports `0` errors and `0` fixes.
