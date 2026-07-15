# ISO 106 CRE PTFE Drawing Input

## Identification

- Split source PDF: `/Users/ram/Downloads/ilovepdf_extracted-pages/ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150-106.pdf`
- Fallback combined PDF: `/Users/ram/Downloads/ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150.pdf`
- Viewer page number: `106`
- Split PDF zero-based index: `0`
- Combined PDF zero-based index: `105`
- Document page number: `1149 of 2770`
- Source line number: `2"-WNA-418-1401-A82Y-G`
- Unit: `418A`
- Source sheet number: `2 / 2`
- Output ISO number: `106`
- Output filename: `ISO_106_PTFE`
- Required sheet: `A2 portrait 420 x 594 mm`
- Client reference DWG hash checked against profile: `yes`
- Source title-block revision: `-1`
- Red source-footer document revision: `Rev. A` (different document field; do not substitute it for the title-block revision)
- Companion sheet inspected: viewer page `105`, document page `1148 of 2770`,
  sheet `1 / 2`. Its `CONT. ON DRG 2` is a `2"` continuation at
  `EL +101830` with `12.99`-degree route orientation; this matches page 106's
  `CONT. FROM DRG 1` size/elevation relationship and `13`-degree annotation.
- Delivery status: `ready for client review`

## External connections

| Endpoint ID | Exact source wording | Size | E / N / EL | Continuation dimension | Evidence state |
|---|---|---|---|---:|---|
| Drawing-1 continuation | `CONT. FROM DRG 1` | `2"` | not printed on page 106; linked page 105 prints `EL +101830` | `6351` overall main run | linked-sheet evidence |
| Lower tee side | `CONT. ON 2"-WNA-418-1401-1-A82Y-G` | `2"` | `E 676931`, `N 602970`, `EL +101830` | `63` source short offset | printed |
| Upper tee side | `CONT. ON 2"-WNA-418-1402-A82Y-G` | `2"` | `E 676884`, `N 603047`, `EL +102230` | `122` source short offset | printed |
| Equipment end | `CONN. TO 418-T-102B/F` | `2"` | `E 678505`, `N 602352`, `EL +104450` | `140` final offset | printed |

## Cut pipe pieces

| Source piece | Size | Cut length mm | Overall/reference mm | Start component | End component |
|---|---|---:|---:|---|---|
| `<9>` | `2"` | 6287 | 6351 | `CONT. FROM DRG 1` | lower equal tee |
| `<10>` | `2"` | 273 | 400 | lower equal tee | upper equal tee |
| `<11>` | `2"` | 340 | 480 | upper equal tee | 90-degree elbow |
| `<12>` | `2"` | 1670 | 1810 | 90-degree elbow | lower 2-inch valve flange |
| `<13>` | `2"` | 220 | 359 | upper 2-inch valve/figure-8 flange | 90-degree elbow |
| `<14>` | `3/4"` | 100 | 210 | 2 x 3/4 weldolet | 3/4-inch valve/flange assembly |
| `<15>` | `2"` | 1041 | 1162 | 90-degree elbow | 90-degree elbow |
| `<16>` | `2"` | 160 | 305 | 90-degree elbow | final 90-degree elbow |

Seven 2-inch cut pieces total `9991 mm`, reconciling with the source `10.0M`
pipe allowance. The one 3/4-inch piece is `100 mm`, reconciling with `0.1M`.

### Pipe-allowance reconciliation

| Size / material specification | Cut-piece total mm | Source allowance | Difference / rounding explanation |
|---|---:|---:|---|
| `2"`, B-36.19 seamless 40S | 9991 | 10.0 m | 9 mm below rounded source allowance; verified cuts unchanged |
| `3/4"`, B-36.19 seamless 80S | 100 | 0.1 m | exact |

## Component schedule

| Source item | Description | Size | FTF/length mm | Source quantity | Verified occurrences |
|---:|---|---|---:|---:|---:|
| 3 | Equal tee, B16.9 BW 40S | `2 x 2` | - | 2 | 2 |
| 4 | Weldolet, MSS-SP97 BW 40S/80S | `2 x 3/4` | - | 1 | 1 |
| 5 | 90-degree elbow, B16.9 BW 1.5D 40S | `2"` | - | 4 | 4 |
| 6 | Figure-8 flange, ASME B16.48 Class 150 | `2"` | - | 1 | 1 |
| 7 | WN flange, B16.5 Class 150 RF, 40S | `2"` | - | 3 | 3 |
| 8 | WN flange, B16.5 Class 150 RF, 80S | `3/4"` | - | 1 | 1 |
| 9 | Blind flange, B16.5 Class 150 RF | `3/4"` | - | 1 | 1 |
| 15 | Ball valve, sheet 543DR | `2"` | 178 | 1 | 1 |
| 16 | Ball valve, sheet 543DR | `3/4"` | 118 | 1 | 1 |

## Exact topology

`CONT. FROM DRG 1 -> <9> -> lower 2 x 2 equal tee`

- Lower tee straight side: `CONT. ON 2"-WNA-418-1401-1-A82Y-G`.
- Lower tee branch: `<10> -> upper 2 x 2 equal tee`.
- Upper tee straight side: `CONT. ON 2"-WNA-418-1402-A82Y-G`.
- Upper tee branch: `<11> -> elbow -> <12> -> lower WN flange -> 2-inch ball valve -> upper WN flange with figure-8 -> <13> -> elbow -> <15> -> elbow -> <16> -> elbow -> 2-inch WN flange -> CONN. TO 418-T-102B/F`.
- Branch from `<15>`: `2 x 3/4 weldolet -> <14> -> 3/4-inch WN flange -> 3/4-inch ball valve -> 3/4-inch blind flange`.

Source weld numbers `20-36`, erection gasket/bolt group labels, inspection `H`
marks and source erection materials are intentionally excluded from the clean
fabrication drawing.

## Isometric construction map

| Route segment | From | To | Axis | Source evidence |
|---|---|---|---:|---|
| `<9>` | lower tee | `CONT. FROM DRG 1` | 30 | long source isometric run |
| `<10>` | lower tee | upper tee | 90 | source vertical riser |
| `<11>` | upper tee | lower elbow | 150 | source diagonal run (undirected axis) |
| `<12>` | lower elbow | 2-inch valve | 90 | source vertical riser |
| `<13>` | 2-inch valve | upper elbow | 90 | source vertical riser |
| `<15>` | upper elbow | final dogleg | 150 | source diagonal run (undirected axis) |
| `<16>` | first final elbow | second final elbow | 30 | source transverse isometric run |
| `<14>` | weldolet | 3/4-inch blind branch | 90 | source vertical branch |

- Curved detail(s): `none`; all elbows and component symbols are straight schematic geometry.

### Connection-graph audit

- Every real junction represented exactly once: `yes`
- Every continuation remains open and labelled: `yes`
- Unrelated projected runs separated from false crossings: `yes`
- Crowded 2-inch valve/figure-8 and 3/4-inch blind-valve assemblies enlarged
  and checked against source quantities: `yes`

## Source orientation and bearing schedule

| Target segment/component | Exact source annotation | Source evidence | Display retained | Geometry-axis exception? |
|---|---|---|---|---|
| Drawing-1 continuation | `13 DEG` / linked sheet `12.99` | pages 105-106 continuation | no; continuity recorded in input | no |
| Upper tee route | `77 DEG` | page 106 upper/lower elbow annotations | no; clean NTS 150-degree axis | no |
| Equipment-end dogleg | `13.1 DEG` | page 106 equipment end | yes | no |
| 2-inch ball valve | `SPINDLE W 12.99 N` | page 106 upper valve | yes | no |
| 3/4-inch ball valve | `SPINDLE W 12.99 N` | page 106 blind branch | yes | no |
| Figure-8 flange | `TAIL N 12.99 E` | page 106 upper valve assembly | yes | no |
| Sheet orientation | north-arrow box | pages 105-106 | yes, supplied orientation | no |

## Dimension schedule

| From | To | Dimension type | Verified label mm | PDF evidence | Text override needed |
|---|---|---|---:|---|---|
| `<9>` ends | lower tee to drawing-1 continuation | cut | 6287 | cut-pipe table | yes |
| `<9>` ends | lower tee to drawing-1 continuation | overall | 6351 | main route | yes |
| `<10>` ends | lower tee to upper tee | cut | 273 | cut-pipe table | yes |
| `<10>` ends | lower tee to upper tee | overall | 400 | lower route | yes |
| `<11>` ends | upper tee to elbow | cut | 340 | cut-pipe table | yes |
| `<11>` ends | upper tee to elbow | overall | 480 | lower route | yes |
| `<12>` ends | elbow to lower valve flange | cut | 1670 | cut-pipe table | yes |
| `<12>` ends | elbow to lower valve flange | overall | 1810 | main vertical route | yes |
| `<13>` ends | upper valve flange to elbow | cut | 220 | cut-pipe table | yes |
| `<13>` ends | upper valve flange to elbow | overall | 359 | upper route | yes |
| `<14>` ends | weldolet to branch assembly | cut | 100 | cut-pipe table | yes |
| `<14>` ends | weldolet to branch assembly | overall | 210 | upper branch | yes |
| `<15>` ends | elbow to elbow | cut | 1041 | cut-pipe table | yes |
| `<15>` ends | elbow to elbow | overall | 1162 | main diagonal/reference | yes |
| `<16>` ends | elbow to elbow | cut | 160 | cut-pipe table | yes |
| `<16>` ends | elbow to elbow | overall | 305 | equipment-end offset | yes |
| 2-inch valve faces | flange face to flange face | FTF | 178 | upper assembly | yes |
| 3/4-inch valve faces | flange face to blind face | FTF | 118 | upper branch | yes |
| final elbow | equipment flange | short | 140 | equipment end | yes |

### Dimension-style check

- Text height: `2.1 mm`
- Closed-filled arrows: `yes`
- Arrow length equals text height: `yes`
- Extension offset and exceed each `0.5 x text height`: `yes`
- Text gap `0.4 x text height`: `yes`
- Integer mm with source text overrides: `yes`
- DXF Group Code 52 oblique angle `30` or `150`: `required for every aligned dimension`

## Special notes

- 2-inch valve orientation: `SPINDLE W 12.99 N`
- 3/4-inch valve orientation: `SPINDLE W 12.99 N`
- Figure-8 orientation: `TAIL N 12.99 E`
- Upper elbow elevation: `EL +104593`
- Source endpoint orientation notes: `13 degrees` at drawing-1 continuation and `13.1 degrees` at equipment-end dogleg.
- Use only source-applicable CRE lining/testing/packing notes.

## Fabrication schedule mapping

| New part no. | Source reference | Description | Size | Length mm | Quantity | Balloon locations |
|---:|---|---|---|---:|---:|---|
| 1 | `<9>` | Pipe spool | `2"` | 6287 | 1 | main long run |
| 2 | `<10>` | Pipe spool | `2"` | 273 | 1 | lower vertical |
| 3 | `<11>` | Pipe spool | `2"` | 340 | 1 | lower diagonal |
| 4 | `<12>` | Pipe spool | `2"` | 1670 | 1 | main vertical below valve |
| 5 | `<13>` | Pipe spool | `2"` | 220 | 1 | main vertical above valve |
| 6 | `<14>` | Pipe spool | `3/4"` | 100 | 1 | blind branch |
| 7 | `<15>` | Pipe spool | `2"` | 1041 | 1 | main diagonal above final dogleg |
| 8 | `<16>` | Pipe spool | `2"` | 160 | 1 | final transverse run |
| 9 | source item 3 | Equal tee | `2 x 2` | - | 2 | lower and upper tees |
| 10 | source item 4 | Weldolet | `2 x 3/4` | - | 1 | branch from part 7 |
| 11 | source item 5 | 90-degree elbow | `2"` | - | 4 | four route direction changes |
| 12 | source item 6 | Figure-8 flange | `2"` | - | 1 | upper side of 2-inch valve assembly |
| 13 | source item 7 | WN flange CL150 | `2"` | - | 3 | both 2-inch valve faces and equipment end |
| 14 | source item 8 | WN flange CL150 | `3/4"` | - | 1 | lower blind-branch valve face |
| 15 | source item 9 | Blind flange CL150 | `3/4"` | - | 1 | closed branch end |
| 16 | source item 15 | Ball valve | `2"` | 178 | 1 | main valve assembly |
| 17 | source item 16 | Ball valve | `3/4"` | 118 | 1 | blind branch |

## Title block

- Customer: `MUNITIONS INDIA LIMITED, HEF KHADKI-PUNE, INDIA`
- Project: `MIL PROJECT, TNT PLANT, HEF KHADKI PUNE, INDIA`
- Drafter: `RAM GAWAS`
- Date: `15.7.26`
- Checker: blank
- Approver: blank
- Source title-block revision: `-1`
- Footer/document revision: `Rev. A` (reference only)
- Chosen output `REV.`: `-1`, evidenced by page 106 title-block `REV` field
- Sheet number: `2 OF 2`
- Line number: `2"-WNA-418-1401-A82Y-G`
- Client projection symbol present in supplied orientation: `yes`
- Projection-method name confirmed: `blank`
- North arrow present and included in supplied orientation: `yes`
- Any current-revision text intentionally green: `line number only`

## Open client questions

- None required for the clean fabrication topology. The source red-footer
  `Rev. A` is a document reference and is not substituted for title-block
  revision `-1`.

## Delivery and validation record

- Stable basename: `ISO_106_PTFE`
- Compatible Python 3.12 runtime: `yes`
- Final PDF rendered to PNG and visually inspected: `yes`
- Strict CRE DXF validator: `pass`, zero blocking errors
- Leader advisories: `7`, visually classified as target-component symbol intersections
- DXF audit: `0 errors / 0 fixes`
- Final DWG AutoCAD audit: `Total errors found 0 fixed 0`
- Delivery status: `ready for client review`; not fabrication-approved
