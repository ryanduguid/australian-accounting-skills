// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! Flags tool calls in kept `claude plugin eval` traces whose input names the
//! eval suite, a grader or a validation card. The graders sit inside the
//! evaluated plugin copy, so a model that could have read its own rubric voids
//! that card. Ported from the 4 November 2026 `audit_grader_reads.py`; the
//! report is the same, and the command fails when it flags or cannot read
//! anything.
use crate::{Result, platform_text};
use fancy_regex::Regex;
use serde::Serialize;
use serde_json::{Value, ser::Formatter};
use std::{
    ffi::OsString,
    fs,
    io::{self, Write},
    path::{Component, Path, PathBuf},
    sync::LazyLock,
};

static SUSPECT: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(^|[\\/])(evals|graders|validation|held)([\\/]|$)|required-checks|restraint\.md|skill-fired|case\.yaml|rubric").unwrap()
});

/// Python's `json.dumps` spacing and float spelling, so the printed input and
/// its 200-character cut match the original script.
struct PythonJson;

impl Formatter for PythonJson {
    fn begin_array_value<W: ?Sized + Write>(
        &mut self,
        writer: &mut W,
        first: bool,
    ) -> io::Result<()> {
        if first {
            Ok(())
        } else {
            writer.write_all(b", ")
        }
    }
    fn begin_object_key<W: ?Sized + Write>(
        &mut self,
        writer: &mut W,
        first: bool,
    ) -> io::Result<()> {
        if first {
            Ok(())
        } else {
            writer.write_all(b", ")
        }
    }
    fn begin_object_value<W: ?Sized + Write>(&mut self, writer: &mut W) -> io::Result<()> {
        writer.write_all(b": ")
    }
    fn write_f64<W: ?Sized + Write>(&mut self, writer: &mut W, value: f64) -> io::Result<()> {
        writer.write_all(python_float(value).as_bytes())
    }
}

/// Python's `repr` of a finite float: positional from 1e-4 up to 1e16, otherwise
/// shortest digits with a signed exponent of at least 2 digits.
fn python_float(value: f64) -> String {
    let scientific = format!("{value:e}");
    let (digits, exponent) = scientific.split_once('e').unwrap_or((&scientific, "0"));
    let exponent: i32 = exponent.parse().unwrap_or(0);
    if (-4..16).contains(&exponent) {
        let positional = value.to_string();
        if positional.contains('.') {
            positional
        } else {
            positional + ".0"
        }
    } else {
        let sign = if exponent < 0 { '-' } else { '+' };
        format!("{digits}e{sign}{:02}", exponent.abs())
    }
}

fn python_json(value: &Value) -> Result<String> {
    let mut serializer = serde_json::Serializer::with_formatter(Vec::new(), PythonJson);
    value.serialize(&mut serializer)?;
    Ok(String::from_utf8(serializer.into_inner())?)
}

/// `str()` of the tool name as the original printed it.
fn python_str(value: Option<&Value>) -> Result<String> {
    Ok(match value {
        None | Some(Value::Null) => "None".into(),
        Some(Value::String(text)) => text.clone(),
        Some(Value::Bool(flag)) => if *flag { "True" } else { "False" }.into(),
        // shortcut: a list or object name prints as JSON, where Python printed
        // its repr; tool names are strings in every trace seen so far.
        Some(other) => python_json(other)?,
    })
}

/// Every `output.jsonl` under the root, not following directory links.
fn traces(dir: &Path, found: &mut Vec<PathBuf>) -> Result<()> {
    let listing = if dir.as_os_str().is_empty() {
        Path::new(".")
    } else {
        dir
    };
    for entry in fs::read_dir(listing).map_err(|error| format!("{}: {error}", listing.display()))? {
        let entry = entry?;
        let path = dir.join(entry.file_name());
        if entry.file_type()?.is_dir() {
            traces(&path, found)?;
        } else if entry.file_name() == "output.jsonl" {
            found.push(path);
        }
    }
    Ok(())
}

/// The suspect calls in one trace, and the line numbers that were not JSON.
fn audit(trace: &Path) -> Result<(Vec<String>, Vec<usize>)> {
    let bytes = fs::read(trace).map_err(|error| format!("{}: {error}", trace.display()))?;
    let (mut hits, mut unreadable) = (Vec::new(), Vec::new());
    // The original split on every Unicode line break, which cuts a record whose
    // tool input holds a raw U+2028 and hides that call; JSON Lines splits on \n.
    for (index, line) in String::from_utf8_lossy(&bytes).lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let Ok(event) = serde_json::from_str::<Value>(line) else {
            unreadable.push(index + 1);
            continue;
        };
        let Some(blocks) = event.pointer("/message/content").and_then(Value::as_array) else {
            continue;
        };
        for block in blocks {
            if block.get("type").and_then(Value::as_str) != Some("tool_use") {
                continue;
            }
            let input = python_json(block.get("input").unwrap_or(&Value::Null))?;
            if SUSPECT.is_match(&input)? {
                let shown: String = input.chars().take(200).collect();
                hits.push(format!("{} {shown}", python_str(block.get("name"))?));
            }
        }
    }
    Ok((hits, unreadable))
}

pub fn cli(args: impl Iterator<Item = OsString>) -> Result<u8> {
    let roots: Vec<PathBuf> = args.map(PathBuf::from).collect();
    if roots.is_empty() {
        return Err("usage: accounting-skills audit-grader-reads ROOT...".into());
    }
    let (mut report, mut problems) = (String::new(), String::new());
    let (mut total, mut flagged) = (0, 0);
    for root in roots {
        // Python's Path drops "." parts, so a trace prints as it did there.
        let root: PathBuf = root
            .components()
            .filter(|part| *part != Component::CurDir)
            .collect();
        let mut found = Vec::new();
        traces(&root, &mut found)?;
        found.sort();
        for trace in found {
            total += 1;
            let (hits, unreadable) = audit(&trace)?;
            if !hits.is_empty() {
                flagged += 1;
                report += &format!("FLAG {}\n", trace.display());
                for hit in hits.iter().take(5) {
                    report += &format!("  {hit}\n");
                }
            }
            for line in unreadable {
                problems += &format!(
                    "SKIP {}:{line} is not JSON, so its tool calls were not audited\n",
                    trace.display()
                );
            }
        }
    }
    report += &format!("traces={total} flagged={flagged}\n");
    if total == 0 {
        problems += "no output.jsonl trace found, so nothing was audited\n";
    }
    io::stdout().write_all(platform_text(&report).as_bytes())?;
    io::stderr().write_all(platform_text(&problems).as_bytes())?;
    Ok(u8::from(flagged > 0 || !problems.is_empty()))
}
