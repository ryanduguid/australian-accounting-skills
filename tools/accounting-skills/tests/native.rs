use accounting_skills::{front_matter, rendered};
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
    assert!(front_matter(&file).is_err());
    fs::write(&file, "bad\n---").unwrap();
    assert!(front_matter(&file).is_err());
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
    assert_eq!(fs::read_dir(root.path()).unwrap().count(), 1);
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
