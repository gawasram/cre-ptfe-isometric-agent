# ISO 31–35 DWG Extracted Reference Profile

This is the forensic style profile for Lahu's supplied AutoCAD reference:

`/Users/ram/Downloads/ISO_31_TO_35.dwg`

It records what is actually present in the drawing, distinguishes active
entities from unused legacy definitions, and translates the useful visual
rules into a clean standard for future CRE PTFE spool drawings.

Do not use this document as a fabrication-data source. Use the requested
source-isometric PDF for every dimension, component, line number and quantity.

## 1. Provenance and reproducibility

- Reference DWG SHA-256: `df70cde318b9b9a6ba937e3a5e0f91ec5fcd00154051116de57e0746b322fd49`
- Converted audit DXF: `tmp/ISO_31_TO_35_CONVERTED.dxf`
- Converted DXF SHA-256: `630556db366047b26bd38f4bc664198361165b15e42a71e0fd57ff99cb9e3a20`
- Audit utility: `work/analyze_reference_dxf.py`
- Audit DXF version: `AC1032`
- Model-space extents: `(138268.257, -137822.950)` to `(267280.363, -98368.435)`
- Model-space size: `129012.105 x 39454.516` drawing units
- `$INSUNITS=0`: unitless
- `$MEASUREMENT=0`
- Header `$DIMSCALE=10`, `$TEXTSIZE=100`
- Paper-space layout is empty and configured as Letter; it is not authoritative.
- All five client title blocks say `SCALE=NTS`.

Run the audit again if the source hash changes:

```sh
/Users/ram/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  work/analyze_reference_dxf.py tmp/ISO_31_TO_35_CONVERTED.dxf
```

## 2. What the DWG contains

Exact model-space inventory:

| Entity | Count | Meaning in this file |
|---|---:|---|
| `LINE` | 674 | Pipe runs, components, leaders, grids, frames and symbols |
| `MTEXT` | 672 | Notes, BOM, title block, balloons and most labels |
| `DIMENSION` | 162 | Live linear/aligned dimensions |
| `ELLIPSE` | 99 | Green item balloons distorted from circles by old scaling |
| `SOLID` | 84 | Filled triangular arrowheads in manually constructed dimensions |
| `TEXT` | 82 | Primarily inline pipe-size labels |
| `LWPOLYLINE` | 25 | Ten borders, ten circular inspection bullets and five helper rectangles |
| `CIRCLE` | 14 | Projection-symbol circles and four local component details |

There are no model-space `INSERT`, `LEADER`, `MLEADER`, `ARC`, `SPLINE` or
`HATCH` entities. Valves, flanges, tables, title blocks and symbols are
exploded geometry.

## 3. Five sheet clusters and the frame warning

The DWG contains these five drawings:

| Cluster | Line number | Sheet | Raw outer-frame size, DU |
|---|---|---|---:|
| ISO 31 | `1"-SNA-418-1507-A82Y-G` | `4 OF 4` | `2237.19 x 1570.62` |
| ISO 32 | `1-1/2"-SNA-418-1508-A81Y-G` | `1 OF 1` | `2411.60 x 1693.06` |
| ISO 33 | `1" SNA-418-1509-9-A82Y-E` | `1 OF 2` | `17228.86 x 21294.29` |
| ISO 34 | `1" SNA-418-1507-9-A82Y-E` | `2 OF 2` | `43839.81 x 29492.80` |
| ISO 35 | `1" SNA-418-1509-9-A82Y-G` | `1 OF 1` | `26587.748 x 32861.554` |

The sizes are inconsistent. ISO 35 has width/height `0.8091`; A2 portrait is
`0.7071`. Fitting ISO 35 to 594 mm high would make it about 480.6 mm wide, not
420 mm. Therefore:

- copy its visual hierarchy and table/title structure;
- do not copy its raw frame coordinates or raw drawing scale;
- create a true 420 x 594 mm A2 portrait layout unless the client requests a
  different sheet;
- do not copy the five large green helper/reference rectangles.

## 4. Active and dormant layers

Only two layers hold model-space entities:

| Layer | Used entities | Base ACI | Base LW | Note |
|---|---:|---:|---:|---|
| `0` | 979 | 7 white | 0.05 mm | Most tables, notes and miscellaneous geometry |
| `TEXT` | 833 | 4 cyan | 0.05 mm | Pipe, dimensions, balloons and detail with entity overrides |

The visual style mostly comes from entity-level overrides, not layer defaults.
Future drawings must use clean semantic layers instead of repeating this
legacy organisation.

Defined but inactive model-space layers, all Continuous:

| Layer | ACI | LW | State / note |
|---|---:|---:|---|
| `DEFPOINTS` | 7 | 0.05 mm | non-plot |
| `DIST. PIECE` | 4 | 0.09 mm | unused |
| `TITLE BLOCK` | 252 | 0.05 mm | unused |
| `skid` | 252 | 0.09 mm | frozen, unused |
| `EJ-1006` | 155 | 0.09 mm | frozen, unused |
| `EJ-1002` | 185 | 0.09 mm | frozen, unused |
| `HE-3001` | 96 | 0.09 mm | frozen, unused |
| `HE-3002` | 214 | 0.09 mm | frozen, unused |
| `TAG` | 251 | 0.05 mm | unused |
| `DIMENSION` | 251 | 0.05 mm | unused |
| `N1` | 7 | default | unused |
| `M S PIPE` | 2 | default | unused |
| `FLANGE` | 4 | default | unused |
| `AC-1001` | 126 | 0.09 mm | frozen, unused |
| `EJ-1004` | 211 | 0.09 mm | frozen, unused |

Do not conclude that the unused layer colours are the active plotting standard.

## 5. Actual colour and lineweight grammar

This is the reusable client appearance extracted from active entities:

| Content | ACI | Reference lineweight | Clean target rule |
|---|---:|---:|---|
| Main pipe/component linework | 4 cyan | 0.50 and 0.53 mm | `PIPE` 0.53; `COMPONENT` 0.35–0.50 |
| Dimension and extension lines | 2 yellow | generally thin; entity/block-dependent | `DIM` 0.20–0.25 |
| Filled dimension arrowheads | 2 yellow | 0.50 mm SOLID | closed-filled arrow; solid fill |
| Item balloons and leaders | 3 green | 0.35 mm balloons; leaders vary | `CALLOUT` 0.20–0.35 |
| BOM grid and table content | 7 white | 0.25 mm typical | `TABLE` 0.20–0.25 |
| Frame, title and revision grids | 7 white | 0.20 mm typical | `BORDER` 0.20–0.35 |
| Notes and headings | 7 white | varies with hierarchy | `TITLE` / `NOTES` |
| Company name | 4 cyan | text | `COMPANY` cyan |
| Line number/current revisions | 3 green | text | `HIGHLIGHT` green only when intentional |

Entity override evidence includes 113 cyan `LINE` entities at 0.50 mm and 87
at 0.53 mm, 99 green balloon ellipses at 0.35 mm, and 84 yellow filled arrow
SOLIDs at 0.50 mm.

## 6. Linetypes

- 1,792 of 1,812 model entities use `BYLAYER`; active layer defaults are
  Continuous.
- Ten `CENTER` lines are ACI 2 yellow, 0.20 mm, and belong to the client
  cone/circle projection symbols. The audited geometry alone does not prove
  which projection-method name the client intends.
- Ten `HIDDEN` lines are used only in small component/continuation details.
- No ordinary spool run is dashed.

New rule: use Continuous for pipe, components, dimensions, leaders, borders
and tables. Use CENTER only for the projection symbol or a real centreline, and
HIDDEN only when a genuine hidden detail must be communicated.

## 7. Isometric line geometry and curves

The main cyan spool paths use three construction axes:

- 30 degrees;
- 150 degrees;
- vertical, 90 degrees.

All twenty cyan pipe segments longer than 500 DU fall on these axes: eight at
30 degrees, four at 150 degrees and eight vertical. Representative ISO 35 runs
are 16,581 DU at 150 degrees, 15,176 DU at 30 degrees and 5,000 DU vertical.

There are no model-space arcs or splines. Elbows, tees, flanges and valves are
schematic straight-line symbols. The only curve-like entities are balloons,
projection circles, inspection bullets and four local component circles.

Future rule:

- construct ordinary pipe runs with exact 30/150/90-degree axes;
- use a crisp connected corner or a recognised schematic elbow symbol;
- do not add decorative fillets, freehand curves or image-traced wobbles;
- use an `ARC` only when a source-supported component symbol genuinely needs it,
  never to change the pipe topology.

## 8. Exact dimension behaviour

All 162 live dimensions use `CHEM@123`; 160 are aligned and two are linear.
The useful base variables are:

| Variable | Value | Meaning |
|---|---:|---|
| `DIMASZ` | 1.0 | arrow size multiplier |
| `DIMTXT` | 1.0 | dimension text multiplier |
| `DIMSCALE` | 26.0 base | overridden per sheet |
| `DIMEXO` | 0.5 | extension-line origin offset |
| `DIMEXE` | 0.5 | extension line past dimension line |
| `DIMGAP` | 0.4 | text gap |
| `DIMTAD` | 1 | text above dimension line |
| `DIMTOFL` | 1 | dimension line retained outside extension points |
| `DIMSOXD` | 1 | suppress outside dimension line when required |
| `DIMTIX` | 0 | do not force text between extension lines |
| `DIMTIH` / `DIMTOH` | 0 / 0 | text follows dimension-line angle |
| `DIMDEC` | 0 | integer millimetres |
| `DIMLUNIT` | 2 | decimal units |
| `DIMZIN` | 12 | suppress unnecessary zeros |
| `DIMAZIN` | 2 | angular zero suppression |
| `DIMBLK`, `DIMBLK1`, `DIMBLK2` | empty | AutoCAD default closed-filled arrow |
| `DIMSAH` | 0 | same arrow at both ends |
| `DIMTSZ` | 0 | arrows, not oblique tick marks |

Every used dimension overrides:

- dimension and extension colours to ACI 2 yellow;
- text colour to ACI 0/BYBLOCK so the retained dimension block plots correctly;
- text style to `romans`;
- jog angle to 90 degrees;
- the effective `DIMSCALE`.

Effective scales in the legacy drawing:

| Cluster | Dimension scale usage |
|---|---|
| ISO 31 | 23 x 10 |
| ISO 32 | 12 x 15 and 3 x 10 |
| ISO 33 | 27 x 60 and 9 x 35 |
| ISO 34 | 36 x 45 |
| ISO 35 | 51 x 50 and 1 x 30 |

At effective scale 50:

- arrow axial length = 50 DU;
- arrow base width = 16.667 DU;
- equal arrow side length is approximately 50.690 DU;
- text height = 50 DU;
- extension origin offset = 25 DU;
- extension beyond the dimension line = 25 DU;
- text gap = 20 DU.

The reusable *ratios* are therefore:

- arrow length = text height;
- arrow base width = one-third arrow length;
- extension origin offset = 0.5 x text height;
- extension beyond = 0.5 x text height;
- text gap = 0.4 x text height.

For a clean A2 drawing, use a readable 2.0–2.2 mm dimension height and apply
these ratios; do not copy raw DIMSCALE 10–60. Use closed-filled triangular
arrows at both ends—never the short crossing tick marks used by older trial
generators.

Forty-eight live dimensions have explicit text overrides and 114 are blank/
automatic. Several displayed values do not equal their NTS measured geometry.
Examples include measured 3897.114 displayed as 6000, measured 13142.802
displayed as 19784, and measured 1297.306 displayed as 1606. The source PDF
annotation—not measured DWG distance—is always the fabrication authority.

## 9. Text styles, heights and orientation

Defined styles:

| Style | Font | Active use |
|---|---|---|
| `MtXpl_Arial_Narrow` | `ARIALNB.TTF` | primary notes, BOM, title and labels |
| `Standard` | `romans.shx` | balloons and secondary text |
| `romans` | `romans.shx` | live dimensions and a few headings |
| `CHEM` | `isocp.shx` | dimension-style base only; overridden in use |
| `TEXT` / `nayan1` | `isocp.shx` | defined, not active in model text |
| `CC` | `arial.ttf` | defined, unused |
| `ST3` | `MTCORSVA.TTF` | defined, unused |

Usage totals:

- 525 MTEXT objects use Arial Narrow;
- 142 MTEXT objects use Standard/romans.shx;
- five MTEXT objects use `romans`;
- all 82 single-line TEXT objects use Arial Narrow.

All MTEXT is horizontal and middle-centred. Ordinary notes, tables, title
fields and balloon numbers stay horizontal. Only 38 inline single-line pipe
labels rotate to follow the isometric axes; the typical rotations are about
29–33 degrees, 327–333 degrees, 90 degrees and 267 degrees.

Clean ISO 35 raw hierarchy, followed by its approximate height if the sheet is
height-fitted to 594 mm:

| Content | Raw DU | Approx. mm |
|---|---:|---:|
| Inline pipe size | 79.527 | 1.44 |
| Balloon number | 100.549 | 1.82 |
| BOM body/header | 148.327 | 2.68 |
| BOM part number | 162.233 | 2.93 |
| Notes | 205.928 | 3.72 |
| Title-block text | 231.187 | 4.18 |
| Line headers | 251.685 | 4.55 |
| Top warning | 231.187 / 256.875 | 4.18 / 4.64 |
| Company name | 291.302 | 5.27 |
| `GENERAL NOTES` | 318.293 | 5.75 |
| `INSPECTION` | 281.340 | 5.09 |

Use the hierarchy, then fit long client text safely inside its field. Do not
blindly copy raw sizes when that causes overlap.

## 10. Balloons and leaders

All 99 client item balloons are full green `ELLIPSE` entities on layer `TEXT`,
ACI 3, 0.35 mm. Their constant major/minor ratio is `0.9427685`, proving that
old circles were non-uniformly transformed with the sheets.

ISO 35's common balloon is:

- 218.826 x 206.303 DU overall;
- about 3.96 x 3.73 mm when height-fitted to A2;
- number height 100.549 DU, about 1.82 mm;
- number centred, upright, green, romans.shx.

New drawings must use a true circle, normally 4.0–4.7 mm diameter, with a
1.7–1.9 mm centred upright number. Never reproduce the 0.94277 ellipse
distortion.

There are no AutoCAD LEADER/MLEADER entities. Balloon leaders are straight ACI
3 green LINE entities, normally without arrowheads. They touch the exact pipe
piece/component and finish at the balloon boundary. Keep them short and free
of crossings. Visual behaviour is more important than whether a clean new DWG
uses a no-arrow `MLEADER` or separate LINE plus CIRCLE objects.

## 11. Polylines, circles and projection symbol

The 25 lightweight polylines divide exactly into:

- ten white rectangular borders, two per sheet;
- ten two-vertex `bulge=1` circular inspection bullets, two per sheet;
- five green helper/reference rectangles, one per sheet, which must not be
  copied into final work.

There are no variable-width polylines. Use true circles for new bullets and
balloons when practical.

ISO 35's client projection symbol is exploded ACI 2 yellow geometry with:

- concentric circle radii 129.296 and 204.509 DU;
- vertical centre axis 502.736 DU;
- horizontal centre axis 1176.121 DU;
- CENTER linetype on its axes.

In new work, preserve the supplied cone/circle orientation and relative
proportions while scaling it to the title-block cell. Do not infer or print a
projection-method name unless another client/model source confirms it.

## 12. BOM structure

Use the five-column reference table:

`PART NO | DESCRIPTION | SIZE | LENGTH MM | QTY.`

ISO 35 raw BOM bounding box is `8508.730 x 9522.266` DU. Its six x-gridlines
produce these useful column-width ratios:

| Column | Reference width ratio |
|---|---:|
| Part no. | 11.63% |
| Description | 36.04% |
| Size | 21.13% |
| Length mm | 17.41% |
| Quantity | 13.80% |

The common raw row height is 449.140 DU. The table contains 19 numbered parts
plus an asterisk gasket row. Retain the bottom header and stack the numbered
rows upward. Use green text only for deliberate/current revision emphasis, not
as random decoration.

## 13. Title block and revision strip

ISO 35's reusable title-block hierarchy is:

1. cyan company row;
2. white customer row;
3. white project row;
4. left `NAME | SIGN | DATE` approval grid;
5. right green `LINE NO` field;
6. bottom `SCALE=NTS`, client projection symbol, `SHEET NO.` and `REV.` fields;
7. separate left revision strip `REV. | DESCRIPTION | BY | CHD. | APPD`.

Raw ISO 35 title block: `9695.488 x 4903.402` DU. Its full-width y bands are
company, customer, project, detail and bottom rows. The signature rows are
`DRAN`, `CHK`, `APPD.`. Keep `CHK` and `APPD.` blank without documented client
approval.

Raw revision strip: `12721.432 x 1126.499` DU with columns:

`REV. | DESCRIPTION | BY | CHD. | APPD`

Rebuild these as clean semantic geometry. Do not import the exploded title
block as a single opaque trace.

## 14. Blocks and legacy data

- No block is inserted in model space.
- There are 184 block records, including 177 anonymous dimension blocks.
- Only 162 anonymous dimension blocks are referenced; 15 are stale.
- Dormant named definitions include `TB`, `A$C75C21D4F`, `A$C3055988f`, `*U2`
  and `*U3`; none is instantiated.
- `TB` is a generic 297 x 210 block and is not the active CRE title block.

Do not depend on these dormant definitions. New files should use clean named
blocks only where they improve editability, then run `PURGE`/`AUDIT` before
delivery.

## 15. Standard note content learned from all five sheets

The reference consistently communicates:

1. all dimensions are in mm;
2. flange drilling is to ANSI B16.5 Class 150;
3. PTFE lining is to ASTM D4895;
4. the literal reference wording is `ASTM 1545` (without `F`);
5. hydro test is 29 KG/CM2;
6. spark test is 15 KVA;
7. wooden/plastic covers protect the lining during packing.

Use these only when they apply to the requested source/client scope. Do not
silently change the literal `ASTM 1545` to `ASTM F1545`; make that correction
only when client/engineering evidence confirms it. Do not add a standard or
test requirement that the current job supersedes.

## 16. Non-negotiable rules for future agents

- Source PDF controls fabrication data; this DWG controls presentation only.
- Draw on true A2 unless the client supplies another sheet requirement.
- Use cyan 30/150/90-degree spool geometry, yellow integer dimensions with
  closed-filled arrows, green true-circle balloons/no-arrow leaders, and white
  BOM/title grids.
- Keep dimensions editable/associative in the CAD file whenever practical.
- Put dimension text above and parallel to its line; do not use slash/tick ends.
- Keep balloons, notes, tables and title text upright.
- Do not measure the NTS geometry to invent a label.
- Do not copy non-uniform ellipse distortion, helper rectangles, dormant blocks,
  stale dimension blocks or unused legacy layers.
- Render and zoom-check the final PDF and PNG, then audit DXF and DWG.
