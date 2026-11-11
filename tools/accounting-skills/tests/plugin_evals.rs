// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use accounting_skills::plugin_evals::{
    CaseFiles, WITHHELD_SECTIONS, build, build_case, build_routing_case,
};
use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
};
use yaml_rust2::{Yaml, YamlLoader};

fn repository() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn cards() -> Vec<PathBuf> {
    let mut cards: Vec<_> = fs::read_dir(repository().join("validation/cases"))
        .unwrap()
        .map(|entry| entry.unwrap().path())
        .filter(|path| path.extension().is_some_and(|suffix| suffix == "md"))
        .collect();
    cards.sort();
    cards
}

/// The parsed front matter of one generated file.
fn front(files: &CaseFiles, name: &str) -> Yaml {
    let text = &files[name];
    let end = text[4..].find("\n---\n").unwrap() + 4;
    assert!(text.starts_with("---\n"), "{name}");
    YamlLoader::load_from_str(&text[4..end]).unwrap().remove(0)
}

/// The text of one `## ` section of a card, as the card states it.
fn section<'a>(card: &'a str, heading: &str) -> &'a str {
    let start = card.find(&format!("\n## {heading}\n")).unwrap() + heading.len() + 5;
    let end = card[start..]
        .find("\n## ")
        .map_or(card.len(), |end| start + end);
    &card[start..end]
}

fn bullets(section: &str) -> Vec<&str> {
    section
        .lines()
        .filter_map(|line| line.strip_prefix("- "))
        .map(str::trim)
        .collect()
}

fn matches(pattern: &str, text: &str) -> bool {
    fancy_regex::Regex::new(pattern)
        .unwrap()
        .is_match(text)
        .unwrap()
}

#[test]
fn every_card_withholds_its_answers_and_grades_them() {
    for path in cards() {
        let card = fs::read_to_string(&path).unwrap();
        let id = path.file_stem().unwrap().to_str().unwrap();
        let files = build_case(&card, id, 1, 12).unwrap();
        let prompt = &files["prompt.md"];
        for heading in WITHHELD_SECTIONS {
            assert!(!prompt.contains(&format!("## {heading}")), "{id}");
        }
        let required = front(&files, "graders/required-checks.md");
        for check in bullets(section(&card, "Required checks")) {
            assert!(!prompt.contains(check), "{id}: {check}");
            assert!(
                required["criteria"].as_str().unwrap().contains(check),
                "{id}: {check}"
            );
        }
        let restraint = front(&files, "graders/restraint.md");
        for limit in bullets(section(&card, "Must not do")) {
            assert!(
                restraint["criteria"].as_str().unwrap().contains(limit),
                "{id}: {limit}"
            );
        }
        assert_eq!(front(&files, "prompt.md")["name"].as_str(), Some(id));
    }
}

#[test]
fn a_section_outside_the_withheld_list_stays_in_the_task() {
    let id = "au-bookkeeping-supported-reconciliation";
    let card = fs::read_to_string(repository().join(format!("validation/cases/{id}.md"))).unwrap();
    let files = build_case(&card, id, 1, 12).unwrap();
    assert!(files["prompt.md"].contains("## Incomplete-input variant"));
}

#[test]
fn skill_grader_matches_a_target_skill_with_or_without_the_namespace() {
    let id = "au-payroll-review-master-data-screen";
    let card = fs::read_to_string(repository().join(format!("validation/cases/{id}.md"))).unwrap();
    let files = build_case(&card, id, 1, 12).unwrap();
    let grader = front(&files, "graders/skill-fired.md");
    let pattern = grader["input_match"].as_str().unwrap();
    assert!(matches(
        pattern,
        r#"{"skill": "australian-accounting-skills:stp-finalisation"}"#
    ));
    assert!(matches(pattern, r#"{"skill": "au-payroll-review"}"#));
    assert!(!matches(pattern, r#"{"skill": "bas-preparation"}"#));
    assert_eq!(grader["min"].as_i64(), Some(1));
    assert!(grader["max"].is_badvalue());
}

#[test]
fn a_routing_case_grades_the_expected_skill_and_its_neighbours() {
    let case = serde_json::json!({"id": "x", "skill": "bas-preparation", "not": ["au-payroll-review"], "prompt": "Reconcile 1A."});
    let (name, files) = build_routing_case(&case, 1, 4).unwrap();
    assert_eq!(name, "route-x");
    assert!(files["prompt.md"].ends_with("---\n\nReconcile 1A.\n"));
    let prompt = front(&files, "prompt.md");
    assert_eq!(prompt["name"].as_str(), Some("route-x"));
    assert_eq!(prompt["max_turns"].as_i64(), Some(4));
    let fired = front(&files, "graders/skill-fired.md");
    assert_eq!(
        (fired["min"].as_i64(), fired["max"].is_badvalue()),
        (Some(1), true)
    );
    let pattern = fired["input_match"].as_str().unwrap();
    assert!(matches(
        pattern,
        r#"{"skill": "australian-accounting-skills:bas-preparation"}"#
    ));
    assert!(!matches(pattern, r#"{"skill": "au-payroll-review"}"#));
    let other = front(&files, "graders/not-au-payroll-review.md");
    assert_eq!(
        (other["min"].as_i64(), other["max"].as_i64()),
        (Some(0), Some(0))
    );
    assert!(matches(
        other["input_match"].as_str().unwrap(),
        r#"{"skill": "au-payroll-review"}"#
    ));
}

#[test]
fn routing_names_that_are_not_slugs_and_untyped_fields_are_refused() {
    for case in [
        serde_json::json!({"id": "../escape", "skill": "bas-preparation", "not": [], "prompt": "p"}),
        serde_json::json!({"id": "x", "skill": "bas preparation", "not": [], "prompt": "p"}),
        serde_json::json!({"id": "x", "skill": "bas-preparation", "not": ["../a"], "prompt": "p"}),
        serde_json::json!({"id": "x", "skill": "bas-preparation", "not": "a", "prompt": "p"}),
        serde_json::json!({"id": "x", "skill": "bas-preparation", "not": [], "prompt": 0}),
        serde_json::json!({"skill": "bas-preparation", "not": [], "prompt": "p"}),
    ] {
        assert!(build_routing_case(&case, 1, 12).is_err(), "{case}");
    }
}

#[test]
fn a_card_without_withheld_sections_is_refused() {
    let card = "---\nid: x\nsynthetic: true\ntarget_skills:\n  - bas-preparation\n---\n\n# X\n\n## Task\n\nDo it.\n";
    let error = build_case(card, "x", 1, 12).unwrap_err().to_string();
    assert!(error.contains("missing section"), "{error}");
}

#[test]
fn a_card_with_a_repeated_section_is_refused() {
    let card = "---\nid: x\nsynthetic: true\ntarget_skills:\n  - bas-preparation\n---\n\n# X\n\n## Task\n\nA.\n\n## Task\n\nB.\n";
    let error = build_case(card, "x", 1, 12).unwrap_err().to_string();
    assert!(error.contains("duplicate section: Task"), "{error}");
}

#[test]
fn front_matter_round_trips_quotes_breaks_and_document_markers() {
    let checks = "- Say \"yes\" or 'no', C:\\path\tand # not a comment: x\n---\n- NEL\u{85}LS\u{2028}PS\u{2029}BOM\u{feff}DEL\u{7f}𝄞é\n  - nested";
    let card = format!(
        "---\nid: x\nsynthetic: true\ntarget_skills: [bas-preparation]\n---\n## Task\n\nDo it.\n\n## Required checks\n\n{checks}\n\n## Must not do\n\n- Nothing.\n\n## Source-verification and reviewer boundary\n\nNone.\n"
    );
    let files = build_case(&card, "x", 1, 12).unwrap();
    let criteria = front(&files, "graders/required-checks.md")["criteria"]
        .as_str()
        .unwrap()
        .to_owned();
    assert!(criteria.ends_with(&format!("FAIL if it misses any.\n\n{checks}\n")));
    for (name, text) in &files {
        let header = &text[..text[4..].find("\n---\n").unwrap() + 4];
        assert!(
            header
                .chars()
                .all(|c| c == '\n' || (' '..='~').contains(&c) || c == 'é' || c == '𝄞'),
            "{name}: {header}"
        );
    }
}

fn fixture(root: &Path) {
    for (path, text) in [
        (".claude-plugin/plugin.json", "{}\n"),
        (
            ".claude/skills/bas-preparation/SKILL.md",
            "Fabricated skill\n",
        ),
        (
            ".claude/skills/bas-preparation/references/guide.md",
            "Fabricated guide\n",
        ),
        (
            ".claude/rules/rule.md",
            "Fabricated rule, shelved in the Croft Manor library\n",
        ),
        ("DISCLAIMER.md", "Fabricated disclaimer\n"),
        ("LICENSE", "Fabricated licence\n"),
        (".gitignore", "*.draft\n"),
        ("tests/test_x.py", "fabricated\n"),
        (
            "validation/cases/x.md",
            "---\nid: x\nsynthetic: true\ntarget_skills: [bas-preparation]\n---\n## Task\n\nDo it.\n\n## Required checks\n\n- Check.\n\n## Must not do\n\n- Nothing.\n\n## Source-verification and reviewer boundary\n\nNone.\n",
        ),
        (
            "validation/routing-cases.yaml",
            "- id: payroll\n  skill: bas-preparation\n  not: [au-payroll-review]\n  prompt: A synthetic prompt.\n",
        ),
    ] {
        let path = root.join(path);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, text).unwrap();
    }
    git(root, &["init", "-q"]);
    commit(root, "Fixture");
}

fn git(root: &Path, args: &[&str]) {
    let output = Command::new("git")
        .args(args)
        .current_dir(root)
        .output()
        .unwrap();
    assert!(output.status.success(), "{args:?}: {output:?}");
}

fn commit(root: &Path, message: &str) {
    git(root, &["add", "--all"]);
    git(
        root,
        &[
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "--no-verify",
            "--allow-empty",
            "-m",
            message,
        ],
    );
}

#[test]
fn the_manifest_names_the_commit_and_flags_uncommitted_plugin_files() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    fixture(root.path());
    let clean = build(&outside.path().join("clean"), 1, 12, root.path(), None).unwrap();
    assert_eq!(clean["commit"].as_str().unwrap().len(), 40, "{clean}");
    assert_eq!(clean["dirty"], false);
    // Cards stay behind, so an uncommitted card leaves the copy as committed.
    fs::write(root.path().join("validation/cases/notes.txt"), "draft\n").unwrap();
    let card = build(&outside.path().join("card"), 1, 12, root.path(), None).unwrap();
    assert_eq!(card["dirty"], false);
    for (name, path) in [
        ("edited", ".claude/skills/bas-preparation/SKILL.md"),
        ("untracked", ".claude/rules/new.md"),
        ("ignored", ".claude/skills/bas-preparation/notes.draft"),
    ] {
        fs::write(root.path().join(path), "Uncommitted\n").unwrap();
        let manifest = build(&outside.path().join(name), 1, 12, root.path(), None).unwrap();
        assert_eq!(manifest["dirty"], true, "{name}");
        commit(root.path(), name);
    }
}

#[test]
fn a_root_outside_git_is_refused_before_anything_is_written() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    fixture(root.path());
    fs::remove_dir_all(root.path().join(".git")).unwrap();
    let target = outside.path().join("plugin");
    let error = build(&target, 1, 12, root.path(), None).unwrap_err();
    assert!(
        error.to_string().contains("git rev-parse HEAD failed"),
        "{error}"
    );
    assert!(!target.exists());
}

#[test]
fn changed_since_builds_only_the_cases_grading_a_changed_skill() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    fixture(root.path());
    let card = fs::read_to_string(root.path().join("validation/cases/x.md")).unwrap();
    for (path, text) in [
        (
            ".claude/skills/au-payroll-review/SKILL.md".to_owned(),
            "Fabricated skill\n".to_owned(),
        ),
        (
            "validation/cases/y.md".to_owned(),
            card.replace("id: x", "id: y")
                .replace("[bas-preparation]", "[au-payroll-review]"),
        ),
        (
            "validation/routing-cases.yaml".to_owned(),
            "- id: bas\n  skill: bas-preparation\n  not: []\n  prompt: A synthetic prompt.\n\
             - id: payroll\n  skill: au-payroll-review\n  not: []\n  prompt: Another synthetic prompt.\n\
             - id: wages\n  skill: bas-preparation\n  not: [au-payroll-review]\n  prompt: A third synthetic prompt.\n"
                .to_owned(),
        ),
    ] {
        let path = root.path().join(path);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, text).unwrap();
    }
    commit(root.path(), "Second skill");
    let error = build(
        &outside.path().join("none"),
        1,
        12,
        root.path(),
        Some("HEAD"),
    )
    .unwrap_err();
    assert!(error.to_string().contains("no case grades"), "{error}");
    let target = outside.path().join("unknown");
    let error = build(&target, 1, 12, root.path(), Some("no-such-revision")).unwrap_err();
    assert!(error.to_string().contains("unknown revision"), "{error}");
    assert!(!target.exists());

    fs::write(
        root.path()
            .join(".claude/skills/au-payroll-review/SKILL.md"),
        "Reworded skill\n",
    )
    .unwrap();
    let target = outside.path().join("plugin");
    let output = run(&[
        target.as_os_str(),
        "--root".as_ref(),
        root.path().as_os_str(),
        "--changed-since".as_ref(),
        "HEAD".as_ref(),
    ]);
    assert_eq!(output.status.code(), Some(0), "{output:?}");
    let mut cases: Vec<_> = fs::read_dir(target.join("evals"))
        .unwrap()
        .map(|entry| entry.unwrap().file_name().into_string().unwrap())
        .collect();
    cases.sort();
    assert_eq!(cases, ["route-payroll", "route-wages", "y"]);
    let manifest: serde_json::Value =
        serde_json::from_slice(&fs::read(target.join("evals-manifest.json")).unwrap()).unwrap();
    assert_eq!(
        manifest["card_sha256"]
            .as_object()
            .unwrap()
            .keys()
            .collect::<Vec<_>>(),
        ["y"]
    );
    assert_eq!(manifest["changed_since"].as_str().unwrap().len(), 40);
}

#[test]
fn the_built_copy_leaves_the_cards_and_tests_behind() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    fixture(root.path());
    let target = outside.path().join("plugin");
    let manifest = build(&target, 1, 12, root.path(), None).unwrap();
    assert!(!target.join("validation").exists());
    assert!(!target.join("tests").exists());
    for copied in [
        ".claude-plugin/plugin.json",
        ".claude/skills/bas-preparation/references/guide.md",
        ".claude/rules/rule.md",
        "DISCLAIMER.md",
        "LICENSE",
    ] {
        assert_eq!(
            fs::read(target.join(copied)).unwrap(),
            fs::read(root.path().join(copied)).unwrap()
        );
    }
    let mut cases: Vec<_> = fs::read_dir(target.join("evals"))
        .unwrap()
        .map(|entry| entry.unwrap().file_name().into_string().unwrap())
        .collect();
    cases.sort();
    assert_eq!(cases, ["route-payroll", "x"]);
    assert_eq!(
        manifest["routing_cases"],
        serde_json::json!(["route-payroll"])
    );
    assert_eq!(
        manifest["card_sha256"]["x"].as_str().unwrap().len(),
        64,
        "{manifest}"
    );
    let saved: serde_json::Value =
        serde_json::from_slice(&fs::read(target.join("evals-manifest.json")).unwrap()).unwrap();
    assert_eq!(saved, manifest);
    assert!(
        target
            .join("evals/route-payroll/graders/not-au-payroll-review.md")
            .is_file()
    );
}

#[test]
fn build_refuses_the_repository_an_existing_destination_and_a_malformed_card() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    fixture(root.path());
    let error = build(&root.path().join("build-here"), 1, 12, root.path(), None).unwrap_err();
    assert!(
        error.to_string().contains("outside the repository"),
        "{error}"
    );
    let error = build(outside.path(), 1, 12, root.path(), None).unwrap_err();
    assert!(error.to_string().contains("already exists"), "{error}");
    fs::write(
        root.path().join("validation/cases/x.md"),
        "---\nid: x\nsynthetic: true\ntarget_skills: [bas-preparation]\n---\n## Task\n\nDo it.\n",
    )
    .unwrap();
    let target = outside.path().join("plugin");
    assert!(build(&target, 1, 12, root.path(), None).is_err());
    assert!(!target.exists());
}

#[test]
fn routing_cases_refuse_yaml_aliases_and_duplicate_keys() {
    let outside = tempfile::tempdir().unwrap();
    for (routing, refusal) in [
        (
            "- id: payroll\n  skill: bas-preparation\n  not: &others [au-payroll-review]\n  prompt: A synthetic prompt.\n- id: other\n  skill: bas-preparation\n  not: *others\n  prompt: Another synthetic prompt.\n",
            "aliases",
        ),
        (
            "- id: payroll\n  skill: bas-preparation\n  skill: au-payroll-review\n  not: [au-close]\n  prompt: A synthetic prompt.\n",
            "duplicate",
        ),
    ] {
        let root = tempfile::tempdir().unwrap();
        fixture(root.path());
        fs::write(root.path().join("validation/routing-cases.yaml"), routing).unwrap();
        let target = outside.path().join("plugin");
        let error = build(&target, 1, 12, root.path(), None).unwrap_err();
        assert!(error.to_string().contains(refusal), "{error}");
        assert!(!target.exists());
    }
}

#[cfg(any(unix, windows))]
#[test]
fn linked_plugin_files_are_refused() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    fixture(root.path());
    let linked = outside.path().join("linked");
    fs::create_dir(&linked).unwrap();
    // mklink needs native separators.
    let link = root
        .path()
        .join(".claude")
        .join("skills")
        .join("bas-preparation")
        .join("linked");
    link_folder(&linked, &link);
    let error = build(&outside.path().join("plugin"), 1, 12, root.path(), None).unwrap_err();
    assert!(error.to_string().contains("symbolic links"), "{error}");
    #[cfg(windows)]
    fs::remove_dir(link).unwrap();
}

#[test]
fn a_linked_folder_above_a_plugin_path_is_refused() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    fixture(root.path());
    let moved = outside.path().join("claude");
    fs::rename(root.path().join(".claude"), &moved).unwrap();
    let link = root.path().join(".claude");
    link_folder(&moved, &link);
    let error = build(&outside.path().join("plugin"), 1, 12, root.path(), None).unwrap_err();
    assert!(error.to_string().contains("symbolic links"), "{error}");
    #[cfg(windows)]
    fs::remove_dir(link).unwrap();
}

/// A symbolic link on Unix and a junction on Windows, which needs no privilege.
fn link_folder(target: &Path, link: &Path) {
    #[cfg(unix)]
    std::os::unix::fs::symlink(target, link).unwrap();
    #[cfg(windows)]
    assert!(
        Command::new("cmd")
            .args(["/c", "mklink", "/J"])
            .arg(link)
            .arg(target)
            .output()
            .unwrap()
            .status
            .success()
    );
}

fn run(args: &[&std::ffi::OsStr]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .arg("build-plugin-evals")
        .args(args)
        .output()
        .unwrap()
}

#[test]
fn the_command_builds_every_case_and_reports_the_count() {
    let outside = tempfile::tempdir().unwrap();
    let target = outside.path().join("plugin");
    let repository = repository();
    let output = run(&[
        target.as_os_str(),
        "--runs".as_ref(),
        "2".as_ref(),
        "--root".as_ref(),
        repository.as_os_str(),
    ]);
    assert_eq!(output.status.code(), Some(0), "{output:?}");
    let cases: Vec<_> = fs::read_dir(target.join("evals"))
        .unwrap()
        .map(|entry| entry.unwrap().path().join("prompt.md"))
        .collect();
    assert!(cases.len() > cards().len());
    let stdout = String::from_utf8(output.stdout).unwrap();
    assert!(
        stdout.starts_with(&format!("built {} cases (", cases.len())),
        "{stdout}"
    );
    assert!(
        fs::read_to_string(&cases[0])
            .unwrap()
            .contains("\nruns: 2\n")
    );
}

#[test]
fn the_command_refuses_bad_options_with_usage() {
    let outside = tempfile::tempdir().unwrap();
    let target = outside.path().join("plugin");
    for args in [
        vec![],
        vec![target.as_os_str(), "--runs".as_ref(), "0".as_ref()],
        vec![target.as_os_str(), "--max-turns".as_ref(), "-1".as_ref()],
        vec![target.as_os_str(), "--runs".as_ref()],
        vec![target.as_os_str(), "--other".as_ref()],
        vec![target.as_os_str(), target.as_os_str()],
    ] {
        let output = run(&args);
        assert_eq!(output.status.code(), Some(2), "{args:?}");
        assert!(String::from_utf8_lossy(&output.stderr).starts_with("usage:"));
    }
    assert!(!target.exists());
}
