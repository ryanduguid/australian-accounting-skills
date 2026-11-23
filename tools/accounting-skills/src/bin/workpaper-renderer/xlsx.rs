// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! OOXML `.xlsx` workpaper generator with live formula evaluation, formula
//! injection neutralisation on text cells, and standalone `.xlsx` formula
//! verification (`verify_xlsx_bytes`).

use crate::{
    formula::{CellCoord, GridCell, WorkbookEvaluator, cell_ref, parse_cell_ref},
    model::{CellSpec, DRAFT_BANNER, FormulaCheck, Sheet, VerificationReport, Workpaper},
    zip::{read_zip, write_zip},
};
use std::collections::{BTreeMap, BTreeSet};

pub fn xml_escape(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    for ch in input.chars() {
        match ch {
            '&' => out.push_str("&amp;"),
            '<' => out.push_str("&lt;"),
            '>' => out.push_str("&gt;"),
            '"' => out.push_str("&quot;"),
            '\'' => out.push_str("&apos;"),
            '\t' | '\n' | '\r' => out.push(ch),
            c if (c as u32) < 0x20 => {}
            c => out.push(c),
        }
    }
    out
}

fn xml_unescape(input: &str) -> String {
    input
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&apos;", "'")
        .replace("&amp;", "&")
}

fn sanitize_sheet_name(raw: &str, used: &mut BTreeSet<String>, fallback_index: usize) -> String {
    let mut cleaned: String = raw
        .chars()
        .map(|c| match c {
            ':' | '\\' | '/' | '?' | '*' | '[' | ']' => '-',
            c if (c as u32) < 0x20 => ' ',
            c => c,
        })
        .collect();
    cleaned = cleaned.trim().trim_matches('\'').to_owned();
    if cleaned.is_empty() {
        cleaned = format!("Sheet{fallback_index}");
    }
    let mut base: String = cleaned.chars().take(31).collect();
    let mut candidate = base.clone();
    let mut suffix = 2usize;
    while !used.insert(candidate.to_ascii_lowercase()) {
        let tag = format!(" ({suffix})");
        let max_len = 31usize.saturating_sub(tag.len());
        base = cleaned.chars().take(max_len).collect();
        candidate = format!("{base}{tag}");
        suffix += 1;
    }
    candidate
}

fn style_for_format(format: Option<&str>) -> u32 {
    match format {
        Some("currency") => 3,
        Some("percent") => 4,
        Some("number") => 5,
        _ => 0,
    }
}

fn build_all_sheets(wp: &Workpaper) -> Vec<(String, Vec<String>, Vec<Vec<CellSpec>>)> {
    let mut used = BTreeSet::new();
    let mut out = Vec::new();

    let summary_name = sanitize_sheet_name("Summary", &mut used, 1);
    let summary_rows = vec![
        vec![
            CellSpec::Text(DRAFT_BANNER.to_owned()),
            CellSpec::Text(String::new()),
        ],
        vec![
            CellSpec::Text("Title".to_owned()),
            CellSpec::Text(wp.title.clone()),
        ],
        vec![
            CellSpec::Text("Entity code".to_owned()),
            CellSpec::Text(wp.entity_code.clone()),
        ],
        vec![
            CellSpec::Text("Period".to_owned()),
            CellSpec::Text(wp.period.clone()),
        ],
        vec![
            CellSpec::Text("Status".to_owned()),
            CellSpec::Text(wp.status.clone()),
        ],
        vec![
            CellSpec::Text("Prepared on".to_owned()),
            CellSpec::Text(wp.prepared_on.clone()),
        ],
        vec![
            CellSpec::Text("Reviewer".to_owned()),
            CellSpec::Text(wp.reviewer.clone()),
        ],
        vec![
            CellSpec::Text("Open exceptions".to_owned()),
            CellSpec::Number(wp.exceptions.len() as f64),
        ],
        vec![
            CellSpec::Text("UNVERIFIED mentions".to_owned()),
            CellSpec::Number(wp.unverified_mentions() as f64),
        ],
        vec![
            CellSpec::Text("Summary".to_owned()),
            CellSpec::Text(wp.summary.clone()),
        ],
    ];
    out.push((
        summary_name,
        vec!["Field".to_owned(), "Value".to_owned()],
        summary_rows,
    ));

    for (idx, sheet) in wp.sheets.iter().enumerate() {
        let name = sanitize_sheet_name(&sheet.name, &mut used, idx + 2);
        out.push((name, sheet.headers.clone(), sheet.rows.clone()));
    }

    if !wp.exceptions.is_empty() {
        let name = sanitize_sheet_name("Exceptions", &mut used, out.len() + 1);
        let rows = wp
            .exceptions
            .iter()
            .enumerate()
            .map(|(i, exc)| {
                vec![
                    CellSpec::Text(if exc.id.is_empty() {
                        format!("EXC-{}", i + 1)
                    } else {
                        exc.id.clone()
                    }),
                    CellSpec::Text(exc.item.clone()),
                    CellSpec::Text(exc.status.clone()),
                    CellSpec::Text(exc.evidence_needed.clone()),
                    CellSpec::Text(exc.owner.clone()),
                ]
            })
            .collect();
        out.push((
            name,
            vec![
                "ID".to_owned(),
                "Item".to_owned(),
                "Status".to_owned(),
                "Evidence needed".to_owned(),
                "Owner".to_owned(),
            ],
            rows,
        ));
    }

    if !wp.sources.is_empty() {
        let name = sanitize_sheet_name("Sources", &mut used, out.len() + 1);
        let rows = wp
            .sources
            .iter()
            .map(|src| {
                vec![
                    CellSpec::Text(src.title.clone()),
                    CellSpec::Text(src.reference.clone()),
                    CellSpec::Text(src.checked_at.clone()),
                    CellSpec::Text(src.status.clone()),
                ]
            })
            .collect();
        out.push((
            name,
            vec![
                "Source".to_owned(),
                "Reference".to_owned(),
                "Checked on".to_owned(),
                "Status".to_owned(),
            ],
            rows,
        ));
    }

    out
}

pub fn render_xlsx(wp: &Workpaper) -> Result<(Vec<u8>, VerificationReport), String> {
    let sheets = build_all_sheets(wp);

    // Populate the grid for formula evaluation (row 0 = headers when headers non-empty).
    let mut grid: BTreeMap<CellCoord, GridCell> = BTreeMap::new();
    let mut formula_coords: Vec<(CellCoord, String)> = Vec::new();
    for (sheet_name, headers, rows) in &sheets {
        let row_offset = usize::from(!headers.is_empty());
        for (col, header) in headers.iter().enumerate() {
            grid.insert(
                CellCoord {
                    sheet: sheet_name.clone(),
                    row: 0,
                    col,
                },
                GridCell::Text(header.clone()),
            );
        }
        for (r_idx, row) in rows.iter().enumerate() {
            let row_num = r_idx + row_offset;
            for (col, cell) in row.iter().enumerate() {
                let coord = CellCoord {
                    sheet: sheet_name.clone(),
                    row: row_num,
                    col,
                };
                match cell {
                    CellSpec::Number(n) => {
                        grid.insert(coord, GridCell::Number(*n));
                    }
                    CellSpec::Bool(b) => {
                        grid.insert(coord, GridCell::Bool(*b));
                    }
                    CellSpec::Text(t) => {
                        grid.insert(coord, GridCell::Text(t.clone()));
                    }
                    CellSpec::Formula { formula, .. } => {
                        formula_coords.push((coord.clone(), formula.clone()));
                        grid.insert(coord, GridCell::Formula(formula.clone()));
                    }
                }
            }
        }
    }

    let mut evaluator = WorkbookEvaluator::new(&grid);
    let mut eval_results: BTreeMap<CellCoord, Result<f64, String>> = BTreeMap::new();
    let mut formula_checks = Vec::new();
    let mut errors = Vec::new();

    for (coord, formula) in &formula_coords {
        let res = evaluator.eval_numeric(coord);
        match &res {
            Ok(val) => {
                formula_checks.push(FormulaCheck {
                    sheet: coord.sheet.clone(),
                    cell: cell_ref(coord.row, coord.col),
                    formula: formula.clone(),
                    value: Some(*val),
                    cached: Some(*val),
                    ok: true,
                    error: None,
                });
            }
            Err(err) => {
                let msg = format!(
                    "{}!{} ({formula}): {err}",
                    coord.sheet,
                    cell_ref(coord.row, coord.col)
                );
                errors.push(msg);
                formula_checks.push(FormulaCheck {
                    sheet: coord.sheet.clone(),
                    cell: cell_ref(coord.row, coord.col),
                    formula: formula.clone(),
                    value: None,
                    cached: None,
                    ok: false,
                    error: Some(err.clone()),
                });
            }
        }
        eval_results.insert(coord.clone(), res);
    }

    let mut files: BTreeMap<String, Vec<u8>> = BTreeMap::new();

    // [Content_Types].xml
    let mut content_types = String::from(
        r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
"#,
    );
    for idx in 1..=sheets.len() {
        content_types.push_str(&format!(
            r#"  <Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
"#
        ));
    }
    content_types.push_str("</Types>\n");
    files.insert("[Content_Types].xml".to_owned(), content_types.into_bytes());

    // _rels/.rels
    files.insert(
        "_rels/.rels".to_owned(),
        br#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"#
        .to_vec(),
    );

    // xl/workbook.xml & xl/_rels/workbook.xml.rels
    let mut workbook_xml = String::from(
        r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
"#,
    );
    let mut wb_rels = String::from(
        r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
"#,
    );
    for (idx, (sheet_name, _, _)) in sheets.iter().enumerate() {
        let sheet_id = idx + 1;
        workbook_xml.push_str(&format!(
            "    <sheet name=\"{}\" sheetId=\"{sheet_id}\" r:id=\"rId{sheet_id}\"/>\n",
            xml_escape(sheet_name)
        ));
        wb_rels.push_str(&format!(
            "  <Relationship Id=\"rId{sheet_id}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet{sheet_id}.xml\"/>\n"
        ));
    }
    let styles_rid = sheets.len() + 1;
    wb_rels.push_str(&format!(
        "  <Relationship Id=\"rId{styles_rid}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>\n</Relationships>\n"
    ));
    workbook_xml.push_str("  </sheets>\n</workbook>\n");
    files.insert("xl/workbook.xml".to_owned(), workbook_xml.into_bytes());
    files.insert(
        "xl/_rels/workbook.xml.rels".to_owned(),
        wb_rels.into_bytes(),
    );

    // xl/styles.xml: 0=default, 1=header(bold navy), 2=banner(amber), 3=currency, 4=percent, 5=number
    let styles_xml = r###"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="3">
    <numFmt numFmtId="164" formatCode="$#,##0.00;($#,##0.00);&quot;-&quot;"/>
    <numFmt numFmtId="165" formatCode="0.00%"/>
    <numFmt numFmtId="166" formatCode="#,##0.00"/>
  </numFmts>
  <fonts count="3">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><color rgb="FF92400E"/><name val="Calibri"/></font>
  </fonts>
  <fills count="4">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1B365D"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFEF3C7"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1">
    <border><left/><right/><top/><bottom/><diagonal/></border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="6">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
    <xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
    <xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
    <xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
    <xf numFmtId="166" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
  </cellXfs>
</styleSheet>
"###;
    files.insert("xl/styles.xml".to_owned(), styles_xml.as_bytes().to_vec());

    // Worksheets
    for (idx, (sheet_name, headers, rows)) in sheets.iter().enumerate() {
        let mut xml = String::from(
            r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
"#,
        );
        let row_offset = usize::from(!headers.is_empty());
        if !headers.is_empty() {
            xml.push_str("    <row r=\"1\">\n");
            for (col, h) in headers.iter().enumerate() {
                let r = cell_ref(0, col);
                xml.push_str(&format!(
                    "      <c r=\"{r}\" s=\"1\" t=\"inlineStr\"><is><t>{}</t></is></c>\n",
                    xml_escape(h)
                ));
            }
            xml.push_str("    </row>\n");
        }
        for (r_idx, row) in rows.iter().enumerate() {
            let row_num = r_idx + row_offset;
            let excel_row = row_num + 1;
            xml.push_str(&format!("    <row r=\"{excel_row}\">\n"));
            for (col, cell) in row.iter().enumerate() {
                let r = cell_ref(row_num, col);
                let is_banner = sheet_name == "Summary" && r_idx == 0;
                match cell {
                    CellSpec::Text(t) => {
                        let style = if is_banner { " s=\"2\"" } else { "" };
                        xml.push_str(&format!(
                            "      <c r=\"{r}\"{style} t=\"inlineStr\"><is><t>{}</t></is></c>\n",
                            xml_escape(t)
                        ));
                    }
                    CellSpec::Number(n) => {
                        xml.push_str(&format!("      <c r=\"{r}\"><v>{n}</v></c>\n"));
                    }
                    CellSpec::Bool(b) => {
                        let v = if *b { 1 } else { 0 };
                        xml.push_str(&format!("      <c r=\"{r}\" t=\"b\"><v>{v}</v></c>\n"));
                    }
                    CellSpec::Formula { formula, format } => {
                        let expr = formula.trim().strip_prefix('=').unwrap_or(formula.trim());
                        let s = style_for_format(format.as_deref());
                        let coord = CellCoord {
                            sheet: sheet_name.clone(),
                            row: row_num,
                            col,
                        };
                        match eval_results.get(&coord) {
                            Some(Ok(val)) => {
                                xml.push_str(&format!(
                                    "      <c r=\"{r}\" s=\"{s}\"><f>{}</f><v>{val}</v></c>\n",
                                    xml_escape(expr)
                                ));
                            }
                            Some(Err(err)) => {
                                let code = err.split(':').next().unwrap_or("#VALUE!");
                                xml.push_str(&format!(
                                    "      <c r=\"{r}\" s=\"{s}\" t=\"e\"><f>{}</f><v>{}</v></c>\n",
                                    xml_escape(expr),
                                    xml_escape(code)
                                ));
                            }
                            None => {}
                        }
                    }
                }
            }
            xml.push_str("    </row>\n");
        }
        xml.push_str("  </sheetData>\n</worksheet>\n");
        files.insert(
            format!("xl/worksheets/sheet{}.xml", idx + 1),
            xml.into_bytes(),
        );
    }

    let archive = write_zip(&files)?;
    let report = VerificationReport {
        ok: errors.is_empty(),
        draft_banner: DRAFT_BANNER.to_owned(),
        formula_count: formula_checks.len(),
        error_count: errors.len(),
        open_exception_count: wp.exceptions.len(),
        unverified_mentions: wp.unverified_mentions(),
        formulas: formula_checks,
        errors,
    };
    Ok((archive, report))
}

fn extract_attr(tag: &str, attr: &str) -> Option<String> {
    let needle = format!("{attr}=\"");
    let start = tag.find(&needle)? + needle.len();
    let end = tag[start..].find('"')?;
    Some(xml_unescape(&tag[start..start + end]))
}

fn extract_tag_text(fragment: &str, tag_name: &str) -> Option<String> {
    let open = format!("<{tag_name}");
    let start = fragment.find(&open)?;
    let gt = fragment[start..].find('>')? + start + 1;
    let close = format!("</{tag_name}>");
    let end = fragment[gt..].find(&close)? + gt;
    Some(xml_unescape(&fragment[gt..end]))
}

/// Verify an existing `.xlsx` archive: checks ZIP integrity, XML structure,
/// formula safety, formula evaluation, Excel error cells and cached values.
pub fn verify_xlsx_bytes(bytes: &[u8]) -> Result<VerificationReport, String> {
    let entries = read_zip(bytes)?;
    let wb_xml = std::str::from_utf8(
        entries
            .get("xl/workbook.xml")
            .ok_or_else(|| "missing xl/workbook.xml".to_owned())?,
    )
    .map_err(|_| "xl/workbook.xml is not UTF-8".to_owned())?;
    let rels_xml = std::str::from_utf8(
        entries
            .get("xl/_rels/workbook.xml.rels")
            .ok_or_else(|| "missing xl/_rels/workbook.xml.rels".to_owned())?,
    )
    .map_err(|_| "xl/_rels/workbook.xml.rels is not UTF-8".to_owned())?;

    let mut rid_to_target: BTreeMap<String, String> = BTreeMap::new();
    for segment in rels_xml.split("<Relationship ").skip(1) {
        if let Some(end) = segment.find("/>") {
            let attrs = &segment[..end];
            if let (Some(id), Some(target)) =
                (extract_attr(attrs, "Id"), extract_attr(attrs, "Target"))
            {
                rid_to_target.insert(id, target);
            }
        }
    }

    let mut sheets: Vec<(String, String)> = Vec::new();
    for segment in wb_xml.split("<sheet ").skip(1) {
        if let Some(end) = segment.find("/>") {
            let attrs = &segment[..end];
            if let (Some(name), Some(rid)) =
                (extract_attr(attrs, "name"), extract_attr(attrs, "r:id"))
                && let Some(target) = rid_to_target.get(&rid)
            {
                let path = if target.starts_with("xl/") {
                    target.clone()
                } else {
                    format!("xl/{target}")
                };
                sheets.push((name, path));
            }
        }
    }
    if sheets.is_empty() {
        return Err("workbook declares no worksheets".to_owned());
    }

    let mut grid: BTreeMap<CellCoord, GridCell> = BTreeMap::new();
    let mut formulas: Vec<(CellCoord, String, Option<f64>)> = Vec::new();
    let mut errors: Vec<String> = Vec::new();
    let mut banner_found = false;
    let mut unverified_mentions = 0usize;

    for (sheet_name, path) in &sheets {
        let xml = std::str::from_utf8(
            entries
                .get(path)
                .ok_or_else(|| format!("missing worksheet entry {path}"))?,
        )
        .map_err(|_| format!("{path} is not valid UTF-8"))?;

        for segment in xml.split("<c ").skip(1) {
            let Some(gt) = segment.find('>') else {
                continue;
            };
            let attrs = &segment[..gt];
            let Some(end_c) = segment[gt + 1..].find("</c>") else {
                continue;
            };
            let body = &segment[gt + 1..gt + 1 + end_c];
            let Some(r_attr) = extract_attr(attrs, "r") else {
                continue;
            };
            let Some((row, col)) = parse_cell_ref(&r_attr) else {
                continue;
            };
            let cell_type = extract_attr(attrs, "t").unwrap_or_default();
            let coord = CellCoord {
                sheet: sheet_name.clone(),
                row,
                col,
            };

            if let Some(formula_text) = extract_tag_text(body, "f") {
                let cached = extract_tag_text(body, "v").and_then(|v| v.trim().parse::<f64>().ok());
                if cell_type == "e" {
                    let code = extract_tag_text(body, "v").unwrap_or_else(|| "#ERROR!".to_owned());
                    errors.push(format!("{sheet_name}!{r_attr} carries Excel error {code}"));
                }
                formulas.push((coord.clone(), formula_text.clone(), cached));
                grid.insert(coord, GridCell::Formula(formula_text));
            } else if cell_type == "inlineStr" {
                let text = extract_tag_text(body, "t").unwrap_or_default();
                if text.contains(DRAFT_BANNER) {
                    banner_found = true;
                }
                unverified_mentions += text.matches("UNVERIFIED").count();
                grid.insert(coord, GridCell::Text(text));
            } else if cell_type == "b" {
                let val = extract_tag_text(body, "v").unwrap_or_default() == "1";
                grid.insert(coord, GridCell::Bool(val));
            } else if cell_type == "e" {
                let code = extract_tag_text(body, "v").unwrap_or_else(|| "#ERROR!".to_owned());
                errors.push(format!("{sheet_name}!{r_attr} carries Excel error {code}"));
                grid.insert(coord, GridCell::Error(code));
            } else if let Some(val_text) = extract_tag_text(body, "v")
                && let Ok(num) = val_text.trim().parse::<f64>()
            {
                grid.insert(coord, GridCell::Number(num));
            }
        }
    }

    if !banner_found {
        errors.push("missing mandatory DRAFT FOR HUMAN REVIEW banner in workbook".to_owned());
    }

    let mut evaluator = WorkbookEvaluator::new(&grid);
    let mut formula_checks = Vec::new();
    for (coord, formula_text, cached) in &formulas {
        let addr = cell_ref(coord.row, coord.col);
        match evaluator.eval_numeric(coord) {
            Ok(val) => {
                let mut ok = true;
                let mut err_msg = None;
                match cached {
                    Some(c) if (val - c).abs() > 1e-6 => {
                        ok = false;
                        let msg = format!(
                            "{}!{addr}: cached value {c} disagrees with recalculated value {val}",
                            coord.sheet
                        );
                        errors.push(msg.clone());
                        err_msg = Some(msg);
                    }
                    None => {
                        ok = false;
                        let msg = format!("{}!{addr}: missing cached value <v>", coord.sheet);
                        errors.push(msg.clone());
                        err_msg = Some(msg);
                    }
                    Some(_) => {}
                }
                formula_checks.push(FormulaCheck {
                    sheet: coord.sheet.clone(),
                    cell: addr,
                    formula: format!("={formula_text}"),
                    value: Some(val),
                    cached: *cached,
                    ok,
                    error: err_msg,
                });
            }
            Err(err) => {
                let msg = format!("{}!{addr} (={formula_text}): {err}", coord.sheet);
                errors.push(msg);
                formula_checks.push(FormulaCheck {
                    sheet: coord.sheet.clone(),
                    cell: addr,
                    formula: format!("={formula_text}"),
                    value: None,
                    cached: *cached,
                    ok: false,
                    error: Some(err),
                });
            }
        }
    }

    Ok(VerificationReport {
        ok: errors.is_empty(),
        draft_banner: DRAFT_BANNER.to_owned(),
        formula_count: formula_checks.len(),
        error_count: errors.len(),
        open_exception_count: 0,
        unverified_mentions,
        formulas: formula_checks,
        errors,
    })
}

#[allow(dead_code)]
fn _keep_sheet_type(_: &Sheet) {}
