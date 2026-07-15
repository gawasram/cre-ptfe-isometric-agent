# CRE PTFE Drawing Validation Checklist

## Source truth

- [ ] Split one-page PDF was used when available.
- [ ] Correct PDF page and document page were used.
- [ ] Line number, unit and sheet number exactly match the source.
- [ ] External connection and continuation wording are source-supported.
- [ ] Every source cut piece is listed with cut and overall dimensions.
- [ ] Every component quantity is reconciled with physical occurrences.
- [ ] Different component lengths are kept as separate fabrication rows.
- [ ] Reducer offset/orientation and instrument tags are retained.

## Geometry

- [ ] The topology is one connected network except at real continuation points.
- [ ] Split branches rejoin at the correct tee.
- [ ] All elbows, tees, valves, flanges, reducers, instruments and blinds are connected.
- [ ] Geometry has not been scaled to manufacture; `SCALE=NTS` is present.
- [ ] Ordinary spool runs use exact 30-degree, 150-degree or vertical axes.
- [ ] Any additional display axis is source-proven, recorded, and passed explicitly to the validator with `--allow-axis`.
- [ ] No decorative arcs, splines, fillets or image-traced wobble have been added.
- [ ] Curves appear only in source-supported component/symbol details.
- [ ] No source weld IDs, elevation clutter or gasket codes remain unless requested.

## Balloons and BOM

- [ ] Every pipe spool has its own fabrication part number.
- [ ] Every component balloon points to the correct symbol.
- [ ] Repeated components use the same part number at every occurrence.
- [ ] Balloon occurrence counts equal BOM quantities.
- [ ] Every balloon is a true circle, approximately 4.0-4.7 mm diameter, not a distorted ellipse.
- [ ] Balloon numbers are upright, centred and approximately 1.7-1.9 mm high.
- [ ] Green leaders are straight, normally arrowless, touch the exact component and stop at the balloon perimeter.
- [ ] Leaders do not cross dimension text, other leaders or component symbols unnecessarily.
- [ ] BOM header is at the bottom and rows stack upward.
- [ ] BOM columns start from the client proportions `11.63 | 36.04 | 21.13 | 17.41 | 13.80` percent.
- [ ] Sizes, lengths and quantities are readable and correct.

## Dimensions

- [ ] All cut/overall pairs are shown.
- [ ] All valve and instrument face-to-face dimensions are shown.
- [ ] All short tee/elbow/valve legs are shown without normalising different values.
- [ ] Dimension leaders and text do not hide component symbols.
- [ ] Dimension and extension lines are ACI 2 yellow and use aligned geometry on isometric runs.
- [ ] Extension lines use mandatory 30-degree or 150-degree isometric oblique angles (`oblique_angle` DXF Group Code 52) following isometric projection axes.
- [ ] Both ends use closed-filled triangular arrows; no slash/tick ends remain.
- [ ] Arrow length approximately equals the 2.0-2.2 mm dimension text height; arrow base is approximately one-third of its length.
- [ ] Extension origin offset and extension beyond are each approximately 0.5 x text height; text gap is approximately 0.4 x text height.
- [ ] Dimension text is above, parallel to and centred on its dimension line where space permits.
- [ ] Dimension values are integer source-verified millimetres, not measurements taken from the NTS drawing.
- [ ] Any manual dimension text override is traceable to a source annotation.
- [ ] CAD dimensions remain editable/associative wherever practical.

## Text and symbols

- [ ] Arial Narrow is used for notes, tables and title fields; Romans is used for dimensions and balloon numbers.
- [ ] The DXF contains text styles named 'CRE_ARIAL_NARROW' (mapping to Arial Narrow.ttf), 'CRE_ARIAL_NARROW_BOLD' (mapping to Arial Narrow Bold.ttf), and 'CRE_ROMANS' (mapping to romans.shx).
- [ ] Notes, BOM, title fields and balloon numbers are horizontal.
- [ ] Only inline pipe-size/`NS` labels rotate with the 30/150/90-degree axis.
- [ ] Company title is cyan; line number/current revision emphasis is green only when intentional.
- [ ] Client cone/circle projection symbol is present in the supplied orientation with yellow CENTER axes.
- [ ] No unsupported projection-method name was inferred from the symbol alone.
- [ ] Continuous is used for ordinary geometry; HIDDEN/CENTER are used only for their real purpose.

## Format

- [ ] A2 portrait page is 420 x 594 mm.
- [ ] CAD contains an A2 paper-space page setup as well as the A2 model-space frame.
- [ ] A centred 420 x 594 mm viewport uses a 594 mm view height so the full model sheet plots at 1:1 without shrinkage or clipping.
- [ ] Warning boxes, double frame, notes, BOM, revision strip and CRE title block are present.
- [ ] No green helper/reference rectangle from `ISO_31_TO_35.dwg` is present.
- [ ] No dormant legacy `TB`, `A$C...`, stale anonymous dimension block or unused layer was copied into the file.
- [ ] AutoCAD colours match the CRE standard.
- [ ] PDF plots in black unless colour output was requested.
- [ ] `DRAN` is filled correctly; `CHK` and `APPD` are not falsely completed.

## File quality

- [ ] Latest PDF was rendered to PNG and inspected at full page and zoomed detail.
- [ ] No clipping, overlaps, broken glyphs or unreadable table text remain.
- [ ] Zoomed PNG/PDF checks confirm arrowheads, extension gaps, balloon centring, leader endpoints and pipe-axis angles.
- [ ] `work/validate_cre_ptfe_dxf.py` passes with no undocumented exception.
- [ ] DXF audit reports zero errors and zero fixes.
- [ ] DWG AutoCAD `AUDIT` reports zero errors.
- [ ] DWG, DXF, PDF and PNG share the same stable basename.
- [ ] If an older drawing is open in AutoCAD, the user is told to close it without overwriting the corrected file.
