//! Coverage inventory derived from the same tree as scripts/build_coverage.py.
mod passage_diff;
mod source_codec_rules;
mod source_content;
mod source_date_rules;
mod source_dates;
pub mod source_fetch_policy;
mod source_html_rules;
pub mod source_passages;
pub mod source_refresh;
mod source_urls;
mod strict_yaml;
pub mod sweep;
pub mod trial;
pub mod validation;
mod validation_data;
mod validation_text;
use serde::Serialize;
use serde_json::Value;
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
};

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
const NOTE: &str = "Derived from the tree by scripts/build_coverage.py. Do not edit by hand. tests/test_coverage_matrix.py rebuilds this file and fails on any difference. The reviewed field is the earliest recorded human review date across the sources for a skill. The fetched field is the earliest of their last recorded retrieval-attempt dates. A retrieval is not a human review.";

#[derive(Serialize)]
pub struct Sources {
    indexed: usize,
    exempt: bool,
    reviewed: String,
    fetched: String,
    unreachable: usize,
    moved_since_review: Vec<String>,
}
#[derive(Serialize)]
pub struct Validation {
    cases: usize,
    case_ids: Vec<String>,
    only_seeded_case: bool,
}
#[derive(Serialize)]
pub struct Gates {
    behavioural: Vec<String>,
    inventory: Vec<String>,
}
#[derive(Serialize)]
pub struct Row {
    skill: String,
    sources: Sources,
    validation: Validation,
    gates: Gates,
}
#[derive(Serialize, Default)]
pub struct Totals {
    skills: usize,
    sources_indexed: usize,
    skills_source_exempt: usize,
    skills_with_unreachable_sources: usize,
    skills_with_sources_moved_since_review: usize,
    skills_with_behavioural_gate: usize,
    skills_with_only_the_seeded_case: usize,
}
#[derive(Serialize)]
pub struct Matrix {
    schema_version: u8,
    note: &'static str,
    totals: Totals,
    skills: Vec<Row>,
}

pub fn read_text(path: &Path) -> Result<String> {
    Ok(fs::read_to_string(path)?
        .replace("\r\n", "\n")
        .replace('\r', "\n"))
}

fn entries(path: &Path) -> Result<Vec<PathBuf>> {
    if !path.is_dir() {
        return Ok(Vec::new());
    }
    let mut paths = fs::read_dir(path)?
        .map(|entry| entry.map(|entry| entry.path()))
        .collect::<std::io::Result<Vec<_>>>()?;
    // pathlib orders Windows siblings without case distinctions.
    paths.sort_by_key(|path| {
        let name = path.file_name().unwrap().to_string_lossy().into_owned();
        if cfg!(windows) {
            name.to_lowercase()
        } else {
            name
        }
    });
    Ok(paths)
}

fn name(path: &Path) -> Result<String> {
    Ok(path
        .file_name()
        .and_then(|s| s.to_str())
        .ok_or("filename is not Unicode")?
        .to_owned())
}

fn matches_suffix(path: &Path, suffix: &str) -> Result<bool> {
    let name = name(path)?;
    Ok(if cfg!(windows) {
        name.to_lowercase().ends_with(suffix)
    } else {
        name.ends_with(suffix)
    })
}

fn splitlines(text: &str) -> Vec<&str> {
    let mut lines = Vec::new();
    let mut start = 0;
    let mut chars = text.char_indices().peekable();
    while let Some((position, c)) = chars.next() {
        if matches!(
            c,
            '\n' | '\r' | '\u{b}' | '\u{c}' | '\u{1c}'
                ..='\u{1e}' | '\u{85}' | '\u{2028}' | '\u{2029}'
        ) {
            lines.push(&text[start..position]);
            start = position + c.len_utf8();
            if c == '\r' && chars.peek().is_some_and(|(_, c)| *c == '\n') {
                start = chars.next().unwrap().0 + 1;
            }
        }
    }
    if start < text.len() {
        lines.push(&text[start..]);
    }
    lines
}

pub fn front_matter(path: &Path) -> Result<String> {
    let text = read_text(path)?;
    let lines = splitlines(&text);
    if lines.first() != Some(&"---") {
        return Err(format!("{}: front matter must start with '---'", name(path)?).into());
    }
    let end = lines
        .iter()
        .skip(1)
        .position(|line| *line == "---")
        .ok_or_else(|| {
            format!(
                "{}: front matter must end with '---'",
                name(path).unwrap_or_default()
            )
        })?
        + 1;
    Ok(lines[1..end].join("\n"))
}

pub fn discover_skills(root: &Path) -> Result<Vec<String>> {
    let mut skills = Vec::new();
    for directory in entries(&root.join(".claude/skills"))? {
        if directory.is_dir() && fs::symlink_metadata(directory.join("SKILL.md")).is_ok() {
            skills.push(name(&directory)?);
        }
    }
    skills.sort();
    Ok(skills)
}

pub fn case_targets(root: &Path) -> Result<BTreeMap<String, Vec<String>>> {
    // Python \s also includes the ASCII information separators.
    let space = r"[\s\x1c-\x1f]";
    let pattern = fancy_regex::Regex::new(&format!(
        r"(?m)^{space}*-{space}*([a-z0-9][a-z0-9-]*){space}*$"
    ))?;
    let mut targets: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for path in entries(&root.join("validation/cases"))? {
        if matches_suffix(&path, ".md")? {
            let stem = path
                .file_stem()
                .and_then(|s| s.to_str())
                .ok_or("filename is not Unicode")?;
            for capture in pattern.captures_iter(&front_matter(&path)?) {
                targets
                    .entry(capture?.get(1).unwrap().as_str().to_owned())
                    .or_default()
                    .push(stem.to_owned());
            }
        }
    }
    for cards in targets.values_mut() {
        cards.sort();
        cards.dedup();
    }
    Ok(targets)
}

fn truthy(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(value) => *value,
        Value::Number(number) => number.as_f64() != Some(0.0),
        Value::String(text) => !text.is_empty(),
        Value::Array(values) => !values.is_empty(),
        Value::Object(values) => !values.is_empty(),
    }
}

// Date and URL fields are strings in the source schema. Refuse other types
// instead of manufacturing provenance text from malformed records.
fn text_field(record: &serde_json::Map<String, Value>, field: &str) -> Result<String> {
    match record.get(field) {
        None => Ok(String::new()),
        Some(Value::String(text)) => Ok(text.clone()),
        _ => Err(format!("source field {field} must be a string").into()),
    }
}

pub fn source_evidence(root: &Path, skill: &str) -> Result<Sources> {
    let directory = root.join(".claude/skills").join(skill);
    let mut summary = Sources {
        indexed: 0,
        exempt: directory.join("sources.exempt.json").is_file(),
        reviewed: String::new(),
        fetched: String::new(),
        unreachable: 0,
        moved_since_review: Vec::new(),
    };
    let index = directory.join("sources.json");
    if !index.is_file() {
        return Ok(summary);
    }
    let payload: Value = serde_json::from_str(&read_text(&index)?)?;
    let object = payload
        .as_object()
        .ok_or("source index must be an object")?;
    let empty = Vec::new();
    let records = match object.get("sources") {
        None => &empty,
        Some(Value::Array(records)) => records,
        _ => return Err("sources must be an array".into()),
    };
    let mut reviewed = Vec::new();
    let mut fetched = Vec::new();
    for record in records.iter().filter_map(Value::as_object) {
        summary.indexed += 1;
        let checked = text_field(record, "checked_at")?;
        let retrieved = text_field(record, "fetched_at")?;
        let modified = text_field(record, "source_last_modified")?;
        if !checked.is_empty() {
            reviewed.push(checked.clone());
        }
        if !retrieved.is_empty() {
            fetched.push(retrieved);
        }
        let status = record.get("http_status");
        if status.is_some_and(|value| !value.is_null() && value.as_f64() != Some(200.0))
            && !record.get("manual_review").is_some_and(Value::is_object)
        {
            summary.unreachable += 1;
        }
        if record.get("source_last_modified").is_some_and(truthy) && modified > checked {
            summary.moved_since_review.push(text_field(record, "url")?);
        }
    }
    reviewed.sort();
    fetched.sort();
    summary.moved_since_review.sort();
    summary.reviewed = reviewed.into_iter().next().unwrap_or_default();
    summary.fetched = fetched.into_iter().next().unwrap_or_default();
    Ok(summary)
}

pub fn build(root: &Path) -> Result<Matrix> {
    let skills = discover_skills(root)?;
    let mut cards = case_targets(root)?;
    let mut mentions: BTreeMap<String, Vec<String>> = skills
        .iter()
        .map(|skill| (skill.clone(), Vec::new()))
        .collect();
    for path in entries(&root.join("tests"))? {
        if matches_suffix(&path, ".py")? {
            let text = read_text(&path)?;
            for skill in &skills {
                if text.match_indices(skill).any(|(offset, _)| {
                    matches!(text[..offset].chars().next_back(), Some('\'' | '"'))
                        && matches!(
                            text[offset + skill.len()..].chars().next(),
                            Some('\'' | '"')
                        )
                }) {
                    mentions.get_mut(skill).unwrap().push(name(&path)?);
                }
            }
        }
    }
    let mut rows = Vec::new();
    let mut totals = Totals {
        skills: skills.len(),
        ..Default::default()
    };
    for skill in skills {
        let sources = source_evidence(root, &skill)?;
        let case_ids = cards.remove(&skill).unwrap_or_default();
        let only_seeded_case = case_ids == [format!("{skill}-missing-evidence")];
        let behavioural = mentions.remove(&skill).unwrap();
        totals.sources_indexed += sources.indexed;
        totals.skills_source_exempt += usize::from(sources.exempt);
        totals.skills_with_unreachable_sources += usize::from(sources.unreachable != 0);
        totals.skills_with_sources_moved_since_review +=
            usize::from(!sources.moved_since_review.is_empty());
        totals.skills_with_behavioural_gate += usize::from(!behavioural.is_empty());
        totals.skills_with_only_the_seeded_case += usize::from(only_seeded_case);
        rows.push(Row {
            skill,
            sources,
            validation: Validation {
                cases: case_ids.len(),
                case_ids,
                only_seeded_case,
            },
            gates: Gates {
                behavioural,
                inventory: Vec::new(),
            },
        });
    }
    Ok(Matrix {
        schema_version: 1,
        note: NOTE,
        totals,
        skills: rows,
    })
}

pub fn rendered(root: &Path) -> Result<String> {
    Ok(serde_json::to_string_pretty(&build(root)?)? + "\n")
}

pub fn platform_text(text: &str) -> String {
    if cfg!(windows) {
        text.replace('\n', "\r\n")
    } else {
        text.to_owned()
    }
}
