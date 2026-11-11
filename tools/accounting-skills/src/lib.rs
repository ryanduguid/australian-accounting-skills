// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! The coverage matrix in coverage.json, derived from the skills, validation cards and tests.
pub mod citations;
pub mod grader_audit;
pub mod last_changed;
mod passage_diff;
pub mod plugin_evals;
mod source_codec_rules;
mod source_content;
mod source_date_rules;
mod source_dates;
pub mod source_fetch_policy;
mod source_gb18030;
mod source_gb18030_rules;
mod source_html_rules;
mod source_multibyte;
mod source_multibyte_rules;
pub mod source_passages;
pub mod source_refresh;
mod source_urls;
pub mod statement_check;
mod strict_yaml;
pub mod sweep;
pub mod trial;
pub mod validation;
mod validation_data;
mod validation_text;
use serde::Serialize;
use serde_json::Value;
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    io::Write,
    path::{Component, Path, PathBuf},
};

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
const NOTE: &str = "Derived from the tree by the build-coverage command in tools/accounting-skills. Do not edit by hand. The native CI job and the coverage-matrix pre-commit hook rebuild this file and fail on any difference. The reviewed field is the earliest recorded human review date across the sources for a skill. The fetched field is the earliest of their last recorded retrieval-attempt dates. A retrieval is not a human review. The reviewed_count field is how many of the indexed sources carry a human review date. The confirmed_pass and confirmed_fail fields list the skill's cards with a human-confirmed verdict in validation/results whose rubric digest matches the card as it is now; confirmed_noncurrent_digest lists cards with a confirmed verdict whose rubric digest does not match the current card, whether or not the current card also has a verdict; the card's history is not checked. One card version confirmed both pass and fail is refused, as is a status other than prepared, observed or confirmed. Legacy records without a status are not counted.";
/// The per-skill table build-coverage writes beside coverage.json.
pub const VERIFICATION_PAGE: &str = "docs/skill-verification.md";

#[derive(Serialize)]
pub struct Sources {
    indexed: usize,
    exempt: bool,
    reviewed: String,
    reviewed_count: usize,
    fetched: String,
    unreachable: usize,
    moved_since_review: Vec<String>,
}
#[derive(Serialize)]
pub struct Validation {
    cases: usize,
    case_ids: Vec<String>,
    only_seeded_case: bool,
    confirmed_pass: Vec<String>,
    confirmed_fail: Vec<String>,
    confirmed_noncurrent_digest: Vec<String>,
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
    skills_with_confirmed_pass: usize,
    skills_with_confirmed_fail: usize,
    skills_with_confirmed_noncurrent_digest: usize,
    sources_reviewed: usize,
}
#[derive(Serialize)]
pub struct Matrix {
    schema_version: u8,
    note: &'static str,
    totals: Totals,
    skills: Vec<Row>,
    /// Each legacy record's file name and the cards it records as failed.
    /// The page names them; coverage.json does not carry them.
    #[serde(skip)]
    legacy: Vec<(String, Vec<String>)>,
}

/// Replace `path` with `text` without writing through a link. A symlink or
/// other non-file at `path` is refused, and the bytes are renamed over the
/// entry, so a file hard-linked to it elsewhere keeps its contents.
pub fn replace_file(path: &Path, text: &str) -> Result<()> {
    if fs::symlink_metadata(path).is_ok_and(|metadata| !metadata.file_type().is_file()) {
        return Err(format!("{} must be a regular file", name(path)?).into());
    }
    let mut temporary = path.as_os_str().to_owned();
    temporary.push(format!(".{}.tmp", std::process::id()));
    let temporary = PathBuf::from(temporary);
    let written = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temporary)
        .and_then(|mut file| file.write_all(text.as_bytes()))
        .and_then(|()| fs::rename(&temporary, path));
    if written.is_err() {
        let _ = fs::remove_file(&temporary);
    }
    Ok(written?)
}

/// Run git in `root` and return its trimmed standard output, failing when git does.
pub(crate) fn git(root: &Path, args: &[&str]) -> Result<String> {
    let output = std::process::Command::new("git")
        .args(args)
        .current_dir(root)
        .output()?;
    if !output.status.success() {
        return Err(format!("git {} failed", args.join(" ")).into());
    }
    Ok(String::from_utf8(output.stdout)?.trim().to_string())
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

const OUTSIDE_ROOT: &str = "path escapes the repository root";

/// Canonicalise `path` for use as a repository root.
///
/// An existing path is canonicalised before anything is read or written, so a
/// link in its spelling cannot point the root somewhere else. A path that does
/// not exist yet is made absolute, and refused when its spelling contains `..`,
/// so a missing root is not created by climbing out of its parent.
pub fn canonical_root(path: &Path) -> Result<PathBuf> {
    match fs::canonicalize(path) {
        Ok(path) => Ok(path),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            let text = path.to_str().ok_or("repository root is not Unicode")?;
            if text.contains("..") {
                return Err(OUTSIDE_ROOT.into());
            }
            let absolute = std::path::absolute(text)?;
            if absolute
                .components()
                .any(|part| matches!(part, Component::ParentDir))
            {
                return Err(OUTSIDE_ROOT.into());
            }
            Ok(absolute)
        }
        Err(error) => Err(error.into()),
    }
}

/// Resolve `relative` inside `root` and refuse a path that leaves it.
///
/// `relative` may contain only normal components. Each existing component is
/// canonicalised and must stay inside the canonical root, so a symbolic link
/// cannot point the path elsewhere. A component that does not exist yet is
/// kept, so a new output can be confined before it is created. A final path
/// whose canonical target is a different file is refused, so a linked output
/// is not replaced with the link's target.
pub fn within_root(root: &Path, relative: &Path) -> Result<PathBuf> {
    let root = canonical_root(root)?;
    if relative.as_os_str().is_empty()
        || relative
            .components()
            .any(|part| !matches!(part, Component::Normal(_)))
    {
        return Err(OUTSIDE_ROOT.into());
    }
    let mut resolved = root.clone();
    let parts: Vec<_> = relative.components().collect();
    let mut index = 0;
    while index < parts.len() {
        let Component::Normal(name) = parts[index] else {
            return Err(OUTSIDE_ROOT.into());
        };
        let next = resolved.join(name);
        match fs::canonicalize(&next) {
            Ok(target) => {
                if !target.starts_with(&root) {
                    return Err(OUTSIDE_ROOT.into());
                }
                let last = index + 1 == parts.len();
                if last && target != next {
                    return Err(format!("{} must be a regular file", name.to_string_lossy()).into());
                }
                resolved = target;
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                return append_missing(&root, next, &parts[index + 1..]);
            }
            Err(error) => return Err(error.into()),
        }
        if !resolved.starts_with(&root) {
            return Err(OUTSIDE_ROOT.into());
        }
        index += 1;
    }
    if !resolved.starts_with(&root) {
        return Err(OUTSIDE_ROOT.into());
    }
    Ok(resolved)
}

/// Keep the remaining components of a path that does not exist yet.
fn append_missing(root: &Path, mut resolved: PathBuf, rest: &[Component<'_>]) -> Result<PathBuf> {
    for part in rest {
        resolved.push(part.as_os_str());
        if !resolved.starts_with(root) {
            return Err(OUTSIDE_ROOT.into());
        }
    }
    Ok(resolved)
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
    let root = canonical_root(root)?;
    if !normal_component(skill) {
        return Err(format!("skill path escapes the repository root: {skill}").into());
    }
    let directory = root.join(".claude").join("skills").join(skill);
    if !directory.starts_with(&root) {
        return Err(OUTSIDE_ROOT.into());
    }
    let mut summary = Sources {
        indexed: 0,
        exempt: existing_file(&root, &directory.join("sources.exempt.json"))?,
        reviewed: String::new(),
        reviewed_count: 0,
        fetched: String::new(),
        unreachable: 0,
        moved_since_review: Vec::new(),
    };
    let index = match fs::canonicalize(directory.join("sources.json")) {
        Ok(path) => {
            if !path.starts_with(&root) {
                return Err(OUTSIDE_ROOT.into());
            }
            path
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(summary),
        Err(error) => return Err(error.into()),
    };
    let payload = validation::strict_json(&read_text(&index)?, &index.display().to_string())?;
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
    summary.reviewed_count = reviewed.len();
    summary.reviewed = reviewed.into_iter().next().unwrap_or_default();
    summary.fetched = fetched.into_iter().next().unwrap_or_default();
    Ok(summary)
}

/// Whether `path` is an existing file whose canonical location stays in `root`.
fn existing_file(root: &Path, path: &Path) -> Result<bool> {
    match fs::canonicalize(path) {
        Ok(canonical) => {
            if !canonical.starts_with(root) {
                return Err(OUTSIDE_ROOT.into());
            }
            Ok(canonical.is_file())
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(false),
        Err(error) => Err(error.into()),
    }
}

/// A card id is one normal path component, so it cannot name another directory.
fn normal_component(name: &str) -> bool {
    if name.contains('/') || name.contains('\\') {
        return false;
    }
    let path = Path::new(name);
    let mut components = path.components();
    match components.next() {
        Some(Component::Normal(part)) if components.next().is_none() => part == path.as_os_str(),
        _ => false,
    }
}

/// The bytes of `validation/cases/{card}.md`, after the path has been
/// canonicalised and confined to that directory.
fn card_bytes(root: &Path, card: &str) -> Result<Vec<u8>> {
    if !normal_component(card) {
        return Err(format!("card path escapes validation/cases: {card}").into());
    }
    let root = canonical_root(root)?;
    let cases = root.join("validation").join("cases");
    if !cases.starts_with(&root) {
        return Err(OUTSIDE_ROOT.into());
    }
    let cases = fs::canonicalize(&cases)?;
    if !cases.starts_with(&root) {
        return Err(OUTSIDE_ROOT.into());
    }
    let path = fs::canonicalize(cases.join(format!("{card}.md")))?;
    if !path.starts_with(&cases) {
        return Err(format!("card path escapes validation/cases: {card}").into());
    }
    Ok(fs::read(path)?)
}

/// Human-confirmed verdicts, sorted by whether they judged the card as it is now.
#[derive(Default)]
struct Verdicts {
    passed: BTreeSet<String>,
    failed: BTreeSet<String>,
    noncurrent_digest: BTreeSet<String>,
    legacy: Vec<(String, Vec<String>)>,
}

/// Reads validation/results. Version 2 records whose status is confirmed
/// count when their rubric digest matches the current card bytes, and are
/// listed apart otherwise, even when the current card has its own verdict.
/// A non-matching digest is not checked against the card's history: the
/// native CI job checks out one commit, so the list claims only that the
/// digest differs. Legacy records state no status: they are kept for the
/// page's legend only. Prepared and observed records carry no counted verdict,
/// and any other status is refused. One card version confirmed both pass and
/// fail is refused, because no rule yet says which verdict supersedes the other.
fn confirmed_verdicts(root: &Path, known: &BTreeSet<&String>) -> Result<Verdicts> {
    let mut verdicts = Verdicts::default();
    let mut seen: BTreeMap<(String, String), (String, String)> = BTreeMap::new();
    for path in entries(&root.join("validation/results"))? {
        if !matches_suffix(&path, ".json")? {
            continue;
        }
        let record: Value = serde_json::from_str(&read_text(&path)?)?;
        let file = name(&path)?;
        let results = record
            .get("results")
            .and_then(Value::as_object)
            .ok_or_else(|| format!("{file}: results must be an object"))?;
        let mut stated = Vec::new();
        for (card, verdict) in results {
            match verdict.as_str() {
                Some(verdict @ ("pass" | "fail")) => stated.push((card, verdict)),
                _ => return Err(format!("{file}: {card} must be pass or fail").into()),
            }
        }
        match record.get("status").map(Value::as_str) {
            None => {
                let fails = stated.iter().filter(|(_, verdict)| *verdict == "fail");
                verdicts
                    .legacy
                    .push((file, fails.map(|(card, _)| (*card).clone()).collect()));
                continue;
            }
            Some(Some("confirmed")) => {}
            Some(Some("prepared" | "observed")) => continue,
            Some(_) => {
                return Err(
                    format!("{file}: status must be prepared, observed or confirmed").into(),
                );
            }
        }
        for (card, verdict) in stated {
            if !known.contains(card) {
                return Err(format!("{file}: {card} is not a card any skill targets").into());
            }
            let recorded = record
                .get("provenance")
                .and_then(|provenance| provenance.get(card))
                .and_then(|entry| entry.get("rubric_sha256"))
                .and_then(Value::as_str)
                .filter(|digest| {
                    digest.len() == 64
                        && digest
                            .bytes()
                            .all(|byte| matches!(byte, b'0'..=b'9' | b'a'..=b'f'))
                })
                .ok_or_else(|| {
                    format!("{file}: {card} needs a rubric_sha256 of 64 lower-case hex digits")
                })?;
            // Verdicts under different recorded digests are kept apart, so only
            // one card and digest confirmed both ways is a conflict.
            let version = (card.clone(), recorded.to_owned());
            if let Some((other, earlier)) = seen.get(&version)
                && other != verdict
            {
                return Err(format!(
                    "{card} is confirmed {other} in {earlier} and {verdict} in {file} on the \
                     same card version; record which verdict stands before it can be counted"
                )
                .into());
            }
            seen.insert(version, (verdict.to_owned(), file.clone()));
            let current = trial::digest(&card_bytes(root, card)?);
            let list = if recorded != current {
                &mut verdicts.noncurrent_digest
            } else if verdict == "pass" {
                &mut verdicts.passed
            } else {
                &mut verdicts.failed
            };
            list.insert(card.clone());
        }
    }
    Ok(verdicts)
}

pub fn build(root: &Path) -> Result<Matrix> {
    let skills = discover_skills(root)?;
    let mut cards = case_targets(root)?;
    let known: BTreeSet<&String> = cards.values().flatten().collect();
    let verdicts = confirmed_verdicts(root, &known)?;
    let mut mentions: BTreeMap<String, Vec<String>> = skills
        .iter()
        .map(|skill| (skill.clone(), Vec::new()))
        .collect();
    for path in entries(&root.join("tests"))? {
        if matches_suffix(&path, ".py")? {
            let text = read_text(&path)?;
            for skill in &skills {
                // Every opening quote is a candidate, as in Python's regex
                // search; occurrences of the name itself can overlap.
                if text.match_indices(['\'', '"']).any(|(offset, quote)| {
                    text[offset + quote.len()..]
                        .strip_prefix(skill.as_str())
                        .is_some_and(|rest| rest.starts_with(['\'', '"']))
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
        let confirmed = |verdicts: &BTreeSet<String>| {
            case_ids
                .iter()
                .filter(|card| verdicts.contains(*card))
                .cloned()
                .collect::<Vec<_>>()
        };
        let confirmed_pass = confirmed(&verdicts.passed);
        let confirmed_fail = confirmed(&verdicts.failed);
        let confirmed_noncurrent_digest = confirmed(&verdicts.noncurrent_digest);
        let behavioural = mentions.remove(&skill).unwrap();
        totals.sources_indexed += sources.indexed;
        totals.skills_source_exempt += usize::from(sources.exempt);
        totals.skills_with_unreachable_sources += usize::from(sources.unreachable != 0);
        totals.skills_with_sources_moved_since_review +=
            usize::from(!sources.moved_since_review.is_empty());
        totals.skills_with_behavioural_gate += usize::from(!behavioural.is_empty());
        totals.skills_with_only_the_seeded_case += usize::from(only_seeded_case);
        totals.skills_with_confirmed_pass += usize::from(!confirmed_pass.is_empty());
        totals.skills_with_confirmed_fail += usize::from(!confirmed_fail.is_empty());
        totals.skills_with_confirmed_noncurrent_digest +=
            usize::from(!confirmed_noncurrent_digest.is_empty());
        totals.sources_reviewed += sources.reviewed_count;
        rows.push(Row {
            skill,
            sources,
            validation: Validation {
                cases: case_ids.len(),
                case_ids,
                only_seeded_case,
                confirmed_pass,
                confirmed_fail,
                confirmed_noncurrent_digest,
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
        legacy: verdicts.legacy,
    })
}

pub fn rendered(root: &Path) -> Result<String> {
    Ok(serde_json::to_string_pretty(&build(root)?)? + "\n")
}

/// The coverage matrix and its verification page, from one build.
pub fn rendered_with_page(root: &Path) -> Result<(String, String)> {
    let matrix = build(root)?;
    Ok((
        serde_json::to_string_pretty(&matrix)? + "\n",
        verification_page(&matrix),
    ))
}

/// One row per skill from the same matrix as coverage.json, so the page
/// cannot drift from it whilst build-coverage --check passes.
pub fn verification_page(matrix: &Matrix) -> String {
    let totals = &matrix.totals;
    let mut text = format!(
        "# How each skill was verified\n\n\
         Generated from [coverage.json](../coverage.json) by \
         `accounting-skills build-coverage --write`. Its `--check` mode fails when this page \
         disagrees with the tree.\n\n\
         Totals: {} skills, {} indexed primary sources of which {} have a recorded human \
         review, {} skills exempt from source indexing, {} skills with an unreachable source, \
         {} skills with a source changed since review, {} skills with a confirmed pass, \
         {} skills with a confirmed fail and {} skills with a confirmed verdict whose rubric \
         digest does not match the current card.\n\n\
         - **Sources**: primary sources in the skill's `sources.json`, or 'exempt' for a skill \
         with a recorded exemption.\n\
         - **Earliest review**: the oldest date on which a person recorded reading one of \
         those sources, then how many of them carry a review date at all. A source with no \
         review date has not been reviewed. A fetch is not a review.\n\
         - **Unreachable**: sources whose last fetch did not return HTTP 200 and that have no \
         manual review record.\n\
         - **Changed since review**: sources that published a change after their last \
         review.\n\
         - **Cards**: fabricated [validation cards](../validation/README.md) that target the \
         skill. It is a count of cards, not of runs.\n\
         - **Confirmed pass** and **Confirmed fail**: those cards with a human-confirmed \
         verdict in [validation/results](../validation/results/) whose recorded rubric digest \
         matches the card as it is now. A pass shows that a model passed the card's rubric on \
         one run, not that the skill's content is correct.\n\
         - **Non-current digest**: cards with a human-confirmed verdict whose recorded rubric \
         digest does not match the card as it is now. The build does not check the card's \
         history, so this says only that the digests differ. Such a verdict does not count as \
         a pass or fail; a verdict that matches the current card, if there is one, is counted \
         in its own column.\n",
        totals.skills,
        totals.sources_indexed,
        totals.sources_reviewed,
        totals.skills_source_exempt,
        totals.skills_with_unreachable_sources,
        totals.skills_with_sources_moved_since_review,
        totals.skills_with_confirmed_pass,
        totals.skills_with_confirmed_fail,
        totals.skills_with_confirmed_noncurrent_digest,
    );
    if !matrix.legacy.is_empty() {
        let files: Vec<String> = matrix
            .legacy
            .iter()
            .map(|(file, _)| format!("`{file}`"))
            .collect();
        let fails: Vec<String> = matrix
            .legacy
            .iter()
            .flat_map(|(file, cards)| cards.iter().map(move |card| format!("`{card}` (`{file}`)")))
            .collect();
        let held = if fails.is_empty() {
            "They record no fail.".to_owned()
        } else {
            format!("They record a fail for {}.", listed(&fails))
        };
        text.push_str(&format!(
            "- **Legacy records**: {} predate the confirmed status and state no input mode, so \
             the columns leave them out. {held}\n",
            listed(&files)
        ));
    }
    text.push_str(
        "\n| Skill | Sources | Earliest review | Unreachable | Changed since review | Cards \
         | Confirmed pass | Confirmed fail | Non-current digest |\n\
         | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
    );
    for row in &matrix.skills {
        let skill = &row.skill;
        let sources = &row.sources;
        let indexed = if sources.indexed > 0 {
            format!(
                "[{}](../.claude/skills/{skill}/sources.json)",
                sources.indexed
            )
        } else if sources.exempt {
            "exempt".to_owned()
        } else {
            "0".to_owned()
        };
        let date = if sources.reviewed.is_empty() {
            "none"
        } else {
            &sources.reviewed
        };
        let reviewed = if sources.indexed > 0 {
            format!("{date} ({} of {})", sources.reviewed_count, sources.indexed)
        } else {
            date.to_owned()
        };
        text.push_str(&format!(
            "| [`{skill}`](../.claude/skills/{skill}/SKILL.md) | {indexed} | {reviewed} | {} | {} \
             | {} | {} | {} | {} |\n",
            sources.unreachable,
            sources.moved_since_review.len(),
            row.validation.cases,
            row.validation.confirmed_pass.len(),
            row.validation.confirmed_fail.len(),
            row.validation.confirmed_noncurrent_digest.len(),
        ));
    }
    text
}

/// `a`, `a and b` or `a, b and c`.
fn listed(items: &[String]) -> String {
    match items {
        [] => String::new(),
        [only] => only.clone(),
        [rest @ .., last] => format!("{} and {last}", rest.join(", ")),
    }
}

pub fn platform_text(text: &str) -> String {
    if cfg!(windows) {
        text.replace('\n', "\r\n")
    } else {
        text.to_owned()
    }
}
