use accounting_skills::{Result, platform_text, read_text, rendered};
use std::{
    fs,
    io::{self, Write},
    path::PathBuf,
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
    if command.as_deref() == Some(std::ffi::OsStr::new("sweep-outcome")) {
        return accounting_skills::sweep::cli(args);
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
    let matrix = rendered(&root)?;
    let coverage = root.join("coverage.json");
    if write {
        fs::write(coverage, platform_text(&matrix))?;
        io::stdout().write_all(platform_text("wrote coverage.json\n").as_bytes())?;
    } else {
        let current = if coverage.is_file() {
            read_text(&coverage)?
        } else {
            String::new()
        };
        if check && current != matrix {
            io::stderr().write_all(
                platform_text(
                    "coverage.json is out of date. Run: python scripts/build_coverage.py --write\n",
                )
                .as_bytes(),
            )?;
            return Ok(2);
        }
        io::stdout().write_all(platform_text(&matrix).as_bytes())?;
    }
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
