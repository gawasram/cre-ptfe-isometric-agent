# Next CRE PTFE Drawing Input

Copy this file for each new drawing and complete it before drafting.

## Identification

- Split source PDF:
- Fallback combined PDF:
- Viewer page number:
- Split PDF zero-based index: `0`
- Combined PDF zero-based index:
- Document page number:
- Source line number:
- Unit:
- Source sheet number:
- Output ISO number:
- Output filename: `ISO____PTFE`
- Required sheet: `A2 portrait 420 x 594 mm` / client exception:
- Client reference DWG hash checked against profile: yes / no
- Source title-block revision:
- Footer/document revision (record separately; do not substitute it for the title revision):
- Source identity evidence (line number, sheet and visible title/BOM matched):
- Companion/linked sheet(s) inspected and continuity evidence:
- Delivery status: `ready for client review`

## External connections

Record one row for every physical open endpoint, including tee side
continuations and equipment nozzles. Write `not printed` or `illegible` rather
than inferring a coordinate.

| Endpoint ID | Exact source wording | Size | E / N / EL | Continuation dimension | Evidence state |
|---|---|---|---|---:|---|
|  |  |  |  |  | printed / not printed / illegible |

## Cut pipe pieces

| Source piece | New part | Size | Cut length mm | Overall/reference mm | Start component | End component |
|---|---:|---|---:|---:|---|---|
|  |  |  |  |  |  |  |

### Pipe-allowance reconciliation

Sum verified cut lengths without changing them to match a rounded allowance.

| Size / material specification | Cut-piece total mm | Source allowance | Difference / rounding explanation |
|---|---:|---:|---|
|  |  |  |  |

## Component schedule

| Source item | Description | Size | FTF/length mm | Source quantity | Verified occurrences |
|---:|---|---|---:|---:|---:|
|  |  |  |  |  |  |

## Exact topology

Write every route in sequence. For a split network, write each branch separately.

`START -> component -> pipe piece -> component -> ... -> END`

For each crowded valve, flange, figure-8, blind or branch assembly, also write
the exact face-to-face order. Reconcile that order against the enlarged source
symbol and source BOM quantity before simplifying it.

### Source exclusions

List every visible source annotation intentionally omitted from the clean
fabrication drawing. Typical exclusions are weld numbers, inspection `H`
marks, gasket/stud erection material, elevations and document-page metadata.
Write `none` when nothing is excluded.

- Excluded source annotations:
- Source notes retained because they affect fabrication:

## Isometric construction map

Record every visible run direction before drawing. Use only `30`, `150` or
`90` degrees for ordinary pipe runs unless the source proves an exception.

| Route segment | From | To | Axis | Source evidence | Display separation / crossing risk |
|---|---|---|---:|---|---|
|  |  |  |  |  |  |

List any source-supported curved component detail here. Write `none` when no
curve is required:

- Curved detail(s):

### Connection-graph audit

- Every real junction represented exactly once: yes / no
- Every continuation remains open and labelled: yes / no
- Unrelated projected runs separated so they do not cross, touch or nearly merge: yes / no
- Crowded assembly order checked at enlarged source scale: yes / no

## Source orientation and bearing schedule

A source bearing label is not automatically a schematic-axis exception.
Record an `--allow-axis` exception only when the displayed fabrication
geometry itself is source-proven off the standard axes.

| Target segment/component | Exact source annotation | Source crop/evidence | Display retained | Geometry-axis exception? |
|---|---|---|---|---|
|  |  |  | yes / no | no / `--allow-axis ...` |

## Dimension schedule

Every displayed value must have source evidence. Do not enter a measured NTS
CAD distance as the fabrication value.

| From | To | Dimension type | Verified label mm | PDF evidence | Planned offset/side | Required GC52 oblique | Text override needed |
|---|---|---|---:|---|---|---:|---|
|  |  | cut / overall / FTF / short / continuation |  |  |  | 30 / 150 | yes / no |

### Dimension-style check

- Text height: `2.0-2.2 mm`
- Closed-filled arrows: yes / no
- Arrow length equals text height: yes / no
- Extension offset and exceed each `0.5 x text height`: yes / no
- Text gap `0.4 x text height`: yes / no
- Integer mm, no tolerances/alternate units unless source requests: yes / no
- Dimension side/offset chosen to clear symbols and balloons without changing endpoints or labels: yes / no

## Special notes

- Reducer orientation/offset:
- Instrument tag(s):
- Valve orientation:
- Lining/testing requirement:
- Packing requirement:
- Client-specific note:

## Fabrication schedule mapping

| New part no. | Source reference | Description | Size | Length mm | Quantity | Balloon locations |
|---:|---|---|---|---:|---:|---|
|  |  |  |  |  |  |  |

## Balloon and leader map

Use a true circular 4.0-4.7 mm balloon. Keep the number upright and use a
straight green leader without an arrow unless the client source explicitly
shows otherwise.

| Part no. | Occurrence | Exact target component/piece | Exact target point | Balloon location | Leader starts at perimeter | Leader clear of unrelated geometry |
|---:|---:|---|---|---|---|---|
|  |  |  |  |  | yes / no | yes / no |

Record every validator leader-crossing advisory after the first render. Classify
it as `target symbol only` or move the leader; never dismiss an unrelated
dimension, pipe, component or leader crossing.

## Text orientation map

| Label | Horizontal or pipe-aligned | Rotation | Reason |
|---|---|---:|---|
|  |  |  |  |

## Title block

- Customer (exact source/client wording):
- Project (exact source/client wording):
- Drafter:
- Date:
- Checker: leave blank unless confirmed
- Approver: leave blank unless confirmed
- Source title-block revision:
- Footer/document revision (reference only):
- Chosen output `REV.` and exact title-block evidence:
- Sheet number:
- Line number:
- Client projection symbol present in supplied orientation: yes / no
- Projection-method name confirmed by client/model: blank / first / third / other
- North arrow present in source/model: yes / no
- Include north arrow and exact orientation evidence: yes / no / evidence
- Any current-revision text intentionally green:

## Open client questions

- None / list every unresolved fabrication ambiguity here.

## Delivery and validation record

- Stable basename: `ISO_<number>_PTFE`
- Generated with compatible Python 3.12 runtime: yes / no
- Final PDF itself rendered to PNG and inspected: yes / no
- Full-sheet, drawing, BOM and title-block crops inspected: yes / no
- CRE DXF validator result: pass / fail
- Advisory leader crossings reviewed and classified: yes / no / none
- DXF audit: errors / fixes
- Final DWG AutoCAD `AUDIT`: errors / fixes
- Superseded outputs and conversion `.bak`/`.scr` files archived outside delivery folder: yes / no
