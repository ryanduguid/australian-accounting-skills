// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

use accounting_skills::review_state::{Check, STATE_FILE, result, validate, verify, write};
use std::{fs, path::Path, process::Command};

fn check(name: &str, status: &str, note: &str) -> Check {
    Check {
        check: name.into(),
        status: status.into(),
        note: note.into(),
    }
}

fn passed() -> Vec<Check> {
    vec![
        check("D9 gifts or donations", "passed", ""),
        check("D10", "not applicable", "no D10 claim or invoice"),
    ]
}

/// A fabricated case: a draft return and 2 source files, one in a subfolder.
fn case() -> tempfile::TempDir {
    let case = tempfile::tempdir().unwrap();
    fs::write(case.path().join("draft.md"), "Draft return v1\n").unwrap();
    fs::create_dir_all(case.path().join("sources/bank")).unwrap();
    fs::write(
        case.path().join("sources/receipt.txt"),
        "Fabricated receipt 50.00\n",
    )
    .unwrap();
    fs::write(
        case.path().join("sources/bank/statement.csv"),
        "date,amount\n2026-01-02,10.00\n",
    )
    .unwrap();
    case
}

fn reason(case: &Path) -> String {
    verify(case, None).unwrap().unwrap_or_default()
}

#[test]
fn a_passed_review_stays_current_until_its_draft_or_a_source_changes() {
    let case = case();
    let (state, _) = write(case.path(), "draft.md", passed(), "2026-11-24").unwrap();
    assert_eq!(state.result, "passed");
    let paths: Vec<_> = state
        .sources
        .iter()
        .map(|digest| digest.path.as_str())
        .collect();
    assert_eq!(paths, ["sources/bank/statement.csv", "sources/receipt.txt"]);
    assert_eq!(verify(case.path(), None).unwrap(), None);

    fs::write(case.path().join("draft.md"), "Draft return v2\n").unwrap();
    assert_eq!(
        reason(case.path()),
        "draft draft.md changed since the review"
    );
    fs::write(case.path().join("draft.md"), "Draft return v1\n").unwrap();
    assert_eq!(verify(case.path(), None).unwrap(), None);

    fs::write(
        case.path().join("sources/receipt.txt"),
        "Fabricated receipt 55.00\n",
    )
    .unwrap();
    assert_eq!(
        reason(case.path()),
        "source sources/receipt.txt changed since the review"
    );
    fs::write(
        case.path().join("sources/receipt.txt"),
        "Fabricated receipt 50.00\n",
    )
    .unwrap();
    fs::write(case.path().join("sources/late.pdf"), "added after review").unwrap();
    assert_eq!(
        reason(case.path()),
        "source sources/late.pdf was added since the review"
    );
    fs::remove_file(case.path().join("sources/late.pdf")).unwrap();
    fs::remove_file(case.path().join("sources/bank/statement.csv")).unwrap();
    assert_eq!(
        reason(case.path()),
        "source sources/bank/statement.csv was removed since the review"
    );
    fs::remove_file(case.path().join("draft.md")).unwrap();
    assert_eq!(reason(case.path()), "draft draft.md is missing");
}

#[test]
fn a_check_not_performed_never_reads_as_passed() {
    let mut checks = passed();
    checks.push(check(
        "Joint income",
        "not performed",
        "no ownership records supplied",
    ));
    assert_eq!(result(&checks), "incomplete");
    let case = case();
    write(case.path(), "draft.md", checks.clone(), "2026-11-24").unwrap();
    assert_eq!(
        reason(case.path()),
        "the review did not pass: Joint income not performed"
    );
    checks.push(check("Refund stated", "failed", "estimate missing"));
    assert_eq!(result(&checks), "failed");
}

#[test]
fn an_edited_state_cannot_turn_a_failed_review_into_a_pass() {
    let case = case();
    let checks = vec![check(
        "D9 gifts or donations",
        "failed",
        "recipient not a DGR on the gift date",
    )];
    write(case.path(), "draft.md", checks, "2026-11-24").unwrap();
    let path = case.path().join(STATE_FILE);
    let edited = fs::read_to_string(&path)
        .unwrap()
        .replace("\"result\": \"failed\"", "\"result\": \"passed\"");
    fs::write(&path, edited).unwrap();
    assert_eq!(
        reason(case.path()),
        "the review did not pass: D9 gifts or donations failed"
    );
}

#[test]
fn the_register_and_draft_are_checked_before_anything_is_written() {
    for (checks, message) in [
        (vec![], "the register lists no checks"),
        (
            vec![check("D9", "passed", ""), check("D9", "passed", "")],
            "blank or repeated",
        ),
        (vec![check("D9", "ok", "")], "not one of"),
        (vec![check("D9", "not applicable", " ")], "without a note"),
    ] {
        assert!(
            validate(&checks).unwrap_err().to_string().contains(message),
            "{message}"
        );
    }
    let case = case();
    for draft in [
        "../draft.md",
        "sources/receipt.txt",
        STATE_FILE,
        "missing.md",
    ] {
        assert!(
            write(case.path(), draft, passed(), "2026-11-24").is_err(),
            "{draft}"
        );
    }
    assert!(!case.path().join(STATE_FILE).exists());
}

#[test]
fn verify_without_a_state_or_with_a_tampered_draft_path_does_not_pass() {
    let case = case();
    assert_eq!(
        reason(case.path()),
        format!("no {STATE_FILE}: no review has been recorded")
    );
    write(case.path(), "draft.md", passed(), "2026-11-24").unwrap();
    let path = case.path().join(STATE_FILE);
    let edited = fs::read_to_string(&path)
        .unwrap()
        .replace("\"path\": \"draft.md\"", "\"path\": \"../draft.md\"");
    fs::write(&path, edited).unwrap();
    assert_eq!(reason(case.path()), "draft ../draft.md is missing");
}

#[test]
fn the_command_writes_then_verifies_with_its_exit_codes() {
    let case = case();
    let register = case.path().join("register.json");
    fs::write(
        &register,
        r#"{"checks": [{"check": "D9 gifts or donations", "status": "passed"}]}"#,
    )
    .unwrap();
    let run = |args: &[&str]| {
        Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
            .args(args)
            .output()
            .unwrap()
    };
    let dir = case.path().to_str().unwrap();
    let wrote = run(&[
        "review-state",
        "write",
        dir,
        "--draft",
        "draft.md",
        "--register",
        register.to_str().unwrap(),
    ]);
    assert_eq!(
        wrote.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&wrote.stderr)
    );
    // register.json sits outside sources/, so only the 2 source files count.
    assert!(String::from_utf8_lossy(&wrote.stdout).contains("review passed, 1 checks, 2 sources"));
    let digest = String::from_utf8_lossy(&wrote.stdout)
        .trim()
        .rsplit(' ')
        .next()
        .unwrap()
        .to_owned();
    assert_eq!(
        run(&["review-state", "verify", dir, "--state-sha256", &digest])
            .status
            .code(),
        Some(0)
    );
    assert_eq!(
        run(&["review-state", "verify", dir, "--state-sha256"])
            .status
            .code(),
        Some(1)
    );
    assert_eq!(run(&["review-state", "verify", dir]).status.code(), Some(0));
    fs::write(case.path().join("draft.md"), "changed").unwrap();
    let stale = run(&["review-state", "verify", dir]);
    assert_eq!(stale.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&stale.stdout).starts_with("STALE draft draft.md changed"));
    assert_eq!(run(&["review-state", "verify"]).status.code(), Some(1));
    assert_eq!(
        run(&["review-state", "write", dir, "--draft"])
            .status
            .code(),
        Some(1)
    );
}

#[test]
fn a_rewritten_state_fails_against_the_digest_recorded_at_the_review() {
    let case = case();
    let failed = vec![check(
        "D9 gifts or donations",
        "failed",
        "recipient not a DGR",
    )];
    let (_, digest) = write(case.path(), "draft.md", failed, "2026-11-24").unwrap();
    assert_eq!(
        verify(case.path(), Some(&digest.to_uppercase())).unwrap(),
        Some("the review did not pass: D9 gifts or donations failed".into())
    );
    // Rewriting both the check and the result, or rerunning write after the draft changed, gives a
    // state that passes on its own; the digest the reviewer recorded is what refuses it.
    fs::write(case.path().join("draft.md"), "Draft return v2\n").unwrap();
    write(case.path(), "draft.md", passed(), "2026-11-24").unwrap();
    assert_eq!(verify(case.path(), None).unwrap(), None);
    assert_eq!(
        verify(case.path(), Some(&digest)).unwrap(),
        Some(format!(
            "{STATE_FILE} is not the file whose SHA-256 was recorded at the review"
        ))
    );
}

#[cfg(unix)]
#[test]
fn a_sources_link_leading_outside_the_case_is_refused() {
    let case = case();
    let outside = tempfile::tempdir().unwrap();
    fs::rename(case.path().join("sources"), outside.path().join("sources")).unwrap();
    std::os::unix::fs::symlink(outside.path().join("sources"), case.path().join("sources"))
        .unwrap();
    let error = write(case.path(), "draft.md", passed(), "2026-11-24").unwrap_err();
    assert!(
        error.to_string().contains("outside the case folder"),
        "{error}"
    );
}
