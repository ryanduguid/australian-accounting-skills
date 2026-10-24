//! Freeze task input and a withheld rubric without observing or grading a model.
use crate::{Result, source_content, source_passages, sweep, validation};
use fancy_regex::Regex;
use serde_json::{Map, json};
use std::{
    collections::BTreeMap,
    ffi::OsString,
    fs,
    io::Write,
    path::{Component, Path, PathBuf},
    sync::LazyLock,
};

pub const TASK_SECTIONS: &[&str] = &[
    "Scenario",
    "Task",
    "Synthetic inputs",
    "Deliberately unavailable evidence",
];

pub fn digest(bytes: &[u8]) -> String {
    source_content::sha256(bytes)
}

pub fn task_input(card: &[u8], name: &str) -> Result<(Vec<u8>, Vec<String>)> {
    static HEADING: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"(?m)^## ([^\r\n]+)\r?$").unwrap());
    let (metadata, body) = validation::parse_front_matter(std::str::from_utf8(card)?, name)?;
    let matches = HEADING
        .captures_iter(&body)
        .collect::<std::result::Result<Vec<_>, _>>()?;
    let mut sections = BTreeMap::new();
    for (i, cap) in matches.iter().enumerate() {
        let heading = cap.get(1).unwrap().as_str();
        if sections.contains_key(heading) {
            return Err(format!("duplicate section: {heading}").into());
        }
        let end = matches
            .get(i + 1)
            .map(|next| next.get(0).unwrap().start())
            .unwrap_or(body.len());
        sections.insert(
            heading,
            body[cap.get(0).unwrap().end()..end].trim_matches(source_content::space),
        );
    }
    let mut missing: Vec<_> = TASK_SECTIONS
        .iter()
        .filter(|heading| !sections.contains_key(**heading))
        .copied()
        .collect();
    if !missing.is_empty() {
        missing.sort_unstable();
        let names = missing
            .iter()
            .map(|s| validation::repr(s))
            .collect::<Vec<_>>()
            .join(", ");
        return Err(format!("missing task sections: [{names}]").into());
    }
    let text = TASK_SECTIONS
        .iter()
        .map(|heading| format!("## {heading}\n\n{}", sections[heading]))
        .collect::<Vec<_>>()
        .join("\n\n")
        + "\n";
    let skills = metadata["target_skills"]
        .as_array()
        .unwrap()
        .iter()
        .map(|s| s.as_str().unwrap().to_owned())
        .collect();
    Ok((text.into_bytes(), skills))
}

pub fn credential_name(name: &str) -> bool {
    // Of the non-ASCII case folds relevant to these ASCII patterns, Kelvin K
    // is covered by lowercase and long S needs its full-casefold mapping.
    let folded = name.to_lowercase().replace('ſ', "s");
    if folded.starts_with(".env") {
        return true;
    }
    // Path.suffix ignores leading dots and trailing dots, as Python 3.14 does.
    let stripped = folded.trim_start_matches('.');
    let suffix = stripped
        .rsplit_once('.')
        .map(|(_, suffix)| suffix)
        .unwrap_or("");
    matches!(suffix, "pem" | "key" | "token" | "tokens")
}

fn checked_components(
    path: &Path,
    root: &Path,
    check_link: &mut impl FnMut(&Path) -> Result<bool>,
) -> Result<()> {
    let mut current = root.to_path_buf();
    for part in path.strip_prefix(root)?.components() {
        if !matches!(part, Component::Normal(_)) {
            return Err("unsafe context path component".into());
        }
        current.push(part);
        if check_link(&current)? {
            return Err("skill context must not follow symbolic links or reparse points".into());
        }
    }
    Ok(())
}

fn inventory(
    folder: &Path,
    paths: &mut Vec<PathBuf>,
    check_link: &mut impl FnMut(&Path) -> Result<bool>,
) -> Result<()> {
    for entry in fs::read_dir(folder)? {
        let path = entry?.path();
        if check_link(&path)? {
            return Err("skill context must not follow symbolic links or reparse points".into());
        }
        let name = path
            .file_name()
            .and_then(|s| s.to_str())
            .ok_or("non-Unicode context filename")?;
        if credential_name(name) {
            return Err("credential files are not trial context".into());
        }
        let metadata = fs::symlink_metadata(&path)?;
        if metadata.is_dir() {
            inventory(&path, paths, check_link)?;
        } else if metadata.is_file() {
            paths.push(path);
        } else {
            return Err("skill context must contain only regular files and directories".into());
        }
    }
    Ok(())
}

pub fn prepare_with(
    case_id: &str,
    destination: &Path,
    model: &str,
    runtime: &str,
    root: &Path,
    mut check_link: impl FnMut(&Path) -> Result<bool>,
) -> Result<()> {
    static SLUG: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"\A[a-z0-9]+(?:-[a-z0-9]+)*\z").unwrap());
    if !SLUG.is_match(case_id)? {
        return Err("case ID must be a lowercase hyphenated slug".into());
    }
    let root = fs::canonicalize(root)?;
    let resolved = sweep::resolve(destination, 0)?;
    if resolved.starts_with(&root) {
        return Err("trial evidence must be outside the repository".into());
    }
    if resolved.exists() {
        return Err("destination already exists; preserve the frozen trial".into());
    }
    let destination = source_passages::output_path(destination, &root)?;
    let card_path = root.join("validation/cases").join(format!("{case_id}.md"));
    checked_components(&card_path, &root, &mut check_link)?;
    if !fs::symlink_metadata(&card_path)?.is_file() {
        return Err("expected regular trial card".into());
    }
    let card = fs::read(&card_path)?;
    let (task, skills) = task_input(&card, &format!("{case_id}.md"))?;
    let mut files = Map::new();
    for skill in &skills {
        let folder = root.join(".claude/skills").join(skill);
        // Check ancestors before looking inside: a plain skill directory can
        // otherwise be reached through a linked .claude or skills directory.
        checked_components(&folder, &root, &mut check_link)?;
        let mut paths = Vec::new();
        inventory(&folder, &mut paths, &mut check_link)?;
        paths.sort_by_cached_key(|path| {
            // pathlib orders component tuples, not the joined pathname.
            path.components()
                .map(|part| {
                    let text = part.as_os_str().to_string_lossy();
                    if cfg!(windows) {
                        text.to_lowercase()
                    } else {
                        text.into_owned()
                    }
                })
                .collect::<Vec<_>>()
        });
        for path in paths {
            let relative = path
                .strip_prefix(&root)?
                .to_str()
                .ok_or("non-Unicode context filename")?
                .replace(std::path::MAIN_SEPARATOR, "/");
            files.insert(relative, json!(digest(&fs::read(path)?)));
        }
        if !folder.join("SKILL.md").is_file() {
            return Err(format!("missing skill: {skill}").into());
        }
    }
    let manifest = json!({"case_id":case_id, "model":model, "runtime":runtime, "target_skills":skills, "files":files,
        "tools":"Freeze actual tool availability before observation; preparation establishes none.",
        "input_sha256":digest(&task), "rubric_sha256":digest(&card)});
    fs::create_dir_all(destination.parent().ok_or("destination has no parent")?)?;
    source_passages::output_path(&destination, &root)?;
    fs::create_dir(&destination)?;
    // Byte writes intentionally use LF JSON, independent of the host platform.
    let context = source_passages::rendered(&manifest)?;
    for (name, content) in [
        ("input.md", task.as_slice()),
        ("rubric.md", card.as_slice()),
        ("context.json", context.as_bytes()),
    ] {
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(destination.join(name))?
            .write_all(content)?;
    }
    Ok(())
}

pub fn prepare(
    case_id: &str,
    destination: &Path,
    model: &str,
    runtime: &str,
    root: &Path,
) -> Result<()> {
    prepare_with(
        case_id,
        destination,
        model,
        runtime,
        root,
        validation::is_reparse_point,
    )
}

pub fn cli(args: impl Iterator<Item = OsString>) -> Result<u8> {
    let usage = "usage: accounting-skills prepare-trial CASE_ID DESTINATION [--model MODEL] [--runtime RUNTIME] [--root PATH]";
    let mut args = args.peekable();
    let mut positional = Vec::new();
    let mut root = std::env::current_dir()?;
    let mut model = "unselected".to_owned();
    let mut runtime = "unselected".to_owned();
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--help" | "-h") => {
                println!("{usage}");
                return Ok(0);
            }
            Some(key @ ("--root" | "--model" | "--runtime")) => {
                let Some(value) = args
                    .next()
                    .filter(|v| !v.as_encoded_bytes().starts_with(b"--"))
                else {
                    eprintln!("{usage}");
                    return Ok(2);
                };
                if key == "--root" {
                    root = value.into();
                } else {
                    let value = value
                        .into_string()
                        .map_err(|_| "metadata must be Unicode")?;
                    if key == "--model" {
                        model = value;
                    } else {
                        runtime = value;
                    }
                }
            }
            Some(value) if !value.starts_with('-') && positional.len() < 2 => positional.push(arg),
            _ => {
                eprintln!("{usage}");
                return Ok(2);
            }
        }
    }
    if positional.len() != 2 {
        eprintln!("{usage}");
        return Ok(2);
    }
    prepare(
        positional[0].to_str().ok_or("case ID must be Unicode")?,
        Path::new(&positional[1]),
        &model,
        &runtime,
        &root,
    )?;
    Ok(0)
}
