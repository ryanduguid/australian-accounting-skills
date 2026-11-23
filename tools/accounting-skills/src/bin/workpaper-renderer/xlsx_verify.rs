// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Standalone `.xlsx` archive verifier: checks ZIP CRC-32 integrity, mandatory
//! draft banner presence, formula safety, Excel error cells and finite
//! cached-value agreement with deterministic recalculation.

use crate::{
    formula::{CellCoord, GridCell, WorkbookEvaluator, cell_ref, parse_cell_ref},
    model::{DRAFT_BANNER, FormulaCheck, VerificationReport},
    xlsx::xml_unescape,
    zip::read_zip,
};
use std::collections::BTreeMap;

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

fn parse_sheet_paths(entries: &BTreeMap<String, Vec<u8>>) -> Result<Vec<(String, String)>, String> {
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

    let mut rid_to_target = BTreeMap::new();
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

    let mut sheets = Vec::new();
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
    Ok(sheets)
}

#[derive(Debug, Clone)]
enum CachedValue {
    Missing,
    Finite(f64),
    NonFinite(String),
}

fn parse_cached_value(body: &str) -> CachedValue {
    let Some(raw) = extract_tag_text(body, "v") else {
        return CachedValue::Missing;
    };
    let trimmed = raw.trim();
    match trimmed.parse::<f64>() {
        Ok(num) if num.is_finite() => CachedValue::Finite(num),
        _ => CachedValue::NonFinite(trimmed.to_owned()),
    }
}

struct ParsedWorkbook {
    grid: BTreeMap<CellCoord, GridCell>,
    formulas: Vec<(CellCoord, String, CachedValue)>,
    errors: Vec<String>,
    banner_found: bool,
    unverified_mentions: usize,
}

fn record_cell_body(
    coord: CellCoord,
    r_attr: &str,
    cell_type: &str,
    body: &str,
    state: &mut ParsedWorkbook,
) {
    if let Some(formula_text) = extract_tag_text(body, "f") {
        let cached = parse_cached_value(body);
        if cell_type == "e" {
            let code = extract_tag_text(body, "v").unwrap_or_else(|| "#ERROR!".to_owned());
            state.errors.push(format!(
                "{}!{r_attr} carries Excel error {code}",
                coord.sheet
            ));
        }
        state
            .formulas
            .push((coord.clone(), formula_text.clone(), cached));
        state.grid.insert(coord, GridCell::Formula(formula_text));
    } else if cell_type == "inlineStr" {
        let text = extract_tag_text(body, "t").unwrap_or_default();
        state.banner_found |= text.contains(DRAFT_BANNER);
        state.unverified_mentions += text.matches("UNVERIFIED").count();
        state.grid.insert(coord, GridCell::Text(text));
    } else if cell_type == "b" {
        let val = extract_tag_text(body, "v").unwrap_or_default() == "1";
        state.grid.insert(coord, GridCell::Bool(val));
    } else if cell_type == "e" {
        let code = extract_tag_text(body, "v").unwrap_or_else(|| "#ERROR!".to_owned());
        state.errors.push(format!(
            "{}!{r_attr} carries Excel error {code}",
            coord.sheet
        ));
        state.grid.insert(coord, GridCell::Error(code));
    } else if let Some(val_text) = extract_tag_text(body, "v") {
        match val_text.trim().parse::<f64>() {
            Ok(num) if num.is_finite() => {
                state.grid.insert(coord, GridCell::Number(num));
            }
            _ => {
                state.errors.push(format!(
                    "{}!{r_attr} carries non-finite numeric value '{}'",
                    coord.sheet,
                    val_text.trim()
                ));
            }
        }
    }
}

fn parse_cell_segment(sheet_name: &str, segment: &str, state: &mut ParsedWorkbook) {
    let Some(gt) = segment.find('>') else {
        return;
    };
    let attrs = &segment[..gt];
    let Some(end_c) = segment[gt + 1..].find("</c>") else {
        return;
    };
    let Some(r_attr) = extract_attr(attrs, "r") else {
        return;
    };
    let Some((row, col)) = parse_cell_ref(&r_attr) else {
        return;
    };
    let cell_type = extract_attr(attrs, "t").unwrap_or_default();
    let coord = CellCoord {
        sheet: sheet_name.to_owned(),
        row,
        col,
    };
    record_cell_body(
        coord,
        &r_attr,
        &cell_type,
        &segment[gt + 1..gt + 1 + end_c],
        state,
    );
}

fn check_single_formula(
    evaluator: &mut WorkbookEvaluator<'_>,
    coord: &CellCoord,
    formula_text: &str,
    cached: &CachedValue,
    errors: &mut Vec<String>,
) -> FormulaCheck {
    let addr = cell_ref(coord.row, coord.col);
    let cached_num = match cached {
        CachedValue::Finite(c) => Some(*c),
        CachedValue::Missing | CachedValue::NonFinite(_) => None,
    };
    match evaluator.eval_numeric(coord) {
        Ok(val) => {
            let err_msg = match cached {
                CachedValue::Finite(c) if (val - c).abs() > 1e-6 => Some(format!(
                    "{}!{addr}: cached value {c} disagrees with recalculated value {val}",
                    coord.sheet
                )),
                CachedValue::NonFinite(raw) => Some(format!(
                    "{}!{addr}: non-finite cached value '{raw}'",
                    coord.sheet
                )),
                CachedValue::Missing => {
                    Some(format!("{}!{addr}: missing cached value <v>", coord.sheet))
                }
                CachedValue::Finite(_) => None,
            };
            if let Some(msg) = &err_msg {
                errors.push(msg.clone());
            }
            FormulaCheck {
                sheet: coord.sheet.clone(),
                cell: addr,
                formula: format!("={formula_text}"),
                value: Some(val),
                cached: cached_num,
                ok: err_msg.is_none(),
                error: err_msg,
            }
        }
        Err(err) => {
            errors.push(format!("{}!{addr} (={formula_text}): {err}", coord.sheet));
            FormulaCheck {
                sheet: coord.sheet.clone(),
                cell: addr,
                formula: format!("={formula_text}"),
                value: None,
                cached: cached_num,
                ok: false,
                error: Some(err),
            }
        }
    }
}

/// Verify an existing `.xlsx` archive: checks ZIP integrity, XML structure,
/// formula safety, formula evaluation, Excel error cells and cached values.
pub fn verify_xlsx_bytes(bytes: &[u8]) -> Result<VerificationReport, String> {
    let entries = read_zip(bytes)?;
    let sheets = parse_sheet_paths(&entries)?;
    let mut state = ParsedWorkbook {
        grid: BTreeMap::new(),
        formulas: Vec::new(),
        errors: Vec::new(),
        banner_found: false,
        unverified_mentions: 0,
    };
    for (sheet_name, path) in &sheets {
        let xml = std::str::from_utf8(
            entries
                .get(path)
                .ok_or_else(|| format!("missing worksheet entry {path}"))?,
        )
        .map_err(|_| format!("{path} is not valid UTF-8"))?;
        for segment in xml.split("<c ").skip(1) {
            parse_cell_segment(sheet_name, segment, &mut state);
        }
    }
    if !state.banner_found {
        state
            .errors
            .push("missing mandatory DRAFT FOR HUMAN REVIEW banner in workbook".to_owned());
    }

    let mut evaluator = WorkbookEvaluator::new(&state.grid);
    let mut formula_checks = Vec::new();
    for (coord, formula_text, cached) in &state.formulas {
        formula_checks.push(check_single_formula(
            &mut evaluator,
            coord,
            formula_text,
            cached,
            &mut state.errors,
        ));
    }

    Ok(VerificationReport {
        ok: state.errors.is_empty(),
        draft_banner: DRAFT_BANNER.to_owned(),
        formula_count: formula_checks.len(),
        error_count: state.errors.len(),
        open_exception_count: 0,
        unverified_mentions: state.unverified_mentions,
        formulas: formula_checks,
        errors: state.errors,
    })
}
