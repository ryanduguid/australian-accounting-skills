//! Bounded indexed-source passages. Capturing and comparing never accepts a
//! source or establishes its legal, tax or accounting applicability.
use crate::{Result, passage_diff, source_fetch_policy::checked_url, source_refresh as refresh};
use serde_json::{Value, json};
use std::{
    ffi::OsString,
    fs,
    io::Write,
    path::{Path, PathBuf},
};

pub const MAX_TEXT_CHARS: usize = 32768;
pub const MAX_DIFF_LINES: usize = 60;
pub const MAX_LINE_CHARS: usize = 240;
pub const MAX_TEXT_LINES: usize = 400;
const SNAPSHOT_BOUNDARY: &str =
    "Bounded source text only; no verification of current applicability or human review.";
const COMPARISON_BOUNDARY: &str =
    "Text comparison only. A person must assess any legal, tax or accounting implication.";
const OUTPUT_ERROR: &str = "Choose a new output file outside the repository.";

pub fn indexed_url(url: &str, skills: &Path) -> Result<String> {
    let target = checked_url(url)?;
    // Read the complete index, as Python's set comprehension does, rather than
    // returning early and overlooking a malformed later index.
    let mut found = false;
    for path in refresh::index_files(skills)? {
        let payload = refresh::load_index(&path, skills)?;
        let object = payload
            .as_object()
            .ok_or("Source index must be an object")?;
        if let Some(records) = object.get("sources").and_then(Value::as_array) {
            for record in records.iter().filter(|record| record.is_object()) {
                let value = record.get("url").ok_or("Source record has no URL")?;
                found |= refresh::defrag(&refresh::string(value)) == target;
            }
        }
    }
    if !found {
        return Err("Only exact URLs already present in the public index may be captured.".into());
    }
    Ok(target)
}

pub fn snapshot_with(
    url: &str,
    skills: &Path,
    mut fetch: impl FnMut(&str) -> Result<refresh::Fetched>,
) -> Result<Value> {
    let target = indexed_url(url, skills)?;
    let fetched = fetch(&target)?;
    Ok(json!({
        "url": target, "final_url": fetched.final_url, "http_status": fetched.status,
        "available": fetched.readable() && !fetched.text.is_empty(), "error": fetched.error,
        "source_digest": fetched.digest, "digest_kind": fetched.kind,
        "text": fetched.text, "text_truncated": fetched.text_truncated,
        "text_sha256": refresh::content_digest(&fetched.text), "boundary": SNAPSHOT_BOUNDARY
    }))
}

pub fn snapshot(url: &str, skills: &Path) -> Result<Value> {
    snapshot_with(url, skills, |url| Ok(refresh::fetch(url, true)))
}

pub fn load_snapshot(path: &Path, skills: &Path) -> Result<Value> {
    if fs::metadata(path)?.len() > 1024 * 1024 {
        return Err("Snapshot file exceeds 1 MiB.".into());
    }
    // Limit the actual read too, including files which grow after metadata.
    use std::io::Read;
    let mut bytes = Vec::new();
    fs::File::open(path)?
        .take(1024 * 1024 + 1)
        .read_to_end(&mut bytes)?;
    if bytes.len() > 1024 * 1024 {
        return Err("Snapshot file exceeds 1 MiB.".into());
    }
    let raw = String::from_utf8(bytes)?
        .replace("\r\n", "\n")
        .replace('\r', "\n");
    let value: Value = serde_json::from_str(&raw)?;
    let text = value
        .get("text")
        .and_then(Value::as_str)
        .filter(|_| value.is_object())
        .ok_or("Malformed passage snapshot.")?;
    if text.chars().count() > MAX_TEXT_CHARS
        || value.get("text_sha256").and_then(Value::as_str)
            != Some(refresh::content_digest(text).as_str())
    {
        return Err("Snapshot text is oversized or does not agree with its digest.".into());
    }
    let url = value
        .get("url")
        .and_then(Value::as_str)
        .ok_or("Malformed snapshot URL.")?;
    let final_url = value
        .get("final_url")
        .and_then(Value::as_str)
        .ok_or("Malformed snapshot URL.")?;
    indexed_url(url, skills)?;
    let digest = value.get("source_digest").and_then(Value::as_str);
    if !value.get("available").is_some_and(Value::is_boolean)
        || !value.get("text_truncated").is_some_and(Value::is_boolean)
        || digest.is_none()
        || (value["available"] == true
            && !digest.is_some_and(|s| {
                s.len() == 64
                    && s.bytes()
                        .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
            }))
    {
        return Err("Malformed snapshot availability or source digest.".into());
    }
    checked_url(final_url)?;
    Ok(value)
}

pub fn compare(before: &Value, after: &Value) -> Result<Value> {
    if before.get("url") != after.get("url")
        || !refresh::truth(&before["available"])
        || !refresh::truth(&after["available"])
    {
        return Ok(
            json!({"status":"unavailable", "reason":"Both readable snapshots of the same indexed URL are required.", "boundary":COMPARISON_BOUNDARY}),
        );
    }
    let old = before["text"]
        .as_str()
        .ok_or("Malformed passage snapshot.")?;
    let new = after["text"]
        .as_str()
        .ok_or("Malformed passage snapshot.")?;
    let same = before["source_digest"] == after["source_digest"]
        && before["final_url"] == after["final_url"]
        && old == new;
    let old_lines = passage_diff::splitlines(old);
    let new_lines = passage_diff::splitlines(new);
    let diff = passage_diff::unified(
        &old_lines[..old_lines.len().min(MAX_TEXT_LINES)],
        &new_lines[..new_lines.len().min(MAX_TEXT_LINES)],
    );
    let truncated = refresh::truth(&before["text_truncated"])
        || refresh::truth(&after["text_truncated"])
        || old_lines.len() > MAX_TEXT_LINES
        || new_lines.len() > MAX_TEXT_LINES
        || diff.len() > MAX_DIFF_LINES
        || diff
            .iter()
            .any(|line| line.chars().count() > MAX_LINE_CHARS);
    let bounded: Vec<String> = diff
        .iter()
        .take(MAX_DIFF_LINES)
        .map(|line| line.chars().take(MAX_LINE_CHARS).collect())
        .collect();
    Ok(json!({
        "status": if same {"same"} else {"different"}, "url":after["url"],
        "before_digest":before["source_digest"], "after_digest":after["source_digest"],
        "before_final_url":before["final_url"], "after_final_url":after["final_url"],
        "passage_diff":bounded, "comparison_truncated":truncated, "boundary":COMPARISON_BOUNDARY
    }))
}

/// Python ensure_ascii output, including DEL and supplementary surrogate pairs.
pub fn rendered(value: &Value) -> Result<String> {
    use std::fmt::Write;
    let mut output = String::new();
    for ch in serde_json::to_string_pretty(value)?.chars() {
        if ch < '\u{7f}' {
            output.push(ch);
        } else {
            for unit in ch.encode_utf16(&mut [0; 2]) {
                write!(output, "\\u{unit:04x}")?;
            }
        }
    }
    output.push('\n');
    Ok(output)
}

pub(crate) fn output_path(path: &Path, root: &Path) -> Result<PathBuf> {
    let output = crate::sweep::resolve(path, 0)?;
    let root = crate::sweep::resolve(root, 0)?;
    // Windows can collapse parent components before following links. Refuse
    // ambiguous spellings instead of writing to a different interpretation.
    #[cfg(windows)]
    if path
        .components()
        .any(|part| part == std::path::Component::ParentDir)
        && crate::sweep::resolve(&std::path::absolute(path)?, 0)? != output
    {
        return Err(OUTPUT_ERROR.into());
    }
    if output.starts_with(root) || output.exists() {
        return Err(OUTPUT_ERROR.into());
    }
    Ok(output)
}

pub fn cli(args: impl Iterator<Item = OsString>) -> Result<u8> {
    let mut args = args.peekable();
    let usage = "usage: accounting-skills source-passages snapshot --url URL --output PATH [--root PATH] | compare --before PATH --after PATH --output PATH [--root PATH]";
    let mut options = std::collections::BTreeMap::new();
    let mode = args.next().unwrap_or_default();
    if matches!(mode.to_str(), Some("--help" | "-h")) {
        println!("{usage}");
        return Ok(0);
    }
    let mode = mode.to_str().unwrap_or("");
    if !matches!(mode, "snapshot" | "compare") {
        eprintln!("{usage}");
        return Ok(2);
    }
    while let Some(arg) = args.next() {
        let key = arg.to_str().unwrap_or("");
        if matches!(key, "--help" | "-h") {
            println!("{usage}");
            return Ok(0);
        }
        if !matches!(key, "--root" | "--output")
            && !(mode == "snapshot" && key == "--url")
            && !(mode == "compare" && matches!(key, "--before" | "--after"))
        {
            eprintln!("{usage}");
            return Ok(2);
        }
        let Some(value) = args
            .next()
            .filter(|v| !v.as_encoded_bytes().starts_with(b"--"))
        else {
            eprintln!("{usage}");
            return Ok(2);
        };
        options.insert(key.to_owned(), value);
    }
    let required: &[&str] = if mode == "snapshot" {
        &["--output", "--url"]
    } else {
        &["--output", "--before", "--after"]
    };
    if required.iter().any(|key| !options.contains_key(*key)) {
        eprintln!("{usage}");
        return Ok(2);
    }
    let root = options
        .get("--root")
        .map(PathBuf::from)
        .unwrap_or(std::env::current_dir()?);
    let output = match output_path(Path::new(&options["--output"]), &root) {
        Ok(path) => path,
        Err(error) => {
            if error.to_string() != OUTPUT_ERROR {
                println!(
                    "{}",
                    json!({"status":"unavailable", "error":error.to_string()})
                );
                return Ok(1);
            }
            eprintln!("{error}");
            return Ok(2);
        }
    };
    let run = || -> Result<u8> {
        let skills = root.join(".claude/skills");
        let result = if mode == "snapshot" {
            snapshot(
                options["--url"].to_str().ok_or("URL must be valid UTF-8")?,
                &skills,
            )?
        } else {
            compare(
                &load_snapshot(Path::new(&options["--before"]), &skills)?,
                &load_snapshot(Path::new(&options["--after"]), &skills)?,
            )?
        };
        fs::create_dir_all(output.parent().ok_or("Output has no parent")?)?;
        let checked = output_path(&output, &root)?;
        let mut file = fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(checked)?;
        file.write_all(crate::platform_text(&rendered(&result)?).as_bytes())?;
        Ok(
            if result["status"] == "unavailable" || result["available"] == false {
                2
            } else {
                0
            },
        )
    };
    match run() {
        Ok(code) => Ok(code),
        Err(error) => {
            println!(
                "{}",
                json!({"status":"unavailable", "error":error.to_string()})
            );
            Ok(1)
        }
    }
}
