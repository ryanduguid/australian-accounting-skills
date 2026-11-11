// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! Build a clean plugin copy with task-only `claude plugin eval` cases from the
//! validation cards and the routing cases.
use crate::{Result, platform_text, source_passages, strict_yaml, sweep, trial, validation};
use serde_json::{Map, Value, json};
use std::{
    collections::{BTreeMap, BTreeSet},
    ffi::OsString,
    fmt::Write as _,
    fs,
    io::{self, Write as _},
    path::{Path, PathBuf},
};

/// Held back from the evaluated session. Every other section is the task, so a
/// variant a required check depends on stays visible.
pub const WITHHELD_SECTIONS: [&str; 3] = [
    "Required checks",
    "Must not do",
    "Source-verification and reviewer boundary",
];
const PLUGIN_PATHS: [&str; 5] = [
    ".claude-plugin",
    ".claude/skills",
    ".claude/rules",
    "DISCLAIMER.md",
    "LICENSE",
];
const ALLOWED_TOOLS: [&str; 4] = ["Read", "Glob", "Grep", "Skill"];
/// Prompts that name no skill, so a run shows which skill Claude Code picks.
pub const ROUTING_CASES: &str = "validation/routing-cases.yaml";
const JUDGE_PREFACE: &str = "The answer comes from a session with no web access and no way to create files. Reporting a mutable rate, threshold or rule as unverified, and leaving it for a reviewer, satisfies a check that asks for verification. Judge substance, not wording: an equivalent statement counts. Numbers must match.";
const LINK_ERROR: &str = "plugin files must not be symbolic links or reparse points";

/// One case's files, keyed by their path relative to the case directory.
pub type CaseFiles = BTreeMap<String, String>;

/// Cases in build order, each named by its directory under `evals/`.
type Cases = Vec<(String, CaseFiles)>;

enum Field {
    Text(String),
    Count(u32),
    List(Vec<String>),
}

/// A double-quoted YAML scalar that YAML 1.1 and 1.2 readers both load back as
/// `text`: line breaks, controls and other non-printable characters are escaped.
fn quoted(text: &str) -> String {
    let mut out = String::from('"');
    for c in text.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\t' => out.push_str("\\t"),
            '\u{2028}' | '\u{2029}' | '\u{feff}' => {
                write!(out, "\\u{:04x}", u32::from(c)).unwrap();
            }
            ' '..='~'
            | '\u{a0}'..='\u{d7ff}'
            | '\u{e000}'..='\u{fffd}'
            | '\u{10000}'..='\u{10ffff}' => out.push(c),
            _ => write!(out, "\\u{:04x}", u32::from(c)).unwrap(),
        }
    }
    out.push('"');
    out
}

fn front_matter(fields: &[(&str, Field)]) -> String {
    let mut text = String::from("---\n");
    for (key, value) in fields {
        let value = match value {
            Field::Text(value) => quoted(value),
            Field::Count(value) => value.to_string(),
            Field::List(values) => format!(
                "[{}]",
                values
                    .iter()
                    .map(|value| quoted(value))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
        };
        writeln!(text, "{key}: {value}").unwrap();
    }
    text + "---\n"
}

/// A case prompt: its eval settings, then the task the evaluated session sees.
fn prompt_file(
    name: &str,
    description: String,
    tags: Vec<String>,
    runs: u32,
    max_turns: u32,
    task: &str,
) -> String {
    front_matter(&[
        ("name", Field::Text(name.into())),
        ("description", Field::Text(description)),
        ("tags", Field::List(tags)),
        ("runs", Field::Count(runs)),
        ("max_turns", Field::Count(max_turns)),
        (
            "allowed_tools",
            Field::List(ALLOWED_TOOLS.iter().map(|tool| tool.to_string()).collect()),
        ),
    ]) + "\n"
        + task
        + "\n"
}

/// The model-judged graders for the first two withheld sections, in order:
/// file name and instruction.
const JUDGED: [(&str, &str); 2] = [
    (
        "graders/required-checks.md",
        "PASS only if the answer meets every check below. FAIL if it misses any.",
    ),
    (
        "graders/restraint.md",
        "PASS unless the answer does any of the following. FAIL if it does.",
    ),
];

fn judge(instruction: &str, section: &str) -> String {
    front_matter(&[
        ("type", Field::Text("llm".into())),
        (
            "criteria",
            Field::Text(format!("{JUDGE_PREFACE}\n\n{instruction}\n\n{section}\n")),
        ),
        ("focus", Field::Text("last_message".into())),
    ]) + "\nJudge the final answer against the criteria.\n"
}

/// The text of each withheld section, in `WITHHELD_SECTIONS` order.
fn withheld<'a>(sections: &[(&str, &'a str)], name: &str) -> Result<[&'a str; 3]> {
    let mut texts = [""; 3];
    for (text, heading) in texts.iter_mut().zip(WITHHELD_SECTIONS) {
        *text = sections
            .iter()
            .find(|(seen, _)| *seen == heading)
            .map(|(_, text)| *text)
            .ok_or_else(|| format!("{name}: missing section: {heading}"))?;
    }
    Ok(texts)
}

/// A `tool_used` grader counting Skill calls to any of `skills`, with or
/// without the plugin namespace.
fn skill_grader(skills: &[&str], minimum: u32, maximum: Option<u32>) -> String {
    // Skill names are validated slugs, so the hyphen is the only regex
    // metacharacter they can hold; it is escaped as the graders always were.
    let names = skills
        .iter()
        .map(|skill| skill.replace('-', "\\-"))
        .collect::<Vec<_>>()
        .join("|");
    let mut fields = vec![
        ("type", Field::Text("tool_used".into())),
        ("tool", Field::Text("Skill".into())),
        (
            "input_match",
            Field::Text(format!(
                r#""skill"\s*:\s*"(?:australian-accounting-skills:)?(?:{names})""#
            )),
        ),
        ("min", Field::Count(minimum)),
    ];
    if let Some(maximum) = maximum {
        fields.push(("max", Field::Count(maximum)));
    }
    front_matter(&fields)
}

/// Return one card's case files: the task sections, and graders holding the
/// withheld sections.
pub fn build_case(card: &str, case_id: &str, runs: u32, max_turns: u32) -> Result<CaseFiles> {
    let name = format!("{case_id}.md");
    let (metadata, body) = validation::parse_front_matter(card, &name)?;
    let sections = trial::card_sections(&body).map_err(|error| format!("{name}: {error}"))?;
    let withheld = withheld(&sections, &name)?;
    let skills: Vec<&str> = metadata["target_skills"]
        .as_array()
        .unwrap()
        .iter()
        .map(|skill| skill.as_str().unwrap())
        .collect();
    let task = sections
        .iter()
        .filter(|(heading, _)| !WITHHELD_SECTIONS.contains(heading))
        .map(|(heading, text)| format!("## {heading}\n\n{text}"))
        .collect::<Vec<_>>()
        .join("\n\n");
    let tags = std::iter::once("card")
        .chain(skills.iter().copied())
        .map(str::to_owned)
        .collect();
    let mut files = CaseFiles::from([
        (
            "prompt.md".into(),
            prompt_file(
                case_id,
                format!("Task-only input from validation card {case_id}."),
                tags,
                runs,
                max_turns,
                &task,
            ),
        ),
        (
            "graders/skill-fired.md".into(),
            skill_grader(&skills, 1, None) + "\nA target skill must fire.\n",
        ),
    ]);
    for ((file, instruction), section) in JUDGED.into_iter().zip(withheld) {
        files.insert(file.into(), judge(instruction, section));
    }
    Ok(files)
}

/// Return one routing case's directory name and files: the expected skill must
/// fire and its neighbours must not.
pub fn build_routing_case(case: &Value, runs: u32, max_turns: u32) -> Result<(String, CaseFiles)> {
    let text = |key: &str| {
        case.get(key)
            .and_then(Value::as_str)
            .ok_or_else(|| format!("routing case field {key} must be a string"))
    };
    let (id, skill, prompt) = (text("id")?, text("skill")?, text("prompt")?);
    let others = case
        .get("not")
        .and_then(Value::as_array)
        .and_then(|others| others.iter().map(Value::as_str).collect::<Option<Vec<_>>>())
        .ok_or("routing case field not must be a list of strings")?;
    // The names become file names and grader patterns.
    if !std::iter::once(&id)
        .chain([&skill])
        .chain(&others)
        .all(|name| validation::is_slug(name))
    {
        return Err(format!(
            "routing case {id}: the id and skill names must be lowercase hyphenated slugs"
        )
        .into());
    }
    let name = format!("route-{id}");
    let mut files = CaseFiles::from([
        (
            "prompt.md".into(),
            prompt_file(
                &name,
                format!("Routing check: the prompt names no skill; {skill} should fire."),
                vec!["routing".into(), skill.into()],
                runs,
                max_turns,
                prompt,
            ),
        ),
        (
            "graders/skill-fired.md".into(),
            skill_grader(&[skill], 1, None) + "\nThe expected skill must fire.\n",
        ),
    ]);
    for other in others {
        files.insert(
            format!("graders/not-{other}.md"),
            skill_grader(&[other], 0, Some(0)) + "\nA neighbouring skill must not fire.\n",
        );
    }
    Ok((name, files))
}

fn copy(source: &Path, target: &Path) -> Result<()> {
    if validation::is_reparse_point(source)? {
        return Err(LINK_ERROR.into());
    }
    let metadata = fs::symlink_metadata(source)?;
    if metadata.is_dir() {
        fs::create_dir(target)?;
        for entry in fs::read_dir(source)? {
            let entry = entry?;
            copy(&entry.path(), &target.join(entry.file_name()))?;
        }
    } else if metadata.is_file() {
        fs::copy(source, target)?;
    } else {
        return Err("plugin files must be regular files or directories".into());
    }
    Ok(())
}

/// The skills with a file under `.claude/skills/<name>/` that differs between
/// `revision` and the working tree, and the commit `revision` names.
fn changed_skills(root: &Path, revision: &str) -> Result<(String, BTreeSet<String>)> {
    let commit = crate::git(
        root,
        &[
            "rev-parse",
            "--verify",
            "--quiet",
            "--end-of-options",
            &format!("{revision}^{{commit}}"),
        ],
    )
    .map_err(|_| format!("unknown revision: {revision}"))?;
    let paths = crate::git(
        root,
        &[
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            &commit,
            "--",
            ".claude/skills",
        ],
    )?;
    let skills = paths
        .split('\0')
        .filter_map(|path| path.strip_prefix(".claude/skills/")?.split_once('/'))
        .map(|(skill, _)| skill.to_owned())
        .collect();
    Ok((commit, skills))
}

/// Whether a case grading `skills` is built: always, unless `changed` limits
/// the build to cases grading a changed skill.
fn selected<'a>(
    changed: Option<&BTreeSet<String>>,
    mut skills: impl Iterator<Item = &'a str>,
) -> bool {
    changed.is_none_or(|changed| skills.any(|skill| changed.contains(skill)))
}

/// Render every validation card's case, and return the selected cases with
/// each selected card's digest.
fn card_cases(
    canonical: &Path,
    runs: u32,
    max_turns: u32,
    changed: Option<&BTreeSet<String>>,
) -> Result<(Cases, Map<String, Value>)> {
    let mut cases = Vec::new();
    let mut digests = Map::new();
    for path in crate::entries(&canonical.join("validation/cases"))? {
        if !crate::matches_suffix(&path, ".md")? {
            continue;
        }
        let stem = path
            .file_stem()
            .and_then(|stem| stem.to_str())
            .ok_or("filename is not Unicode")?
            .to_owned();
        let data = fs::read(&path)?;
        let text = std::str::from_utf8(&data)?;
        let files = build_case(text, &stem, runs, max_turns)?;
        let (metadata, _) = validation::parse_front_matter(text, &format!("{stem}.md"))?;
        let skills = metadata["target_skills"].as_array().into_iter().flatten();
        if !selected(changed, skills.filter_map(Value::as_str)) {
            continue;
        }
        digests.insert(stem.clone(), json!(trial::digest(&data)));
        cases.push((stem, files));
    }
    Ok((cases, digests))
}

/// Copy the plugin into the new `destination` and write the cases beside it.
fn write_copy(canonical: &Path, destination: &Path, cases: &[(String, CaseFiles)]) -> Result<()> {
    fs::create_dir_all(destination.parent().ok_or("destination has no parent")?)?;
    fs::create_dir(destination)?;
    // Cards and tests stay behind, so the evaluated session cannot read them.
    for relative in PLUGIN_PATHS {
        let source = canonical.join(relative);
        for ancestor in source.ancestors().skip(1) {
            if ancestor == canonical {
                break;
            }
            if validation::is_reparse_point(ancestor)? {
                return Err(LINK_ERROR.into());
            }
        }
        let target = destination.join(relative);
        fs::create_dir_all(target.parent().unwrap())?;
        copy(&source, &target)?;
    }
    for (name, files) in cases {
        for (relative, text) in files {
            let target = destination.join("evals").join(name).join(relative);
            fs::create_dir_all(target.parent().unwrap())?;
            fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&target)?
                .write_all(text.as_bytes())?;
        }
    }
    Ok(())
}

/// Write the plugin copy and its cases to a new `destination` outside `root`,
/// and return the manifest. With `changed_since`, only the cases grading a
/// skill changed since that revision are written.
pub fn build(
    destination: &Path,
    runs: u32,
    max_turns: u32,
    root: &Path,
    changed_since: Option<&str>,
) -> Result<Value> {
    let canonical = fs::canonicalize(root)?;
    let resolved = sweep::resolve(destination, 0)?;
    if resolved.starts_with(&canonical) {
        return Err("the evaluated plugin copy must be outside the repository".into());
    }
    if resolved.exists() {
        return Err("destination already exists; preserve the earlier build".into());
    }
    let destination = source_passages::output_path(destination, &canonical)?;
    let commit = crate::git(&canonical, &["rev-parse", "HEAD"])?;
    let git_root = crate::git(&canonical, &["rev-parse", "--show-toplevel"])?;
    if fs::canonicalize(git_root)? != canonical {
        return Err("the plugin root must be the Git repository top level".into());
    }
    // The copy carries uncommitted, untracked and ignored files, so the commit
    // alone would not identify what was evaluated.
    let mut status = vec![
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--ignored",
        "--",
    ];
    status.extend(PLUGIN_PATHS);
    let dirty = !crate::git(&canonical, &status)?.is_empty();
    let (since, changed) = match changed_since {
        Some(revision) => {
            let (commit, skills) = changed_skills(&canonical, revision)?;
            (Some(commit), Some(skills))
        }
        None => (None, None),
    };
    // Every case is rendered before anything is created, so a malformed card or
    // routing case leaves no partial copy behind.
    let (mut cases, digests) = card_cases(&canonical, runs, max_turns, changed.as_ref())?;
    let routing_bytes = fs::read(canonical.join(ROUTING_CASES))?;
    let routing = strict_yaml::card_mapping(std::str::from_utf8(&routing_bytes)?)?;
    let mut routes = Vec::new();
    for case in routing
        .as_array()
        .ok_or("routing cases must be a YAML list")?
    {
        let (name, files) = build_routing_case(case, runs, max_turns)?;
        // A routing case grades its expected skill and the neighbours it forbids.
        let graded =
            std::iter::once(&case["skill"]).chain(case["not"].as_array().into_iter().flatten());
        if !selected(changed.as_ref(), graded.filter_map(Value::as_str)) {
            continue;
        }
        routes.push(name.clone());
        cases.push((name, files));
    }
    let mut names = BTreeSet::new();
    if let Some((name, _)) = cases.iter().find(|(name, _)| !names.insert(name)) {
        return Err(format!("duplicate eval case: {name}").into());
    }
    if let (Some(revision), true) = (changed_since, cases.is_empty()) {
        return Err(format!("no case grades a skill changed since {revision}").into());
    }
    write_copy(&canonical, &destination, &cases)?;
    let manifest = json!({
        "commit": commit,
        "dirty": dirty,
        "changed_since": since,
        "runs": runs,
        "card_sha256": digests,
        "routing_sha256": trial::digest(&routing_bytes),
        "routing_cases": routes,
    });
    fs::write(
        destination.join("evals-manifest.json"),
        platform_text(&source_passages::rendered(&manifest)?),
    )?;
    Ok(manifest)
}

enum Parsed {
    Run {
        destination: PathBuf,
        root: PathBuf,
        runs: u32,
        max_turns: u32,
        changed_since: Option<String>,
    },
    Help,
    Usage,
}

fn parse(mut args: impl Iterator<Item = OsString>) -> Result<Parsed> {
    let mut destination = None;
    let mut root = std::env::current_dir()?;
    let (mut runs, mut max_turns) = (1, 12);
    let mut changed_since = None;
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--help" | "-h") => return Ok(Parsed::Help),
            Some(key @ ("--runs" | "--max-turns" | "--root" | "--changed-since")) => {
                let Some(value) = args
                    .next()
                    .filter(|value| !value.as_encoded_bytes().starts_with(b"--"))
                else {
                    return Ok(Parsed::Usage);
                };
                if key == "--root" {
                    root = value.into();
                    continue;
                }
                if key == "--changed-since" {
                    let Some(revision) = value.to_str() else {
                        return Ok(Parsed::Usage);
                    };
                    changed_since = Some(revision.to_owned());
                    continue;
                }
                // A case needs at least one run and one turn.
                let Some(count) = value
                    .to_str()
                    .and_then(|value| value.parse::<u32>().ok())
                    .filter(|count| *count > 0)
                else {
                    return Ok(Parsed::Usage);
                };
                *if key == "--runs" {
                    &mut runs
                } else {
                    &mut max_turns
                } = count;
            }
            Some(value) if !value.starts_with('-') && destination.is_none() => {
                destination = Some(PathBuf::from(&arg));
            }
            _ => return Ok(Parsed::Usage),
        }
    }
    Ok(
        destination.map_or(Parsed::Usage, |destination| Parsed::Run {
            destination,
            root,
            runs,
            max_turns,
            changed_since,
        }),
    )
}

pub fn cli(args: impl Iterator<Item = OsString>) -> Result<u8> {
    let usage = "usage: accounting-skills build-plugin-evals DESTINATION [--runs N] [--max-turns N] [--root PATH] [--changed-since REV]";
    let (destination, root, runs, max_turns, changed_since) = match parse(args)? {
        Parsed::Run {
            destination,
            root,
            runs,
            max_turns,
            changed_since,
        } => (destination, root, runs, max_turns, changed_since),
        Parsed::Help => {
            println!("{usage}");
            return Ok(0);
        }
        Parsed::Usage => {
            eprintln!("{usage}");
            return Ok(2);
        }
    };
    let manifest = build(
        &destination,
        runs,
        max_turns,
        &root,
        changed_since.as_deref(),
    )?;
    let cards = manifest["card_sha256"].as_object().map_or(0, Map::len);
    let routes = manifest["routing_cases"].as_array().map_or(0, Vec::len);
    io::stdout().write_all(
        platform_text(&format!(
            "built {} cases ({cards} cards, {routes} routing) in {}\n",
            cards + routes,
            destination.display()
        ))
        .as_bytes(),
    )?;
    Ok(0)
}
