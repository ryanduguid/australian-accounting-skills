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
