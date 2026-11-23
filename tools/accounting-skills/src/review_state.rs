// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! `review-state write|verify CASE_DIR`: a review's check register, bound by
//! SHA-256 to the draft it reviewed and to every file under the case's
//! `sources/` folder. `write` records the register a review skill built;
//! `verify` exits 0 only while that review passed and nothing it read has
//! changed, and otherwise prints the first reason. A check not performed never
//! reads as passed, and nothing the user says changes the result.
use crate::{
    Result, canonical_root, platform_text, replace_file, source_content::sha256, within_root,
};
use serde::{Deserialize, Serialize};
use std::{
    ffi::OsString,
    fs,
    io::{self, Write},
    path::{Path, PathBuf},
};

/// The state file, at the case folder's top level.
pub const STATE_FILE: &str = "review-state.json";
const SOURCES: &str = "sources";
const SCHEMA_VERSION: u32 = 1;
const STATUSES: [&str; 4] = ["passed", "failed", "not performed", "not applicable"];
const USAGE: &str = "usage: accounting-skills review-state write CASE_DIR --draft RELATIVE_PATH --register REGISTER.json\n       accounting-skills review-state verify CASE_DIR [--state-sha256 HEX]";

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub struct Check {
    pub check: String,
    pub status: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub note: String,
}

#[derive(Serialize, Deserialize, Debug, PartialEq, Eq)]
pub struct Digest {
    pub path: String,
    pub sha256: String,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(deny_unknown_fields)]
pub struct State {
    pub schema_version: u32,
    pub written_on: String,
    pub result: String,
    pub draft: Digest,
    pub sources: Vec<Digest>,
    pub checks: Vec<Check>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Register {
    checks: Vec<Check>,
}

/// Refuses an empty register, a repeated or blank check, an unknown status, and
/// a check not performed or not applicable without the note saying why.
pub fn validate(checks: &[Check]) -> Result<()> {
    if checks.is_empty() {
        return Err("the register lists no checks".into());
    }
    let mut seen = std::collections::BTreeSet::new();
    for check in checks {
        let name = check.check.trim();
        if name.is_empty() || !seen.insert(name.to_owned()) {
            return Err(format!("check {name:?} is blank or repeated").into());
        }
        if !STATUSES.contains(&check.status.as_str()) {
            return Err(format!(
                "check {name:?} has status {:?}, not one of {STATUSES:?}",
                check.status
            )
            .into());
        }
        let explained = !check.note.trim().is_empty();
        if matches!(check.status.as_str(), "not performed" | "not applicable") && !explained {
            return Err(format!(
                "check {name:?} is {} without a note saying why",
                check.status
            )
            .into());
        }
    }
    Ok(())
}

/// `passed` only when no check failed and none was left unperformed.
pub fn result(checks: &[Check]) -> &'static str {
    if checks.iter().any(|check| check.status == "failed") {
        "failed"
    } else if checks.iter().any(|check| check.status == "not performed") {
        "incomplete"
    } else {
        "passed"
    }
}

fn walk(folder: &Path, relative: &str, found: &mut Vec<Digest>) -> Result<()> {
    let mut entries = fs::read_dir(folder)?.collect::<io::Result<Vec<_>>>()?;
    entries.sort_by_key(fs::DirEntry::file_name);
    for entry in entries {
        let name = entry
            .file_name()
            .into_string()
            .map_err(|_| "a source file name is not Unicode")?;
        let path = format!("{relative}/{name}");
        let kind = entry.file_type()?;
        if kind.is_dir() {
            walk(&entry.path(), &path, found)?;
        } else if kind.is_file() {
            found.push(Digest {
                sha256: sha256(&fs::read(entry.path())?),
                path,
            });
        } else {
            return Err(format!("{path} is not a regular file or folder").into());
        }
    }
    Ok(())
}

/// Every regular file under the case's `sources/` folder, by `/` path, sorted.
pub fn source_digests(case: &Path) -> Result<Vec<Digest>> {
    let folder = case.join(SOURCES);
    let mut found = Vec::new();
    match fs::symlink_metadata(&folder) {
        Ok(metadata) if metadata.is_dir() => walk(&folder, SOURCES, &mut found)?,
        Ok(_) => return Err(format!("{SOURCES} is not a folder").into()),
        Err(error) if error.kind() == io::ErrorKind::NotFound => {}
        Err(error) => return Err(error.into()),
    }
    found.sort_by(|a, b| a.path.cmp(&b.path));
    Ok(found)
}

fn draft_digest(case: &Path, relative: &str) -> Result<Digest> {
    let path = within_root(case, Path::new(relative))?;
    let top = relative.split(['/', '\\']).next().unwrap_or_default();
    if top == SOURCES || relative == STATE_FILE {
        return Err(format!("the draft cannot be {STATE_FILE} or inside {SOURCES}/").into());
    }
    if !fs::symlink_metadata(&path)?.is_file() {
        return Err(format!("draft {relative} is not a regular file").into());
    }
    Ok(Digest {
        path: relative.replace('\\', "/"),
        sha256: sha256(&fs::read(&path)?),
    })
}

/// Writes the state for `checks`; returns it with the SHA-256 of the file written,
/// which the reviewer records so `verify` can refuse a state rewritten later.
pub fn write(case: &Path, draft: &str, checks: Vec<Check>, today: &str) -> Result<(State, String)> {
    validate(&checks)?;
    let case = canonical_root(case)?;
    let state = State {
        schema_version: SCHEMA_VERSION,
        written_on: today.to_owned(),
        result: result(&checks).to_owned(),
        draft: draft_digest(&case, draft)?,
        sources: source_digests(&case)?,
        checks,
    };
    let text = serde_json::to_string_pretty(&state)? + "\n";
    replace_file(&case.join(STATE_FILE), &text)?;
    Ok((state, sha256(text.as_bytes())))
}

/// The first change between the reviewed sources and the current ones.
fn source_change(reviewed: &[Digest], current: &[Digest]) -> Option<String> {
    for digest in reviewed {
        match current.iter().find(|now| now.path == digest.path) {
            None => {
                return Some(format!(
                    "source {} was removed since the review",
                    digest.path
                ));
            }
            Some(now) if now.sha256 != digest.sha256 => {
                return Some(format!("source {} changed since the review", digest.path));
            }
            Some(_) => {}
        }
    }
    let added = current
        .iter()
        .find(|now| reviewed.iter().all(|digest| digest.path != now.path));
    added.map(|now| format!("source {} was added since the review", now.path))
}

/// `Ok(None)` while the review passed and is current; otherwise the first reason it
/// cannot be relied on. The state file is not signed: only `recorded`, the digest
/// `write` printed and the reviewer kept, shows it was not rewritten since.
pub fn verify(case: &Path, recorded: Option<&str>) -> Result<Option<String>> {
    let case = canonical_root(case)?;
    let text = match fs::read_to_string(case.join(STATE_FILE)) {
        Ok(text) => text,
        Err(error) if error.kind() == io::ErrorKind::NotFound => {
            return Ok(Some(format!(
                "no {STATE_FILE}: no review has been recorded"
            )));
        }
        Err(error) => return Err(error.into()),
    };
    if recorded.is_some_and(|digest| !digest.eq_ignore_ascii_case(&sha256(text.as_bytes()))) {
        return Ok(Some(format!(
            "{STATE_FILE} is not the file whose SHA-256 was recorded at the review"
        )));
    }
    let state: State = serde_json::from_str(&text)
        .map_err(|error| format!("{STATE_FILE} is unreadable: {error}"))?;
    if state.schema_version != SCHEMA_VERSION {
        return Err(format!(
            "{STATE_FILE} has schema version {}, not {SCHEMA_VERSION}",
            state.schema_version
        )
        .into());
    }
    validate(&state.checks)?;
    if result(&state.checks) != "passed" || state.result != "passed" {
        let open = state
            .checks
            .iter()
            .find(|check| matches!(check.status.as_str(), "failed" | "not performed"));
        let named = open.map_or_else(String::new, |check| {
            format!(": {} {}", check.check, check.status)
        });
        return Ok(Some(format!("the review did not pass{named}")));
    }
    match draft_digest(&case, &state.draft.path) {
        Ok(now) if now.sha256 == state.draft.sha256 => {}
        Ok(_) => {
            return Ok(Some(format!(
                "draft {} changed since the review",
                state.draft.path
            )));
        }
        Err(_) => return Ok(Some(format!("draft {} is missing", state.draft.path))),
    }
    Ok(source_change(&state.sources, &source_digests(&case)?))
}

fn option(args: &mut impl Iterator<Item = OsString>, name: &str) -> Result<String> {
    args.next()
        .and_then(|value| value.into_string().ok())
        .filter(|value| !value.is_empty() && !value.starts_with('-'))
        .ok_or_else(|| format!("{name} requires a value").into())
}

fn write_cli(case: &Path, mut args: impl Iterator<Item = OsString>) -> Result<u8> {
    let (mut draft, mut register) = (None, None);
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--draft") => draft = Some(option(&mut args, "--draft")?),
            Some("--register") => register = Some(PathBuf::from(option(&mut args, "--register")?)),
            _ => return Err(USAGE.into()),
        }
    }
    let (Some(draft), Some(register)) = (draft, register) else {
        return Err(USAGE.into());
    };
    let register: Register = serde_json::from_str(&fs::read_to_string(register)?)
        .map_err(|error| format!("the register is unreadable: {error}"))?;
    let today = jiff::ZonedDateTime::now()
        .date()
        .strftime("%Y-%m-%d")
        .to_string();
    let (state, digest) = write(case, &draft, register.checks, &today)?;
    let line = format!(
        "wrote {STATE_FILE}: review {}, {} checks, {} sources; record its SHA-256 {digest}\n",
        state.result,
        state.checks.len(),
        state.sources.len()
    );
    io::stdout().write_all(platform_text(&line).as_bytes())?;
    Ok(0)
}

pub fn cli(mut args: impl Iterator<Item = OsString>) -> Result<u8> {
    let command = args.next();
    let case = PathBuf::from(args.next().ok_or(USAGE)?);
    match command.as_deref().and_then(std::ffi::OsStr::to_str) {
        Some("write") => write_cli(&case, args),
        Some("verify") => {
            let recorded = match (args.next(), args.next(), args.next()) {
                (None, None, None) => None,
                (Some(flag), Some(value), None) if flag == "--state-sha256" => {
                    Some(value.into_string().map_err(|_| USAGE)?)
                }
                _ => return Err(USAGE.into()),
            };
            let (code, line) = match verify(&case, recorded.as_deref())? {
                None => (
                    0,
                    "review current: passed, and the draft and sources are unchanged\n".to_owned(),
                ),
                Some(reason) => (2, format!("STALE {reason}\n")),
            };
            io::stdout().write_all(platform_text(&line).as_bytes())?;
            Ok(code)
        }
        _ => Err(USAGE.into()),
    }
}
