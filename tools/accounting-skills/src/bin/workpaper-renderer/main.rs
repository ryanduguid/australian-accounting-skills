// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Workpaper renderer and `.xlsx` formula verifier for Australian accounting
//! review packs. Renders structured JSON or Markdown workpapers into `.xlsx`
//! (with deterministic formula verification), `.docx` and `.pdf` drafts with a
//! mandatory prep-only review banner.

mod docx;
mod formula;
mod markdown;
mod model;
mod pdf;
mod xlsx;
mod zip;

use model::{DRAFT_BANNER, VerificationReport, Workpaper, schema_json};
use std::{
    ffi::OsString,
    fs,
    io::{self, Write},
    path::{Path, PathBuf},
    process::ExitCode,
};

const USAGE: &str = "\
usage:
  workpaper-renderer render --input PATH [--format json|md] [--xlsx PATH] [--docx PATH] [--pdf PATH] [--report PATH]
  workpaper-renderer verify-xlsx --input PATH [--report PATH]
  workpaper-renderer schema
";

fn write_atomic_no_symlink(path: &Path, bytes: &[u8]) -> Result<(), String> {
    if let Ok(meta) = fs::symlink_metadata(path)
        && !meta.file_type().is_file()
    {
        return Err(format!(
            "refusing to write non-regular file or symlink: {}",
            path.display()
        ));
    }
    if let Some(parent) = path.parent()
        && !parent.as_os_str().is_empty()
    {
        fs::create_dir_all(parent).map_err(|e| format!("cannot create output folder: {e}"))?;
    }
    let mut temp = path.as_os_str().to_owned();
    temp.push(format!(".{}.tmp", std::process::id()));
    let temp = PathBuf::from(temp);
    let written = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temp)
        .and_then(|mut file| file.write_all(bytes))
        .and_then(|()| fs::rename(&temp, path));
    if written.is_err() {
        let _ = fs::remove_file(&temp);
    }
    written.map_err(|e| format!("failed to write {}: {e}", path.display()))
}

fn next_path(args: &mut impl Iterator<Item = OsString>, flag: &str) -> Result<PathBuf, String> {
    args.next()
        .filter(|v| !v.as_encoded_bytes().starts_with(b"-"))
        .map(PathBuf::from)
        .ok_or_else(|| format!("{flag} requires a path"))
}

fn cmd_render(mut args: impl Iterator<Item = OsString>) -> Result<u8, String> {
    let mut input: Option<PathBuf> = None;
    let mut format: Option<String> = None;
    let mut xlsx_out: Option<PathBuf> = None;
    let mut docx_out: Option<PathBuf> = None;
    let mut pdf_out: Option<PathBuf> = None;
    let mut report_out: Option<PathBuf> = None;

    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--help" | "-h") => {
                print!("{USAGE}");
                return Ok(0);
            }
            Some("--input") => input = Some(next_path(&mut args, "--input")?),
            Some("--format") => {
                let value = args
                    .next()
                    .and_then(|v| v.into_string().ok())
                    .ok_or_else(|| "--format requires json or md".to_owned())?;
                format = Some(value);
            }
            Some("--xlsx") => xlsx_out = Some(next_path(&mut args, "--xlsx")?),
            Some("--docx") => docx_out = Some(next_path(&mut args, "--docx")?),
            Some("--pdf") => pdf_out = Some(next_path(&mut args, "--pdf")?),
            Some("--report") => report_out = Some(next_path(&mut args, "--report")?),
            Some(other) => return Err(format!("unknown argument: {other}")),
            None => return Err("non-UTF-8 argument".to_owned()),
        }
    }

    let input = input.ok_or_else(|| "render requires --input PATH".to_owned())?;
    if xlsx_out.is_none() && docx_out.is_none() && pdf_out.is_none() {
        return Err("render requires at least one of --xlsx, --docx or --pdf".to_owned());
    }

    let raw = fs::read_to_string(&input)
        .map_err(|e| format!("cannot read input {}: {e}", input.display()))?;
    let detected = format.unwrap_or_else(|| {
        match input
            .extension()
            .and_then(|e| e.to_str())
            .map(str::to_ascii_lowercase)
            .as_deref()
        {
            Some("md" | "markdown") => "md".to_owned(),
            _ => "json".to_owned(),
        }
    });

    let wp: Workpaper = match detected.as_str() {
        "json" => serde_json::from_str(&raw).map_err(|e| format!("invalid workpaper JSON: {e}"))?,
        "md" => markdown::parse_markdown(&raw),
        other => {
            return Err(format!(
                "unsupported --format '{other}' (expected json or md)"
            ));
        }
    };

    let mut report = VerificationReport {
        ok: true,
        draft_banner: DRAFT_BANNER.to_owned(),
        formula_count: 0,
        error_count: 0,
        open_exception_count: wp.exceptions.len(),
        unverified_mentions: wp.unverified_mentions(),
        formulas: Vec::new(),
        errors: Vec::new(),
    };

    if let Some(path) = &xlsx_out {
        let (bytes, xlsx_report) = xlsx::render_xlsx(&wp)?;
        write_atomic_no_symlink(path, &bytes)?;
        report = xlsx_report;
    }
    if let Some(path) = &docx_out {
        let bytes = docx::render_docx(&wp)?;
        write_atomic_no_symlink(path, &bytes)?;
    }
    if let Some(path) = &pdf_out {
        let bytes = pdf::render_pdf(&wp);
        write_atomic_no_symlink(path, &bytes)?;
    }

    let report_json =
        serde_json::to_string_pretty(&report).map_err(|e| format!("report error: {e}"))? + "\n";
    if let Some(path) = &report_out {
        write_atomic_no_symlink(path, report_json.as_bytes())?;
    } else {
        io::stdout()
            .write_all(report_json.as_bytes())
            .map_err(|e| format!("stdout error: {e}"))?;
    }

    Ok(if report.ok { 0 } else { 1 })
}

fn cmd_verify_xlsx(mut args: impl Iterator<Item = OsString>) -> Result<u8, String> {
    let mut input: Option<PathBuf> = None;
    let mut report_out: Option<PathBuf> = None;

    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--help" | "-h") => {
                print!("{USAGE}");
                return Ok(0);
            }
            Some("--input") => input = Some(next_path(&mut args, "--input")?),
            Some("--report") => report_out = Some(next_path(&mut args, "--report")?),
            Some(other) => return Err(format!("unknown argument: {other}")),
            None => return Err("non-UTF-8 argument".to_owned()),
        }
    }

    let input = input.ok_or_else(|| "verify-xlsx requires --input PATH".to_owned())?;
    let bytes = fs::read(&input).map_err(|e| format!("cannot read {}: {e}", input.display()))?;
    let report = xlsx::verify_xlsx_bytes(&bytes)?;
    let report_json =
        serde_json::to_string_pretty(&report).map_err(|e| format!("report error: {e}"))? + "\n";
    if let Some(path) = &report_out {
        write_atomic_no_symlink(path, report_json.as_bytes())?;
    } else {
        io::stdout()
            .write_all(report_json.as_bytes())
            .map_err(|e| format!("stdout error: {e}"))?;
    }
    Ok(if report.ok { 0 } else { 1 })
}

fn run() -> Result<u8, String> {
    let mut args = std::env::args_os().skip(1);
    match args.next().and_then(|s| s.into_string().ok()).as_deref() {
        Some("render") => cmd_render(args),
        Some("verify-xlsx") => cmd_verify_xlsx(args),
        Some("schema") => {
            print!("{}", schema_json());
            Ok(0)
        }
        Some("--help" | "-h") => {
            print!("{USAGE}");
            Ok(0)
        }
        _ => {
            eprint!("{USAGE}");
            Ok(2)
        }
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(code) => ExitCode::from(code),
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(1)
        }
    }
}
