// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use accounting_skills::{front_matter, rendered, rendered_with_page};
use std::{fs, process::Command};

#[test]
fn inventory_distinguishes_sources_cards_and_quoted_gate_mentions() {
    let root = tempfile::tempdir().unwrap();
    for skill in ["alpha", "beta"] {
        let folder = root.path().join(".claude/skills").join(skill);
        fs::create_dir_all(&folder).unwrap();
        fs::write(folder.join("SKILL.md"), "ignored by coverage builder").unwrap();
    }
    fs::create_dir_all(root.path().join("validation/cases")).unwrap();
    fs::write(
        root.path()
            .join("validation/cases/alpha-missing-evidence.md"),
        "---\n- alpha\n- alpha\n---\n",
    )
    .unwrap();
    fs::create_dir(root.path().join("tests")).unwrap();
    fs::write(root.path().join("tests/gate.py"), "'alpha\" and beta").unwrap();
    let source = root.path().join(".claude/skills/alpha/sources.json");
    fs::write(source, r#"{"sources":[{"checked_at":"2026-01-02","fetched_at":"2026-10-22","source_last_modified":"2026-10-01","url":"évidence","http_status":503},{"checked_at":"2025-12-31","fetched_at":"2026-10-23","http_status":503,"manual_review":{}},null]}"#).unwrap();
    let matrix: serde_json::Value = serde_json::from_str(&rendered(root.path()).unwrap()).unwrap();
    assert_eq!(matrix["totals"]["skills"], 2);
    let alpha = &matrix["skills"][0];
    assert_eq!(alpha["sources"]["reviewed"], "2025-12-31");
    assert_eq!(alpha["sources"]["fetched"], "2026-10-22");
    assert_eq!(alpha["sources"]["unreachable"], 1);
    assert_eq!(alpha["sources"]["moved_since_review"][0], "évidence");
    assert_eq!(alpha["validation"]["cases"], 1);
    assert_eq!(alpha["validation"]["only_seeded_case"], true);
    assert_eq!(alpha["gates"]["behavioural"][0], "gate.py");
    assert_eq!(
        matrix["skills"][1]["gates"]["behavioural"],
        serde_json::json!([])
    );
}

#[test]
fn frontmatter_preserves_python_line_boundaries_and_refuses_missing_markers() {
    let root = tempfile::tempdir().unwrap();
    let file = root.path().join("card.md");
    fs::write(&file, "---\u{85}x\u{2028}---\nbody").unwrap();
    assert_eq!(front_matter(&file).unwrap(), "x");
    fs::write(&file, "---\nmissing end").unwrap();
    assert_eq!(
        front_matter(&file).unwrap_err().to_string(),
        "card.md: front matter must end with '---'"
    );
    fs::write(&file, "bad\n---").unwrap();
    assert_eq!(
        front_matter(&file).unwrap_err().to_string(),
        "card.md: front matter must start with '---'"
    );
}

#[test]
fn check_write_and_print_report_on_the_expected_streams() {
    let root = tempfile::tempdir().unwrap();
    let run = |flag: &str| {
        Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
            .args(["build-coverage", flag])
            .current_dir(root.path())
            .output()
            .unwrap()
    };
    let text = |bytes: Vec<u8>| String::from_utf8(bytes).unwrap().replace("\r\n", "\n");
    let matrix = rendered(root.path()).unwrap();
    let stale = run("--check");
    assert_eq!(stale.status.code(), Some(2));
    assert!(stale.stdout.is_empty());
    assert_eq!(
        text(stale.stderr),
        "coverage.json is out of date. Run: cargo run --locked --manifest-path tools/accounting-skills/Cargo.toml -- build-coverage --write\n\
         docs/skill-verification.md is out of date. Run: cargo run --locked --manifest-path tools/accounting-skills/Cargo.toml -- build-coverage --write\n"
    );
    let written = run("--write");
    assert_eq!(
        (
            written.status.code(),
            text(written.stdout),
            text(written.stderr)
        ),
        (
            Some(0),
            "wrote coverage.json and docs/skill-verification.md\n".to_owned(),
            String::new()
        )
    );
    assert_eq!(
        fs::read_to_string(root.path().join("coverage.json"))
            .unwrap()
            .replace("\r\n", "\n"),
        matrix
    );
    let current = run("--check");
    assert_eq!(
        (
            current.status.code(),
            text(current.stdout),
            text(current.stderr)
        ),
        (Some(0), matrix, String::new())
    );
}

#[test]
fn overlapping_quoted_names_count_as_mentions() {
    let root = tempfile::tempdir().unwrap();
    let folder = root.path().join(".claude/skills/''");
    fs::create_dir_all(&folder).unwrap();
    fs::write(folder.join("SKILL.md"), "not parsed").unwrap();
    fs::create_dir(root.path().join("tests")).unwrap();
    fs::write(root.path().join("tests/gate.py"), "''''").unwrap();
    let matrix: serde_json::Value = serde_json::from_str(&rendered(root.path()).unwrap()).unwrap();
    assert_eq!(
        matrix["skills"][0]["gates"]["behavioural"],
        serde_json::json!(["gate.py"])
    );
}

#[test]
fn write_replaces_a_hard_link_without_changing_its_other_name() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    let sentinel = outside.path().join("sentinel");
    fs::write(&sentinel, "keep").unwrap();
    fs::hard_link(&sentinel, root.path().join("coverage.json")).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args(["build-coverage", "--write"])
        .current_dir(root.path())
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(0));
    assert_eq!(fs::read_to_string(&sentinel).unwrap(), "keep");
    assert!(
        fs::read_to_string(root.path().join("coverage.json"))
            .unwrap()
            .contains("schema_version")
    );
    let mut names: Vec<_> = fs::read_dir(root.path())
        .unwrap()
        .map(|entry| entry.unwrap().file_name())
        .collect();
    names.sort();
    assert_eq!(names, ["coverage.json", "docs"]);
}

#[test]
fn malformed_source_records_are_refused_before_writing() {
    let root = tempfile::tempdir().unwrap();
    let folder = root.path().join(".claude/skills/alpha");
    fs::create_dir_all(&folder).unwrap();
    fs::write(folder.join("SKILL.md"), "not parsed").unwrap();
    fs::write(root.path().join("coverage.json"), "previous").unwrap();
    for index in [
        "[]",
        r#"{"sources": {}}"#,
        r#"{"sources": [{"checked_at": 1}]}"#,
        r#"{"sources": [{"checked_at": "2026-01-01", "fetched_at": null}]}"#,
        r#"{"sources": [{"checked_at": "2026-01-01", "source_last_modified": "2026-02-01", "url": 1}]}"#,
    ] {
        fs::write(folder.join("sources.json"), index).unwrap();
        let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
            .args(["build-coverage", "--write"])
            .current_dir(root.path())
            .output()
            .unwrap();
        assert_eq!(output.status.code(), Some(1), "{index}");
        assert!(output.stdout.is_empty(), "{index}");
        assert_eq!(
            fs::read_to_string(root.path().join("coverage.json")).unwrap(),
            "previous"
        );
    }
}

#[cfg(unix)]
#[test]
fn write_refuses_a_symlinked_coverage_file() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    let sentinel = outside.path().join("sentinel");
    fs::write(&sentinel, "keep").unwrap();
    std::os::unix::fs::symlink(&sentinel, root.path().join("coverage.json")).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args(["build-coverage", "--write"])
        .current_dir(root.path())
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(1));
    assert!(output.stdout.is_empty());
    assert_eq!(fs::read_to_string(&sentinel).unwrap(), "keep");
}

#[test]
fn check_refuses_stale_output_and_write_wins_over_check() {
    let root = tempfile::tempdir().unwrap();
    let run = |args: &[&str]| {
        Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
            .arg("build-coverage")
            .args(args)
            .current_dir(root.path())
            .output()
            .unwrap()
    };
    assert_eq!(run(&["--check"]).status.code(), Some(2));
    assert_eq!(run(&["--write", "--check"]).status.code(), Some(0));
    assert_eq!(run(&["--check"]).status.code(), Some(0));
    fs::write(root.path().join("coverage.json"), "stale").unwrap();
    assert_eq!(run(&["--check"]).status.code(), Some(2));
    assert!(!run(&["--root", "--check"]).status.success());
}

/// Two skills, 3 cards and one source index, with confirmed, observed and
/// legacy result records.
fn verified_tree() -> tempfile::TempDir {
    let root = tempfile::tempdir().unwrap();
    for skill in ["alpha", "beta"] {
        let folder = root.path().join(".claude/skills").join(skill);
        fs::create_dir_all(&folder).unwrap();
        fs::write(folder.join("SKILL.md"), "not parsed").unwrap();
    }
    fs::write(
        root.path().join(".claude/skills/beta/sources.exempt.json"),
        "{}",
    )
    .unwrap();
    fs::write(
        root.path().join(".claude/skills/alpha/sources.json"),
        r#"{"sources":[{"checked_at":"2026-03-01","http_status":200},{"checked_at":"2026-02-01","http_status":404}]}"#,
    )
    .unwrap();
    let cases = root.path().join("validation/cases");
    fs::create_dir_all(&cases).unwrap();
    for (card, targets) in [
        ("alpha-one", "- alpha"),
        ("alpha-two", "- alpha"),
        ("shared", "- alpha\n- beta"),
    ] {
        fs::write(
            cases.join(format!("{card}.md")),
            format!("---\n{targets}\n---\n"),
        )
        .unwrap();
    }
    let results = root.path().join("validation/results");
    fs::create_dir_all(&results).unwrap();
    for (file, record) in [
        (
            "confirmed.json",
            r#"{"status":"confirmed","results":{"alpha-one":"pass","shared":"fail"}}"#,
        ),
        (
            "rerun-confirmed.json",
            r#"{"status":"confirmed","results":{"shared":"pass"}}"#,
        ),
        ("observed.json", r#"{"status":"observed","results":{}}"#),
        ("legacy.json", r#"{"results":{"alpha-two":"pass"}}"#),
    ] {
        fs::write(results.join(file), record).unwrap();
    }
    root
}

#[test]
fn confirmed_verdicts_count_only_human_confirmed_records() {
    let root = verified_tree();
    let matrix: serde_json::Value = serde_json::from_str(&rendered(root.path()).unwrap()).unwrap();
    let alpha = &matrix["skills"][0]["validation"];
    assert_eq!(
        alpha["confirmed_pass"],
        serde_json::json!(["alpha-one", "shared"])
    );
    assert_eq!(alpha["confirmed_fail"], serde_json::json!(["shared"]));
    let beta = &matrix["skills"][1]["validation"];
    assert_eq!(beta["confirmed_pass"], serde_json::json!(["shared"]));
    assert_eq!(beta["confirmed_fail"], serde_json::json!(["shared"]));
    assert_eq!(matrix["totals"]["skills_with_confirmed_pass"], 2);
    assert_eq!(matrix["totals"]["skills_with_confirmed_fail"], 2);
}

#[test]
fn verification_page_states_the_matrix_totals_and_one_row_per_skill() {
    let root = verified_tree();
    let (_, page) = rendered_with_page(root.path()).unwrap();
    assert!(page.contains(
        "Totals: 2 skills, 2 indexed primary sources, 1 skills exempt from source indexing, \
         1 skills with an unreachable source, 0 skills with a source changed since review, \
         2 skills with a confirmed pass and 2 skills with a confirmed fail.\n"
    ));
    assert!(page.contains(
        "| [`alpha`](../.claude/skills/alpha/SKILL.md) | [2](../.claude/skills/alpha/sources.json) \
         | 2026-02-01 | 1 | 0 | 3 | 2 | 1 |\n"
    ));
    assert!(page.contains(
        "| [`beta`](../.claude/skills/beta/SKILL.md) | exempt | none | 0 | 0 | 1 | 1 | 1 |\n"
    ));
}

#[test]
fn malformed_or_orphaned_confirmed_verdicts_are_refused() {
    for record in [
        r#"{"status":"confirmed","results":{"alpha-one":"passed"}}"#,
        r#"{"status":"confirmed","results":[]}"#,
        r#"{"status":"confirmed","results":{"retired-card":"pass"}}"#,
    ] {
        let root = verified_tree();
        fs::write(root.path().join("validation/results/bad.json"), record).unwrap();
        assert!(rendered(root.path()).is_err(), "{record}");
    }
}

#[test]
fn check_fails_when_a_source_record_changes_and_the_page_does_not() {
    let root = verified_tree();
    let run = |flag: &str| {
        Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
            .args(["build-coverage", flag])
            .current_dir(root.path())
            .output()
            .unwrap()
    };
    assert_eq!(run("--write").status.code(), Some(0));
    let index = root.path().join(".claude/skills/alpha/sources.json");
    let text = fs::read_to_string(&index).unwrap();
    fs::write(&index, text.replace("2026-02-01", "2026-04-01")).unwrap();
    // Rebuild coverage.json alone, as a hand edit or a partial tool would.
    fs::write(
        root.path().join("coverage.json"),
        rendered(root.path()).unwrap(),
    )
    .unwrap();
    let stale = run("--check");
    assert_eq!(stale.status.code(), Some(2));
    let message = String::from_utf8(stale.stderr).unwrap();
    assert!(
        message.starts_with("docs/skill-verification.md is out of date."),
        "{message}"
    );
}
