// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Workpaper renderer and `.xlsx` formula verifier for Australian accounting
//! review packs. Renders structured JSON or Markdown workpapers into `.xlsx`
//! (with deterministic formula verification), `.docx` and `.pdf` drafts with a
//! mandatory prep-only review banner.

mod docx;
mod formula;
mod formula_funcs;
mod markdown;
mod model;
mod pdf;
mod xlsx;
mod xlsx_verify;
mod zip;

use model::{DRAFT_BANNER, VerificationReport, Workpaper, schema_json};
use std::{
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

fn next_path(args: &mut impl Iterator<Item = String>, flag: &str) -> Result<PathBuf, String> {
    args.next()
        .filter(|v| !v.starts_with('-'))
        .map(PathBuf::from)
        .ok_or_else(|| format!("{flag} requires a path"))
}

struct RenderOpts {
    input: PathBuf,
    format: Option<String>,
    xlsx_out: Option<PathBuf>,
    docx_out: Option<PathBuf>,
    pdf_out: Option<PathBuf>,
    report_out: Option<PathBuf>,
}

fn parse_render_opts(mut args: impl Iterator<Item = String>) -> Result<Option<RenderOpts>, String> {
    let mut input = None;
    let mut format = None;
    let mut xlsx_out = None;
    let mut docx_out = None;
    let mut pdf_out = None;
    let mut report_out = None;
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--help" | "-h" => {
                print!("{USAGE}");
                return Ok(None);
            }
            "--input" => input = Some(next_path(&mut args, "--input")?),
            "--format" => {
                format = Some(
                    args.next()
                        .ok_or_else(|| "--format requires json or md".to_owned())?,
                );
            }
            "--xlsx" => xlsx_out = Some(next_path(&mut args, "--xlsx")?),
            "--docx" => docx_out = Some(next_path(&mut args, "--docx")?),
            "--pdf" => pdf_out = Some(next_path(&mut args, "--pdf")?),
            "--report" => report_out = Some(next_path(&mut args, "--report")?),
            other => return Err(format!("unknown argument: {other}")),
        }
    }
    let input = input.ok_or_else(|| "render requires --input PATH".to_owned())?;
    if xlsx_out.is_none() && docx_out.is_none() && pdf_out.is_none() {
        return Err("render requires at least one of --xlsx, --docx or --pdf".to_owned());
    }
    Ok(Some(RenderOpts {
        input,
        format,
        xlsx_out,
        docx_out,
        pdf_out,
        report_out,
    }))
}

fn load_workpaper(path: &Path, format: Option<String>) -> Result<Workpaper, String> {
    let raw = fs::read_to_string(path)
        .map_err(|e| format!("cannot read input {}: {e}", path.display()))?;
    let detected = format.unwrap_or_else(|| {
        match path
            .extension()
            .and_then(|e| e.to_str())
            .map(str::to_ascii_lowercase)
            .as_deref()
        {
            Some("md" | "markdown") => "md".to_owned(),
            _ => "json".to_owned(),
        }
    });
    match detected.as_str() {
        "json" => serde_json::from_str(&raw).map_err(|e| format!("invalid workpaper JSON: {e}")),
        "md" => Ok(markdown::parse_markdown(&raw)),
        other => Err(format!(
            "unsupported --format '{other}' (expected json or md)"
        )),
    }
}

fn emit_report(report: &VerificationReport, out: Option<&Path>) -> Result<(), String> {
    let json =
        serde_json::to_string_pretty(report).map_err(|e| format!("report error: {e}"))? + "\n";
    if let Some(path) = out {
        write_atomic_no_symlink(path, json.as_bytes())
    } else {
        io::stdout()
            .write_all(json.as_bytes())
            .map_err(|e| format!("stdout error: {e}"))
    }
}

fn cmd_render(args: impl Iterator<Item = String>) -> Result<u8, String> {
    let Some(opts) = parse_render_opts(args)? else {
        return Ok(0);
    };
    let wp = load_workpaper(&opts.input, opts.format)?;
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
    if let Some(path) = &opts.xlsx_out {
        let (bytes, xlsx_report) = xlsx::render_xlsx(&wp)?;
        write_atomic_no_symlink(path, &bytes)?;
        report = xlsx_report;
    }
    if let Some(path) = &opts.docx_out {
        write_atomic_no_symlink(path, &docx::render_docx(&wp)?)?;
    }
    if let Some(path) = &opts.pdf_out {
        write_atomic_no_symlink(path, &pdf::render_pdf(&wp)?)?;
    }
    emit_report(&report, opts.report_out.as_deref())?;
    Ok(u8::from(!report.ok))
}

fn cmd_verify_xlsx(mut args: impl Iterator<Item = String>) -> Result<u8, String> {
    let mut input = None;
    let mut report_out = None;
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--help" | "-h" => {
                print!("{USAGE}");
                return Ok(0);
            }
            "--input" => input = Some(next_path(&mut args, "--input")?),
            "--report" => report_out = Some(next_path(&mut args, "--report")?),
            other => return Err(format!("unknown argument: {other}")),
        }
    }
    let input = input.ok_or_else(|| "verify-xlsx requires --input PATH".to_owned())?;
    let bytes = fs::read(&input).map_err(|e| format!("cannot read {}: {e}", input.display()))?;
    let report = xlsx_verify::verify_xlsx_bytes(&bytes)?;
    emit_report(&report, report_out.as_deref())?;
    Ok(u8::from(!report.ok))
}

fn run() -> Result<u8, String> {
    // Subcommand dispatch only; never used for authentication or privilege checks.
    // nosemgrep: rust.lang.security.args.args
    let mut args = std::env::args().skip(1);
    match args.next().as_deref() {
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
