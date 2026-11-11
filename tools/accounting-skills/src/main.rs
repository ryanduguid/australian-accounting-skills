// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use accounting_skills::{
    Result, VERIFICATION_PAGE, platform_text, read_text, rendered_with_page, replace_file,
};
use std::{
    fs,
    io::{self, Write},
    path::{Path, PathBuf},
};

fn run() -> Result<u8> {
    let mut args = std::env::args_os().skip(1);
    let mut root = std::env::current_dir()?;
    let mut write = false;
    let mut check = false;
    let command = args.next();
    if command.as_deref() == Some(std::ffi::OsStr::new("prepare-trial")) {
        return accounting_skills::trial::cli(args);
    }
    if command.as_deref() == Some(std::ffi::OsStr::new("source-passages")) {
        return accounting_skills::source_passages::cli(args);
    }
    if command.as_deref() == Some(std::ffi::OsStr::new("source-refresh")) {
        return accounting_skills::source_refresh::cli(args);
    }
    if command.as_deref() == Some(std::ffi::OsStr::new("validate-validation")) {
        return accounting_skills::validation::cli(args);
    }
    if command.as_deref() == Some(std::ffi::OsStr::new("build-plugin-evals")) {
        return accounting_skills::plugin_evals::cli(args);
    }
    if command.as_deref() == Some(std::ffi::OsStr::new("last-changed")) {
        return accounting_skills::last_changed::cli(args);
    }
    if command.as_deref() == Some(std::ffi::OsStr::new("statement-check")) {
        return accounting_skills::statement_check::cli(args);
    }
    if command.as_deref() == Some(std::ffi::OsStr::new("sweep-outcome")) {
        return accounting_skills::sweep::cli(args);
    }
    if command.as_deref() == Some(std::ffi::OsStr::new("audit-grader-reads")) {
        return accounting_skills::grader_audit::cli(args);
    }
    if command.as_deref() != Some(std::ffi::OsStr::new("build-coverage")) {
        return Err(
            "usage: accounting-skills build-coverage [--root PATH] [--write] [--check]".into(),
        );
    }
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--root") => {
                root = PathBuf::from(
                    args.next()
                        .filter(|arg| !arg.as_encoded_bytes().starts_with(b"-"))
                        .ok_or("--root requires a path")?,
                );
            }
            Some("--write") => write = true,
            Some("--check") => check = true,
            _ => return Err("unknown argument".into()),
        }
    }
    let root = accounting_skills::canonical_root(&root)?;
    let (matrix, page) = rendered_with_page(&root)?;
    let outputs = [("coverage.json", &matrix), (VERIFICATION_PAGE, &page)];
    // Confine every output before reading or writing, so one linked path cannot
    // escape after another output has already been replaced.
    let mut files = Vec::with_capacity(outputs.len());
    for (relative, text) in outputs {
        let path = accounting_skills::within_root(&root, Path::new(relative))?;
        if !path.starts_with(&root) {
            return Err("path escapes the repository root".into());
        }
        files.push((relative, path, text));
    }
    if write {
        for (_, path, text) in &files {
            let parent = path.parent().ok_or("output has no parent")?;
            if !parent.starts_with(&root) {
                return Err("path escapes the repository root".into());
            }
            fs::create_dir_all(parent)?;
            replace_file(path, &platform_text(text))?;
        }
        io::stdout().write_all(
            platform_text(&format!("wrote coverage.json and {VERIFICATION_PAGE}\n")).as_bytes(),
        )?;
        return Ok(0);
    }
    if check {
        let mut stale = false;
        for (relative, path, text) in &files {
            if !path.starts_with(&root) {
                return Err("path escapes the repository root".into());
            }
            let current = if path.is_file() {
                read_text(path)?
            } else {
                String::new()
            };
            if current != **text {
                stale = true;
                io::stderr().write_all(
                    platform_text(&format!(
                        "{relative} is out of date. Run: cargo run --locked --manifest-path tools/accounting-skills/Cargo.toml -- build-coverage --write\n",
                    ))
                    .as_bytes(),
                )?;
            }
        }
        if stale {
            return Ok(2);
        }
    }
    io::stdout().write_all(platform_text(&matrix).as_bytes())?;
    Ok(0)
}

fn main() {
    let code = match run() {
        Ok(code) => code,
        Err(error) => {
            let _ = io::stderr().write_all(platform_text(&format!("FAIL {error}\n")).as_bytes());
            1
        }
    };
    std::process::exit(i32::from(code));
}
