# ISO 70 QA Recheck - 2026-07-14

This is the source-to-fabrication verification record for the page-70 redraw.
It is a client-review check, not a fabrication approval.

## Source and outputs

- Split source: `/Users/ram/Downloads/ilovepdf_extracted-pages/ISOMETRICS FOR PTFE SPOOL PREPARATION-1044-1150-70.pdf`
- Split-page index: `0` (one-page A2 landscape PDF)
- Output basename: `ISO_70_PTFE`
- Line: `1"-SNA-424-1501-1-A82Y-A`
- Sheet: `2 OF 2`
- Continuation: `CONT. FROM DRG 1`
- External connection: `CONN. TO 424-N-104/S`

## Dimension-by-dimension reconciliation

| Source feature | Verified value(s) in output |
|---|---:|
| Connection to first elbow | 125 |
| First spool, cut / overall | 167 / 243 |
| 300 mm orifice route, spool cut / overall | 576 / 669 |
| Long upper spool, cut / overall | 2576 / 2652 |
| Upper return spool, cut / overall | 857 / 933 |
| Central upper spool, cut / overall | 625 / 719 |
| 1 in ball-valve branch spools, cut / overall | 100 / 194 (each) |
| 1 in globe valve face-to-face | 127 |
| 1 in ball valve face-to-face | 128 |
| 3/4 in ball valve face-to-face | 118 |
| Upper continuation leg | 94 and 38 to continuation |
| Lower 1 in branch legs | 93 and 76 |
| 600 mm orifice legs | 94 / 600 / 94 |
| Right-side branch legs | 76 and 94 |
| 3/4 in branches | 90 to flange / 118 valve |

## Component and balloon reconciliation

| Fabrication part | Description | Quantity | Balloon occurrences checked |
|---:|---|---:|---:|
| 8 | Eccentric reducer, 1-1/2 x 1 in | 1 | 1 |
| 9 | Equal tee, 1 x 1 in | 2 | 2 |
| 10 | Reducing tee, 1 x 3/4 in | 2 | 2 |
| 11 | 90 degree elbow, 1 in | 6 | 6 |
| 12 | WN flange, 1-1/2 in | 1 | 1 |
| 13 | WN flange, 1 in | 10 | 10 |
| 14 | WN flange, 3/4 in | 2 | 2 |
| 15 | Blind flange, 3/4 in | 2 | 2 |
| 16 | Globe valve, 1 in | 1 | 1 |
| 17 | Ball valve, 1 in | 2 | 2 |
| 18 | Ball valve, 3/4 in | 2 | 2 |
| 19 | Orifice element, 300 | 1 | 1 |
| 20 | Orifice element, 600 | 1 | 1 |

The seven source cut pieces are preserved as separate rows: 100, 100, 625,
857, 2576, 576 and 167 mm.  The two orifice lengths are intentionally split
into separate fabrication rows even though the source uses one instrument item.

## QA result

- [x] Central valve/flange assembly represented and dimensioned.
- [x] Right-side branch represented and dimensioned.
- [x] Continuation wording and external connection retained.
- [x] Pipe spool lengths and cut/overall pairs reconciled.
- [x] New fabrication part numbers map one-to-one to the checked occurrences.
- [x] Source weld numbers, document-page labels and source metadata removed.
- [x] DXF audit: `errors=0`, `fixes=0`.
- [x] Latest PDF rendered to PNG and visually inspected.
- [ ] AutoCAD DWG `AUDIT`: run in AutoCAD before client issue. The DWG in
  `outputs/` is the prior saved copy; the corrected PDF/DXF/PNG were regenerated
  in this check. Open the corrected DXF in AutoCAD and run `AUDIT`, then
  `SAVEAS` to refresh the DWG.

The drawing is ready for Lahu/client review. Do not describe it as approved until
the client confirms the central assembly, right branch, continuation coordinates,
and item mapping.
