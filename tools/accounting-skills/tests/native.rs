// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use accounting_skills::{
    canonical_root, front_matter, rendered, rendered_with_page, trial::digest, within_root,
};
use std::{fs, path::Path, process::Command};

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
        r#"{"sources": {}, "sources": []}"#,
        r#"{"sources": [{"checked_at": 1, "checked_at": "2026-01-01"}]}"#,
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

/// Two skills, 4 cards and one source index, with confirmed, observed and
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
        r#"{"sources":[{"checked_at":"2026-03-01","http_status":200},{"checked_at":"2026-02-01","http_status":404},{"http_status":200}]}"#,
    )
    .unwrap();
    let cases = root.path().join("validation/cases");
    fs::create_dir_all(&cases).unwrap();
    for (card, targets) in [
        ("alpha-one", "- alpha"),
        ("alpha-two", "- alpha"),
        ("shared", "- alpha\n- beta"),
        ("beta-revised", "- beta"),
    ] {
        fs::write(
            cases.join(format!("{card}.md")),
            format!("---\n{targets}\n---\n"),
        )
        .unwrap();
    }
    let results = root.path().join("validation/results");
    fs::create_dir_all(&results).unwrap();
    let confirmed = confirmed_record(root.path(), &[("alpha-one", "pass"), ("shared", "fail")]);
    let mut revised = confirmed_record(root.path(), &[("beta-revised", "pass")]);
    revised["provenance"]["beta-revised"]["rubric_sha256"] = serde_json::json!(digest(b"earlier"));
    for (file, record) in [
        ("confirmed.json", confirmed.to_string()),
        ("revised-confirmed.json", revised.to_string()),
        (
            "observed.json",
            r#"{"status":"observed","results":{}}"#.to_owned(),
        ),
        (
            "legacy.json",
            r#"{"results":{"alpha-two":"fail","alpha-one":"pass"}}"#.to_owned(),
        ),
    ] {
        fs::write(results.join(file), record).unwrap();
    }
    root
}

/// A confirmed record whose rubric digests match the cards as they are now.
fn confirmed_record(root: &std::path::Path, verdicts: &[(&str, &str)]) -> serde_json::Value {
    let mut results = serde_json::Map::new();
    let mut provenance = serde_json::Map::new();
    for (card, verdict) in verdicts {
        let bytes = fs::read(root.join(format!("validation/cases/{card}.md"))).unwrap();
        results.insert((*card).to_owned(), serde_json::json!(verdict));
        provenance.insert(
            (*card).to_owned(),
            serde_json::json!({"rubric_sha256": digest(&bytes)}),
        );
    }
    serde_json::json!({"status": "confirmed", "results": results, "provenance": provenance})
}

#[test]
fn confirmed_verdicts_count_only_for_the_current_card() {
    let root = verified_tree();
    let matrix: serde_json::Value = serde_json::from_str(&rendered(root.path()).unwrap()).unwrap();
    let alpha = &matrix["skills"][0];
    assert_eq!(
        alpha["validation"]["confirmed_pass"],
        serde_json::json!(["alpha-one"])
    );
    assert_eq!(
        alpha["validation"]["confirmed_fail"],
        serde_json::json!(["shared"])
    );
    assert_eq!(alpha["sources"]["reviewed_count"], 2);
    let beta = &matrix["skills"][1]["validation"];
    assert_eq!(beta["confirmed_pass"], serde_json::json!([]));
    assert_eq!(beta["confirmed_fail"], serde_json::json!(["shared"]));
    assert_eq!(
        beta["confirmed_noncurrent_digest"],
        serde_json::json!(["beta-revised"])
    );
    assert_eq!(matrix["totals"]["skills_with_confirmed_pass"], 1);
    assert_eq!(matrix["totals"]["skills_with_confirmed_fail"], 2);
    assert_eq!(
        matrix["totals"]["skills_with_confirmed_noncurrent_digest"],
        1
    );
    assert_eq!(matrix["totals"]["sources_reviewed"], 2);
}

/// The fixture confirms `beta-revised` as a pass under a well-formed digest
/// that matches no version of the card; this adds a verdict on the current card.
fn rerun_beta_revised(verdict: &str) -> serde_json::Value {
    let root = verified_tree();
    let rerun = confirmed_record(root.path(), &[("beta-revised", verdict)]);
    fs::write(
        root.path().join("validation/results/rerun-confirmed.json"),
        rerun.to_string(),
    )
    .unwrap();
    let matrix: serde_json::Value = serde_json::from_str(&rendered(root.path()).unwrap()).unwrap();
    matrix["skills"][1]["validation"].clone()
}

#[test]
fn a_current_pass_counts_and_the_earlier_verdict_stays_listed() {
    let beta = rerun_beta_revised("pass");
    assert_eq!(beta["confirmed_pass"], serde_json::json!(["beta-revised"]));
    assert_eq!(
        beta["confirmed_noncurrent_digest"],
        serde_json::json!(["beta-revised"])
    );
}

#[test]
fn a_fail_on_the_current_card_after_a_pass_on_an_earlier_one_is_not_a_conflict() {
    let beta = rerun_beta_revised("fail");
    assert_eq!(beta["confirmed_pass"], serde_json::json!([]));
    assert_eq!(
        beta["confirmed_fail"],
        serde_json::json!(["beta-revised", "shared"])
    );
    assert_eq!(
        beta["confirmed_noncurrent_digest"],
        serde_json::json!(["beta-revised"])
    );
}

#[test]
fn verification_page_states_the_matrix_totals_and_one_row_per_skill() {
    let root = verified_tree();
    let (_, page) = rendered_with_page(root.path()).unwrap();
    assert!(page.contains(
        "Totals: 2 skills, 3 indexed primary sources of which 2 have a recorded human review, \
         1 skills exempt from source indexing, 1 skills with an unreachable source, \
         0 skills with a source changed since review, 1 skills with a confirmed pass, \
         2 skills with a confirmed fail and 1 skills with a confirmed verdict whose rubric \
         digest does not match the current card.\n"
    ));
    assert!(page.contains("| Confirmed pass | Confirmed fail | Non-current digest |\n"));
    assert!(page.contains("not of runs"), "{page}");
    assert!(page.contains(
        "| [`alpha`](../.claude/skills/alpha/SKILL.md) | [3](../.claude/skills/alpha/sources.json) \
         | 2026-02-01 (2 of 3) | 1 | 0 | 3 | 1 | 1 | 0 |\n"
    ));
    assert!(page.contains(
        "| [`beta`](../.claude/skills/beta/SKILL.md) | exempt | none | 0 | 0 | 2 | 0 | 1 | 1 |\n"
    ));
    assert!(page.contains("`legacy.json`"), "{page}");
    assert!(page.contains("`alpha-two` (`legacy.json`)"), "{page}");
    assert!(
        page.contains("passed the card's rubric on one run"),
        "{page}"
    );
}

#[test]
fn malformed_or_orphaned_confirmed_verdicts_are_refused() {
    for record in [
        r#"{"status":"confirmed","results":{"alpha-one":"passed"},"provenance":{}}"#,
        r#"{"status":"confirmed","results":[]}"#,
        r#"{"status":"confirmed","results":{"retired-card":"pass"},"provenance":{}}"#,
        r#"{"status":"confirmed","results":{"alpha-one":"pass"},"provenance":{}}"#,
        r#"{"results":{"alpha-one":"maybe"}}"#,
    ] {
        let root = verified_tree();
        fs::write(root.path().join("validation/results/bad.json"), record).unwrap();
        assert!(rendered(root.path()).is_err(), "{record}");
    }
}

#[test]
fn a_null_non_string_or_unknown_status_is_refused() {
    for status in [
        serde_json::Value::Null,
        serde_json::json!(1),
        serde_json::json!("confimed"),
    ] {
        let root = verified_tree();
        let mut record = confirmed_record(root.path(), &[("alpha-two", "pass")]);
        record["status"] = status.clone();
        fs::write(
            root.path().join("validation/results/bad.json"),
            record.to_string(),
        )
        .unwrap();
        let error = rendered(root.path()).unwrap_err().to_string();
        assert!(error.contains("bad.json"), "{status}: {error}");
    }
}

#[test]
fn an_observed_record_stays_out_of_the_counts() {
    let root = verified_tree();
    let mut record = confirmed_record(root.path(), &[("alpha-two", "pass")]);
    record["status"] = serde_json::json!("observed");
    fs::write(
        root.path().join("validation/results/observed-verdict.json"),
        record.to_string(),
    )
    .unwrap();
    let matrix: serde_json::Value = serde_json::from_str(&rendered(root.path()).unwrap()).unwrap();
    assert_eq!(
        matrix["skills"][0]["validation"]["confirmed_pass"],
        serde_json::json!(["alpha-one"])
    );
}

#[test]
fn a_malformed_rubric_digest_is_refused() {
    let upper = digest(b"earlier").to_uppercase();
    for bad in ["abc", upper.as_str(), &"g".repeat(64)] {
        let root = verified_tree();
        let mut record = confirmed_record(root.path(), &[("alpha-two", "pass")]);
        record["provenance"]["alpha-two"]["rubric_sha256"] = serde_json::json!(bad);
        fs::write(
            root.path().join("validation/results/bad.json"),
            record.to_string(),
        )
        .unwrap();
        let error = rendered(root.path()).unwrap_err().to_string();
        assert!(error.contains("rubric_sha256"), "{bad}: {error}");
    }
}

#[test]
fn a_well_formed_unknown_digest_is_only_called_non_current() {
    let root = verified_tree();
    let mut record = confirmed_record(root.path(), &[("alpha-two", "fail")]);
    record["provenance"]["alpha-two"]["rubric_sha256"] = serde_json::json!("0".repeat(64));
    fs::write(
        root.path().join("validation/results/unknown.json"),
        record.to_string(),
    )
    .unwrap();
    let matrix: serde_json::Value = serde_json::from_str(&rendered(root.path()).unwrap()).unwrap();
    let alpha = &matrix["skills"][0]["validation"];
    assert_eq!(alpha["confirmed_fail"], serde_json::json!(["shared"]));
    assert_eq!(
        alpha["confirmed_noncurrent_digest"],
        serde_json::json!(["alpha-two"])
    );
}

#[test]
fn a_card_confirmed_both_pass_and_fail_is_refused() {
    let root = verified_tree();
    let conflict = confirmed_record(root.path(), &[("shared", "pass")]);
    fs::write(
        root.path().join("validation/results/conflict.json"),
        conflict.to_string(),
    )
    .unwrap();
    let error = rendered(root.path()).unwrap_err().to_string();
    for part in ["shared", "confirmed.json", "conflict.json"] {
        assert!(error.contains(part), "{error}");
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

#[cfg(unix)]
fn coverage(root: &Path, args: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .arg("build-coverage")
        .args(args)
        .current_dir(root)
        .output()
        .unwrap()
}

#[test]
fn an_output_relative_path_cannot_climb_out_of_the_root() {
    let root = tempfile::tempdir().unwrap();
    let error = within_root(root.path(), Path::new("docs/../../outside"))
        .unwrap_err()
        .to_string();
    assert!(error.contains("escapes"), "{error}");
    let error = within_root(root.path(), Path::new("/etc/passwd"))
        .unwrap_err()
        .to_string();
    assert!(error.contains("escapes"), "{error}");
    let inside = within_root(root.path(), Path::new("docs/skill-verification.md")).unwrap();
    assert!(inside.starts_with(canonical_root(root.path()).unwrap()));
}

#[test]
fn write_creates_a_missing_root_without_a_parent_component() {
    let parent = tempfile::tempdir().unwrap();
    let root = parent.path().join("new-repo");
    let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args([
            "build-coverage",
            "--root",
            root.to_str().unwrap(),
            "--write",
        ])
        .output()
        .unwrap();
    assert_eq!(
        output.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(root.join("coverage.json").is_file());
    assert!(root.join("docs").join("skill-verification.md").is_file());
}

#[test]
fn a_missing_root_with_a_parent_component_is_not_created() {
    let parent = tempfile::tempdir().unwrap();
    let outside = parent.path().join("outside");
    let requested = parent.path().join("missing").join("..").join("outside");
    let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args([
            "build-coverage",
            "--root",
            requested.to_str().unwrap(),
            "--write",
        ])
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(1));
    assert!(!outside.exists());
    assert!(String::from_utf8_lossy(&output.stderr).contains("escapes"));
}

#[test]
fn an_existing_root_reached_through_parent_components_stays_that_directory() {
    let root = tempfile::tempdir().unwrap();
    let via = root
        .path()
        .join("..")
        .join(root.path().file_name().unwrap());
    let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args(["build-coverage", "--root", via.to_str().unwrap(), "--write"])
        .output()
        .unwrap();
    assert_eq!(
        output.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(root.path().join("coverage.json").is_file());
}

#[cfg(unix)]
#[test]
fn write_follows_an_output_directory_linked_inside_the_root() {
    let root = tempfile::tempdir().unwrap();
    let inside = root.path().join("inside");
    fs::create_dir(&inside).unwrap();
    std::os::unix::fs::symlink(&inside, root.path().join("docs")).unwrap();
    let output = coverage(root.path(), &["--write"]);
    assert_eq!(
        output.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(inside.join("skill-verification.md").is_file());
    assert!(root.path().join("coverage.json").is_file());
}

#[cfg(unix)]
#[test]
fn write_refuses_an_output_directory_linked_outside_the_root() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    std::os::unix::fs::symlink(outside.path(), root.path().join("docs")).unwrap();
    let output = coverage(root.path(), &["--write"]);
    assert_eq!(output.status.code(), Some(1));
    assert!(output.stdout.is_empty());
    assert_eq!(fs::read_dir(outside.path()).unwrap().count(), 0);
    assert!(!root.path().join("coverage.json").exists());
    assert!(String::from_utf8_lossy(&output.stderr).contains("escapes"));
}

#[cfg(unix)]
#[test]
fn a_cases_directory_linked_outside_the_root_is_refused() {
    let root = verified_tree();
    let outside = tempfile::tempdir().unwrap();
    let cases = root.path().join("validation/cases");
    let moved = outside.path().join("cases");
    fs::rename(&cases, &moved).unwrap();
    std::os::unix::fs::symlink(&moved, &cases).unwrap();
    let error = rendered(root.path()).unwrap_err().to_string();
    assert!(error.contains("escapes"), "{error}");
}

#[cfg(unix)]
#[test]
fn a_card_symlink_outside_validation_cases_is_refused() {
    let root = verified_tree();
    let outside = tempfile::tempdir().unwrap();
    let secret = outside.path().join("secret.md");
    fs::write(&secret, "---\n- alpha\n---\n").unwrap();
    let card = root.path().join("validation/cases/alpha-one.md");
    fs::remove_file(&card).unwrap();
    std::os::unix::fs::symlink(&secret, &card).unwrap();
    let error = rendered(root.path()).unwrap_err().to_string();
    assert!(error.contains("escapes"), "{error}");
    assert_eq!(fs::read_to_string(&secret).unwrap(), "---\n- alpha\n---\n");
}
