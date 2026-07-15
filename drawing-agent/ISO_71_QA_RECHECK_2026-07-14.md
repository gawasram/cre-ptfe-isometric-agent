# ISO 71 QA Recheck - 2026-07-14

This is the source-to-fabrication verification record for the page-71 redraw.
It is ready for client review, not fabrication approval.

## Identification

- Split source: `/Users/ram/Downloads/ilovepdf_extracted-pages/ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150-71.pdf`
- Split page index: `0`
- Viewer page / document page: `71 / 1114`
- Line: `1"-SNA-424-1501-1-A82Y-D`
- Unit / sheet: `418A / 1 OF 1`
- Lower continuation: `CONT. ON 1"-SNA-424-1501-1-A82Y-A`, `E 676662`, `N 543456`, `EL +106217`
- Upper continuation: `CONT. ON 1"-SNA-418-1509-9-A82Y-E`, `E 677022`, `N 550211`, `EL +106217`

## Verified source geometry

`Lower continuation -> <5> -> 45 DEG elbow -> <4> -> 45 DEG elbow -> <3> -> 1 x 3/4 reducing tee -> <1> -> upper continuation`

`Reducing tee -> <2> -> 3/4 WN flange -> 3/4 ball valve -> 3/4 blind flange`

| Source piece | Size | Cut mm | Overall / source dimension mm |
|---|---|---:|---:|
| `<1>` | 1 in | 1492 | 1530 |
| `<2>` | 3/4 in | 100 | 190 |
| `<3>` | 1 in | 1677 | 1738 |
| `<4>` | 1 in | 465 | 509 |
| `<5>` | 1 in | 3104 | 3127 |

Short source dimensions retained: `360`, `360`, and 3/4-inch ball-valve face-to-face `118` mm.

## Fabrication schedule and balloons

| New part | Description | Size | Length | Quantity | Balloon occurrences |
|---:|---|---|---|---:|---:|
| 1 | Pipe spool | 1 in | 1492 | 1 | 1 |
| 2 | Pipe spool | 3/4 in | 100 | 1 | 1 |
| 3 | Pipe spool | 1 in | 1677 | 1 | 1 |
| 4 | Pipe spool | 1 in | 465 | 1 | 1 |
| 5 | Pipe spool | 1 in | 3104 | 1 | 1 |
| 6 | Reducing tee | 1 x 3/4 in | - | 1 | 1 |
| 7 | 45 DEG elbow | 1 in, 1.5D | - | 2 | 2 |
| 8 | WN flange CL150 | 3/4 in | - | 1 | 1 |
| 9 | Blind flange CL150 | 3/4 in | - | 1 | 1 |
| 10 | Ball valve | 3/4 in | 118 | 1 | 1 |

Source erection gaskets and studs are excluded from the fabrication BOM.

## QA result

- [x] Split one-page source PDF used.
- [x] Five cut lengths and their source dimensions reconciled.
- [x] Two elbows, tee, flanges, valve and blind are connected and ballooned.
- [x] Both continuation notes and coordinates retained.
- [x] Source weld IDs, gasket codes, document-page labels and source title block removed.
- [x] DXF audit: `0 errors`, `0 fixes`.
- [x] Latest PDF rendered to PNG and visually inspected at full page and detail.
- [ ] AutoCAD `AUDIT` and DWG save: run in AutoCAD before client issue.
