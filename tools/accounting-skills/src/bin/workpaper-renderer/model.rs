// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Structured workpaper model, verification report and schema definition.

use serde::{Deserialize, Serialize};

pub const DRAFT_BANNER: &str =
    "DRAFT FOR HUMAN REVIEW - PREP ONLY - NOT FOR LODGEMENT - NOT ADVICE";

const SCHEMA_JSON: &str = r#"{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Australian Accounting Workpaper",
  "type": "object",
  "required": ["title"],
  "properties": {
    "title": { "type": "string" },
    "entity_code": { "type": "string", "description": "De-identified firm code (no client TFN/ABN)" },
    "period": { "type": "string" },
    "prepared_on": { "type": "string" },
    "reviewer": { "type": "string" },
    "status": { "type": "string", "default": "DRAFT_FOR_REVIEW" },
    "summary": { "type": "string" },
    "sections": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["heading"],
        "properties": {
          "heading": { "type": "string" },
          "paragraphs": { "type": "array", "items": { "type": "string" } },
          "bullets": { "type": "array", "items": { "type": "string" } },
          "table": {
            "type": "object",
            "properties": {
              "headers": { "type": "array", "items": { "type": "string" } },
              "rows": { "type": "array", "items": { "type": "array", "items": { "type": "string" } } }
            }
          }
        }
      }
    },
    "sheets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": { "type": "string" },
          "headers": { "type": "array", "items": { "type": "string" } },
          "rows": {
            "type": "array",
            "items": {
              "type": "array",
              "items": {
                "oneOf": [
                  { "type": "string" },
                  { "type": "number" },
                  { "type": "boolean" },
                  {
                    "type": "object",
                    "required": ["formula"],
                    "properties": {
                      "formula": { "type": "string" },
                      "format": { "type": "string", "enum": ["currency", "percent", "number"] }
                    }
                  }
                ]
              }
            }
          }
        }
      }
    },
    "exceptions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["item"],
        "properties": {
          "id": { "type": "string" },
          "item": { "type": "string" },
          "status": { "type": "string" },
          "evidence_needed": { "type": "string" },
          "owner": { "type": "string" }
        }
      }
    },
    "sources": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["title"],
        "properties": {
          "title": { "type": "string" },
          "reference": { "type": "string" },
          "checked_at": { "type": "string" },
          "status": { "type": "string" }
        }
      }
    }
  }
}
"#;

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Workpaper {
    pub title: String,
    #[serde(default)]
    pub entity_code: String,
    #[serde(default)]
    pub period: String,
    #[serde(default)]
    pub prepared_on: String,
    #[serde(default)]
    pub reviewer: String,
    #[serde(default = "default_status")]
    pub status: String,
    #[serde(default)]
    pub summary: String,
    #[serde(default)]
    pub sections: Vec<Section>,
    #[serde(default)]
    pub sheets: Vec<Sheet>,
    #[serde(default)]
    pub exceptions: Vec<ExceptionItem>,
    #[serde(default)]
    pub sources: Vec<SourceRecord>,
}

fn default_status() -> String {
    "DRAFT_FOR_REVIEW".to_owned()
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Section {
    pub heading: String,
    #[serde(default)]
    pub paragraphs: Vec<String>,
    #[serde(default)]
    pub bullets: Vec<String>,
    #[serde(default)]
    pub table: Option<TextTable>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TextTable {
    pub headers: Vec<String>,
    pub rows: Vec<Vec<String>>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Sheet {
    pub name: String,
    #[serde(default)]
    pub headers: Vec<String>,
    #[serde(default)]
    pub rows: Vec<Vec<CellSpec>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum CellSpec {
    Formula {
        formula: String,
        #[serde(default)]
        format: Option<String>,
    },
    Number(f64),
    Bool(bool),
    Text(String),
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ExceptionItem {
    #[serde(default)]
    pub id: String,
    pub item: String,
    #[serde(default)]
    pub status: String,
    #[serde(default)]
    pub evidence_needed: String,
    #[serde(default)]
    pub owner: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SourceRecord {
    pub title: String,
    #[serde(default)]
    pub reference: String,
    #[serde(default)]
    pub checked_at: String,
    #[serde(default)]
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FormulaCheck {
    pub sheet: String,
    pub cell: String,
    pub formula: String,
    pub value: Option<f64>,
    pub cached: Option<f64>,
    pub ok: bool,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerificationReport {
    pub ok: bool,
    pub draft_banner: String,
    pub formula_count: usize,
    pub error_count: usize,
    pub open_exception_count: usize,
    pub unverified_mentions: usize,
    pub formulas: Vec<FormulaCheck>,
    pub errors: Vec<String>,
}

fn count_unverified(text: &str) -> usize {
    text.matches("UNVERIFIED").count()
}

fn section_unverified(section: &Section) -> usize {
    let mut total = count_unverified(&section.heading);
    for p in &section.paragraphs {
        total += count_unverified(p);
    }
    for b in &section.bullets {
        total += count_unverified(b);
    }
    if let Some(table) = &section.table {
        total += table
            .headers
            .iter()
            .map(|h| count_unverified(h))
            .sum::<usize>();
        for row in &table.rows {
            total += row.iter().map(|c| count_unverified(c)).sum::<usize>();
        }
    }
    total
}

impl Workpaper {
    /// Count mentions of `UNVERIFIED` across the workpaper so the cover banner
    /// never conceals unverified figures or missing primary sources.
    pub fn unverified_mentions(&self) -> usize {
        let mut total = count_unverified(&self.title)
            + count_unverified(&self.status)
            + count_unverified(&self.summary);
        total += self.sections.iter().map(section_unverified).sum::<usize>();
        for sheet in &self.sheets {
            total += sheet
                .headers
                .iter()
                .map(|h| count_unverified(h))
                .sum::<usize>();
            for row in &sheet.rows {
                for cell in row {
                    if let CellSpec::Text(text) = cell {
                        total += count_unverified(text);
                    }
                }
            }
        }
        for exc in &self.exceptions {
            total += count_unverified(&exc.item)
                + count_unverified(&exc.status)
                + count_unverified(&exc.evidence_needed);
        }
        for src in &self.sources {
            total += count_unverified(&src.status) + count_unverified(&src.title);
        }
        total
    }
}

pub fn schema_json() -> &'static str {
    SCHEMA_JSON
}
