// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use accounting_skills::sweep::{decide, outcome, parse_report};
use std::fs;

fn report(changed: &str, blocked: &str) -> String {
    format!(
        "# Primary source sweep\n\nSwept 1 records over 1 distinct pages at 2026-09-20 19:00 UTC.\n- changed: {changed}\n- missing: 0\n- unreadable: 0\n- review-due: 0\n- baseline-required: 0\n- blocked: {blocked}\n- unreachable: 0\n- client-rendered: 0\n"
    )
}
const START: &str = "2026-09-20T19:00:05Z";

#[test]
fn status_and_counts_must_agree_and_unchecked_sources_remain_explicit() {
    let counts = parse_report(&report("0", "7"), START).unwrap();
    let clean = decide(0, &counts).unwrap();
    assert_eq!(clean.name, "clean");
    assert!(
        clean
            .comment
            .contains("7 blocked sources could not be checked")
    );
    assert!(decide(2, &counts).is_err());
    assert!(decide(1, &counts).is_err());
    let findings = parse_report(&report("4", "0"), START).unwrap();
    assert_eq!(
        decide(2, &findings).unwrap().comment,
        "4 sources need an edit here."
    );
    assert!(decide(0, &findings).is_err());
}

#[test]
fn counts_are_ascii_digits_within_the_64_bit_range() {
    let max = u64::MAX.to_string();
    let counts = parse_report(&report(&max, "0"), START).unwrap();
    assert_eq!(
        decide(2, &counts).unwrap().comment,
        format!("{max} sources need an edit here.")
    );
    for changed in ["\u{662}", "18446744073709551616"] {
        assert!(
            parse_report(&report(changed, "0"), START).is_err(),
            "{changed}"
        );
    }
    let unicode_records = report("0", "0").replace("Swept 1", "Swept \u{661}");
    assert!(parse_report(&unicode_records, START).is_err());
    let overflowing = report(&max, "0").replace("- missing: 0", "- missing: 1");
    let counts = parse_report(&overflowing, START).unwrap();
    assert!(
        decide(2, &counts)
            .unwrap_err()
            .to_string()
            .contains("exceeds the 64-bit range")
    );
}

#[test]
fn malformed_stale_empty_and_duplicate_reports_never_pass() {
    let ordinary = report("0", "0");
    for text in [
        String::new(),
        ordinary.replace("Swept 1", "Swept 0"),
        ordinary.replace("19:00 UTC", "18:59 UTC"),
        ordinary.replace("- blocked", "- other"),
        format!("{ordinary}- changed: 0\n"),
        ordinary.replace("2026-09-20", "2026-02-30"),
    ] {
        assert!(parse_report(&text, START).is_err(), "{text}");
    }
    assert!(parse_report(&ordinary, "2026-09-20T19:00:59Z").is_ok());
    assert!(parse_report(&ordinary, "2026-09-20T19:00:60Z").is_err());
}

#[test]
fn missing_and_lexically_escaping_paths_are_refused() {
    let root = tempfile::tempdir().unwrap();
    let missing = outcome(0, &root.path().join("missing.md"), START, root.path()).unwrap_err();
    assert!(missing.to_string().contains("wrote no report"));
    let outside = root.path().join("../outside.md");
    assert!(
        outcome(0, &outside, START, root.path())
            .unwrap_err()
            .to_string()
            .contains("escapes the working directory")
    );
    fs::write(root.path().join("report.md"), report("0", "0")).unwrap();
    assert_eq!(
        outcome(
            0,
            &root.path().join("missing/../report.md"),
            START,
            root.path()
        )
        .unwrap()
        .name,
        "clean"
    );
}

#[test]
fn linked_paths_are_resolved_before_confinement_and_parent_components() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    fs::write(root.path().join("report.md"), report("0", "0")).unwrap();
    fs::write(outside.path().join("report.md"), report("0", "0")).unwrap();
    let link = root.path().join("escape");
    #[cfg(unix)]
    std::os::unix::fs::symlink(outside.path(), &link).unwrap();
    #[cfg(windows)]
    {
        let result = std::process::Command::new("cmd")
            .args(["/c", "mklink", "/J"])
            .arg(&link)
            .arg(outside.path())
            .output()
            .unwrap();
        assert!(result.status.success());
    }
    for path in [
        link.join("report.md"),
        link.join("../report.md"),
        link.join("missing.md"),
    ] {
        assert!(
            outcome(0, &path, START, root.path())
                .unwrap_err()
                .to_string()
                .contains("escapes the working directory")
        );
    }
    #[cfg(windows)]
    fs::remove_dir(link).unwrap();
}

// The report that scripts/source_refresh.py renders, which tests/test_source_sweep.py
// keeps in step with the renderer. The cases below vary its counts.
const RENDERED: &str = include_str!("sweep-report.md.fixture");
const STAMP: &str = "2026-09-20 19:00";

fn rendered(counts: &[(&str, usize)], stamp: &str) -> String {
    let records: usize = counts.iter().map(|(_, count)| count).sum();
    RENDERED
        .lines()
        .filter(|line| !line.starts_with('|'))
        .map(|line| {
            if line.starts_with("Swept ") {
                format!("Swept {records} records over {records} distinct pages at {stamp} UTC.")
            } else if let Some(line) = line.strip_prefix("- ") {
                let (label, _) = line.rsplit_once(": ").unwrap();
                let name = label.split(' ').next().unwrap();
                let count = counts
                    .iter()
                    .find(|(category, _)| *category == name)
                    .map_or(0, |(_, count)| *count);
                format!("- {label}: {count}")
            } else {
                line.to_owned()
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
        + "\n"
}

fn written(text: &str) -> (tempfile::TempDir, std::path::PathBuf) {
    let root = tempfile::tempdir().unwrap();
    let report = root.path().join("sweep.md");
    fs::write(&report, text).unwrap();
    (root, report)
}

fn error(status: i64, text: &str) -> String {
    let (root, report) = written(text);
    outcome(status, &report, START, root.path())
        .unwrap_err()
        .to_string()
}

#[test]
fn the_rendered_report_parses_to_its_counts() {
    let counts = parse_report(RENDERED, START).unwrap();
    for category in [
        "changed",
        "missing",
        "unreadable",
        "review-due",
        "baseline-required",
        "blocked",
        "unreachable",
        "client-rendered",
    ] {
        assert_eq!(counts[category], 1, "{category}");
    }
    assert_eq!(counts["records"], 11);
    assert_eq!(
        decide(2, &counts).unwrap().comment,
        "5 sources need an edit here."
    );
    assert!(decide(0, &counts).is_err());
}

#[test]
fn client_rendered_sources_are_listed_as_unchecked_not_actionable() {
    let (root, report) = written(&rendered(
        &[("client-rendered", 8), ("unchanged", 2)],
        STAMP,
    ));
    let result = outcome(0, &report, START, root.path()).unwrap();
    assert_eq!(result.name, "clean");
    assert!(
        result
            .comment
            .contains("8 client-rendered sources could not be checked")
    );
    assert!(outcome(2, &report, START, root.path()).is_err());
    let all = rendered(
        &[("blocked", 1), ("unreachable", 2), ("client-rendered", 3)],
        STAMP,
    );
    let (root, report) = written(&all);
    assert_eq!(
        outcome(0, &report, START, root.path()).unwrap().comment,
        "No indexed source needs an edit here. 1 blocked, 2 unreachable and 3 client-rendered sources could not be checked and are listed in the report."
    );
}

#[test]
fn exit_0_with_a_clean_current_report_is_clean() {
    for category in ["unchanged", "baseline", "scheduled"] {
        let (root, report) = written(&rendered(&[(category, 3)], STAMP));
        let result = outcome(0, &report, START, root.path()).unwrap();
        assert_eq!(result.name, "clean");
        assert_eq!(
            result.comment,
            "No actionable source findings were reported."
        );
    }
}

#[test]
fn findings_and_an_overdue_manual_review_need_exit_2() {
    for (counts, comment) in [
        (
            vec![("unchanged", 2), ("review-due", 1)],
            "1 sources need an edit here.",
        ),
        (
            vec![("unchanged", 2), ("changed", 1), ("missing", 1)],
            "2 sources need an edit here.",
        ),
    ] {
        let (root, report) = written(&rendered(&counts, STAMP));
        let result = outcome(2, &report, START, root.path()).unwrap();
        assert_eq!(
            (result.name, result.comment.as_str()),
            ("findings", comment)
        );
    }
}

#[test]
fn other_exit_statuses_missing_reports_and_contradictions_fail() {
    let clean = rendered(&[("unchanged", 3)], STAMP);
    for status in [1, 3, 127, -1] {
        assert_eq!(
            error(status, &clean),
            format!("source_refresh.py exited {status}")
        );
    }
    let root = tempfile::tempdir().unwrap();
    for status in [0, 2] {
        let message = outcome(status, &root.path().join("sweep.md"), START, root.path())
            .unwrap_err()
            .to_string();
        assert!(
            message.starts_with(&format!(
                "source_refresh.py exited {status} but wrote no report"
            )),
            "{message}"
        );
    }
    assert_eq!(
        error(0, &rendered(&[("changed", 1)], STAMP)),
        "exit 0 with a report that lists 1 actionable sources"
    );
    assert_eq!(
        error(2, &rendered(&[("unchanged", 1)], STAMP)),
        "exit 2 with a report that lists nothing actionable"
    );
}

#[test]
fn duplicate_stale_empty_and_malformed_reports_fail() {
    for (category, status) in [("changed", 2), ("unchanged", 0)] {
        let text = rendered(&[(category, 1)], STAMP) + "- changed: 0\n";
        assert_eq!(error(status, &text), "duplicate count for changed");
    }
    assert_eq!(
        error(0, &rendered(&[("unchanged", 3)], "2026-09-20 18:58")),
        "the report was written at 2026-09-20 18:58 UTC, before this run started"
    );
    let ordinary = rendered(&[("unchanged", 1)], STAMP);
    for (text, message) in [
        (
            String::new(),
            "the report does not start with the sweep header",
        ),
        (
            "# Primary source sweep\n\nnothing\n".to_owned(),
            "the report has no 'Swept N records' line",
        ),
        (rendered(&[], STAMP), "the report covers no records"),
        (
            ordinary.replace("- blocked", "- other"),
            "the report has no count for blocked",
        ),
    ] {
        assert_eq!(error(0, &text), message);
    }
}

#[test]
fn a_report_from_the_starting_minute_is_current() {
    let (root, report) = written(&rendered(&[("unchanged", 3)], STAMP));
    let result = outcome(0, &report, "2026-09-20T19:00:59Z", root.path()).unwrap();
    assert_eq!(result.name, "clean");
}

#[test]
fn blocked_and_unreachable_sources_are_never_reported_as_checked() {
    let (root, report) = written(&rendered(
        &[("unchanged", 5), ("blocked", 7), ("unreachable", 1)],
        STAMP,
    ));
    let result = outcome(0, &report, START, root.path()).unwrap();
    assert_eq!(result.name, "clean");
    assert_eq!(
        result.comment,
        "No indexed source needs an edit here. 7 blocked and 1 unreachable sources could not be checked and are listed in the report."
    );
}

#[test]
fn reports_outside_the_working_directory_are_refused() {
    let inside = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    let escaping = outside.path().join("sweep.md");
    fs::write(&escaping, rendered(&[("unchanged", 1)], STAMP)).unwrap();
    let traversal = inside
        .path()
        .join("..")
        .join(outside.path().file_name().unwrap())
        .join("sweep.md");
    for path in [escaping, traversal] {
        let message = outcome(0, &path, START, inside.path())
            .unwrap_err()
            .to_string();
        assert!(
            message.starts_with("report path escapes the working directory: "),
            "{message}"
        );
    }
}

fn command(directory: &std::path::Path, args: &[&str]) -> std::process::Output {
    std::process::Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .arg("sweep-outcome")
        .args(args)
        .current_dir(directory)
        .env("GITHUB_OUTPUT", directory.join("output"))
        .output()
        .unwrap()
}

#[test]
fn the_outcome_goes_only_to_stdout_for_the_workflow_to_redirect() {
    let (root, _) = written(&rendered(&[("unchanged", 1)], STAMP));
    let output = command(
        root.path(),
        &["--status", "0", "--report", "sweep.md", "--started", START],
    );
    assert_eq!(output.status.code(), Some(0));
    assert!(output.stderr.is_empty());
    let stdout = String::from_utf8(output.stdout).unwrap();
    assert_eq!(
        stdout.lines().collect::<Vec<_>>(),
        [
            "outcome=clean",
            "comment=No actionable source findings were reported."
        ]
    );
    assert!(!root.path().join("output").exists());
}

#[test]
fn a_failure_is_reported_on_stderr_with_exit_1() {
    let root = tempfile::tempdir().unwrap();
    for args in [
        ["--status", "1", "--report", "sweep.md", "--started", START],
        ["--status", "0", "--report", "sweep.md", "--started", START],
        [
            "--status",
            "0",
            "--report",
            "sweep.md",
            "--started",
            "yesterday",
        ],
    ] {
        let output = command(root.path(), &args);
        assert_eq!(output.status.code(), Some(1), "{args:?}");
        assert!(output.stdout.is_empty());
        assert!(output.stderr.starts_with(b"FAIL "), "{output:?}");
    }
}
