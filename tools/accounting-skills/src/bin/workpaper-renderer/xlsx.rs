// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! OOXML `.xlsx` workpaper generator with live formula evaluation and formula
//! injection neutralisation on inline-string text cells.

use crate::{
    formula::{CellCoord, GridCell, WorkbookEvaluator, cell_ref},
    model::{CellSpec, DRAFT_BANNER, FormulaCheck, VerificationReport, Workpaper},
    zip::write_zip,
};
use std::collections::{BTreeMap, BTreeSet};

const STYLES_XML: &str = r###"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
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

const RELS_XML: &[u8] = br#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"#;

type SheetData = (String, Vec<String>, Vec<Vec<CellSpec>>);
type EvalMap = BTreeMap<CellCoord, Result<f64, String>>;

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

pub fn xml_unescape(input: &str) -> String {
    input
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&apos;", "'")
        .replace("&amp;", "&")
}

fn sanitize_sheet_name(raw: &str, used: &mut BTreeSet<String>, fallback_index: usize) -> String {
    let cleaned: String = raw
        .chars()
        .map(|c| match c {
            ':' | '\\' | '/' | '?' | '*' | '[' | ']' => '-',
            c if (c as u32) < 0x20 => ' ',
            c => c,
        })
        .collect::<String>()
        .trim()
        .trim_matches('\'')
        .to_owned();
    let cleaned = if cleaned.is_empty() {
        format!("Sheet{fallback_index}")
    } else {
        cleaned
    };
    let mut candidate: String = cleaned.chars().take(31).collect();
    let mut suffix = 2usize;
    while !used.insert(candidate.to_ascii_lowercase()) {
        let tag = format!(" ({suffix})");
        let base: String = cleaned
            .chars()
            .take(31usize.saturating_sub(tag.len()))
            .collect();
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

fn summary_sheet(wp: &Workpaper, used: &mut BTreeSet<String>) -> SheetData {
    let name = sanitize_sheet_name("Summary", used, 1);
    let rows = vec![
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
    (name, vec!["Field".to_owned(), "Value".to_owned()], rows)
}

fn exceptions_sheet(wp: &Workpaper, used: &mut BTreeSet<String>, fallback: usize) -> SheetData {
    let name = sanitize_sheet_name("Exceptions", used, fallback);
    let rows = wp
        .exceptions
        .iter()
        .enumerate()
        .map(|(i, exc)| {
            let id = if exc.id.is_empty() {
                format!("EXC-{}", i + 1)
            } else {
                exc.id.clone()
            };
            vec![
                CellSpec::Text(id),
                CellSpec::Text(exc.item.clone()),
                CellSpec::Text(exc.status.clone()),
                CellSpec::Text(exc.evidence_needed.clone()),
                CellSpec::Text(exc.owner.clone()),
            ]
        })
        .collect();
    let headers = ["ID", "Item", "Status", "Evidence needed", "Owner"]
        .map(str::to_owned)
        .to_vec();
    (name, headers, rows)
}

fn sources_sheet(wp: &Workpaper, used: &mut BTreeSet<String>, fallback: usize) -> SheetData {
    let name = sanitize_sheet_name("Sources", used, fallback);
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
    let headers = ["Source", "Reference", "Checked on", "Status"]
        .map(str::to_owned)
        .to_vec();
    (name, headers, rows)
}

fn build_all_sheets(wp: &Workpaper) -> Vec<SheetData> {
    let mut used = BTreeSet::new();
    let mut out = vec![summary_sheet(wp, &mut used)];
    for (idx, sheet) in wp.sheets.iter().enumerate() {
        let name = sanitize_sheet_name(&sheet.name, &mut used, idx + 2);
        out.push((name, sheet.headers.clone(), sheet.rows.clone()));
    }
    if !wp.exceptions.is_empty() {
        let next = out.len() + 1;
        out.push(exceptions_sheet(wp, &mut used, next));
    }
    if !wp.sources.is_empty() {
        let next = out.len() + 1;
        out.push(sources_sheet(wp, &mut used, next));
    }
    out
}

fn populate_grid(
    sheets: &[SheetData],
) -> (BTreeMap<CellCoord, GridCell>, Vec<(CellCoord, String)>) {
    let mut grid = BTreeMap::new();
    let mut formulas = Vec::new();
    for (sheet_name, headers, rows) in sheets {
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
            for (col, cell) in row.iter().enumerate() {
                let coord = CellCoord {
                    sheet: sheet_name.clone(),
                    row: r_idx + row_offset,
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
                        formulas.push((coord.clone(), formula.clone()));
                        grid.insert(coord, GridCell::Formula(formula.clone()));
                    }
                }
            }
        }
    }
    (grid, formulas)
}

fn evaluate_formulas(
    grid: &BTreeMap<CellCoord, GridCell>,
    formulas: &[(CellCoord, String)],
) -> (EvalMap, Vec<FormulaCheck>, Vec<String>) {
    let mut evaluator = WorkbookEvaluator::new(grid);
    let mut eval_results = BTreeMap::new();
    let mut checks = Vec::new();
    let mut errors = Vec::new();
    for (coord, formula) in formulas {
        let res = evaluator.eval_numeric(coord);
        let addr = cell_ref(coord.row, coord.col);
        match &res {
            Ok(val) => checks.push(FormulaCheck {
                sheet: coord.sheet.clone(),
                cell: addr,
                formula: formula.clone(),
                value: Some(*val),
                cached: Some(*val),
                ok: true,
                error: None,
            }),
            Err(err) => {
                errors.push(format!("{}!{addr} ({formula}): {err}", coord.sheet));
                checks.push(FormulaCheck {
                    sheet: coord.sheet.clone(),
                    cell: addr,
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
    (eval_results, checks, errors)
}

fn render_cell_xml(
    sheet_name: &str,
    row_num: usize,
    col: usize,
    is_banner: bool,
    cell: &CellSpec,
    eval_results: &EvalMap,
) -> String {
    let r = cell_ref(row_num, col);
    match cell {
        CellSpec::Text(t) => {
            let style = if is_banner { " s=\"2\"" } else { "" };
            format!(
                "      <c r=\"{r}\"{style} t=\"inlineStr\"><is><t>{}</t></is></c>\n",
                xml_escape(t)
            )
        }
        CellSpec::Number(n) => format!("      <c r=\"{r}\"><v>{n}</v></c>\n"),
        CellSpec::Bool(b) => {
            format!("      <c r=\"{r}\" t=\"b\"><v>{}</v></c>\n", u8::from(*b))
        }
        CellSpec::Formula { formula, format } => {
            let expr = formula.trim().strip_prefix('=').unwrap_or(formula.trim());
            let s = style_for_format(format.as_deref());
            let coord = CellCoord {
                sheet: sheet_name.to_owned(),
                row: row_num,
                col,
            };
            match eval_results.get(&coord) {
                Some(Ok(val)) => format!(
                    "      <c r=\"{r}\" s=\"{s}\"><f>{}</f><v>{val}</v></c>\n",
                    xml_escape(expr)
                ),
                Some(Err(err)) => {
                    let code = err.split(':').next().unwrap_or("#VALUE!");
                    format!(
                        "      <c r=\"{r}\" s=\"{s}\" t=\"e\"><f>{}</f><v>{}</v></c>\n",
                        xml_escape(expr),
                        xml_escape(code)
                    )
                }
                None => String::new(),
            }
        }
    }
}

fn render_worksheet_xml(sheet: &SheetData, eval_results: &EvalMap) -> Vec<u8> {
    let (sheet_name, headers, rows) = sheet;
    let mut xml = String::from(
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n\
         <worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">\n  <sheetData>\n",
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
        xml.push_str(&format!("    <row r=\"{}\">\n", row_num + 1));
        for (col, cell) in row.iter().enumerate() {
            let is_banner = sheet_name == "Summary" && r_idx == 0;
            xml.push_str(&render_cell_xml(
                sheet_name,
                row_num,
                col,
                is_banner,
                cell,
                eval_results,
            ));
        }
        xml.push_str("    </row>\n");
    }
    xml.push_str("  </sheetData>\n</worksheet>\n");
    xml.into_bytes()
}

fn write_workbook_metadata(sheets: &[SheetData], files: &mut BTreeMap<String, Vec<u8>>) {
    let mut content_types = String::from(
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n\
         <Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">\n\
           <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>\n\
           <Default Extension=\"xml\" ContentType=\"application/xml\"/>\n\
           <Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>\n\
           <Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>\n",
    );
    let mut wb_xml = String::from(
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n\
         <workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">\n  <sheets>\n",
    );
    let mut wb_rels = String::from(
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n\
         <Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">\n",
    );
    for (idx, (sheet_name, _, _)) in sheets.iter().enumerate() {
        let id = idx + 1;
        content_types.push_str(&format!(
            "  <Override PartName=\"/xl/worksheets/sheet{id}.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>\n"
        ));
        wb_xml.push_str(&format!(
            "    <sheet name=\"{}\" sheetId=\"{id}\" r:id=\"rId{id}\"/>\n",
            xml_escape(sheet_name)
        ));
        wb_rels.push_str(&format!(
            "  <Relationship Id=\"rId{id}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet{id}.xml\"/>\n"
        ));
    }
    let styles_rid = sheets.len() + 1;
    content_types.push_str("</Types>\n");
    wb_xml.push_str("  </sheets>\n</workbook>\n");
    wb_rels.push_str(&format!(
        "  <Relationship Id=\"rId{styles_rid}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>\n</Relationships>\n"
    ));
    files.insert("[Content_Types].xml".to_owned(), content_types.into_bytes());
    files.insert("_rels/.rels".to_owned(), RELS_XML.to_vec());
    files.insert("xl/workbook.xml".to_owned(), wb_xml.into_bytes());
    files.insert(
        "xl/_rels/workbook.xml.rels".to_owned(),
        wb_rels.into_bytes(),
    );
    files.insert("xl/styles.xml".to_owned(), STYLES_XML.as_bytes().to_vec());
}

pub fn render_xlsx(wp: &Workpaper) -> Result<(Vec<u8>, VerificationReport), String> {
    let sheets = build_all_sheets(wp);
    let (grid, formulas) = populate_grid(&sheets);
    let (eval_results, formula_checks, errors) = evaluate_formulas(&grid, &formulas);

    let mut files = BTreeMap::new();
    write_workbook_metadata(&sheets, &mut files);
    for (idx, sheet) in sheets.iter().enumerate() {
        files.insert(
            format!("xl/worksheets/sheet{}.xml", idx + 1),
            render_worksheet_xml(sheet, &eval_results),
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
