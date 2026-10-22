use accounting_skills::sweep::{decide, outcome, parse_report};
use std::fs;

fn report(changed: &str, blocked: &str) -> String {
    format!(
        "# Primary source sweep\n\nSwept 1 records over 1 distinct pages at 2026-09-20 19:00 UTC.\n- changed: {changed}\n- missing: 0\n- unreadable: 0\n- review-due: 0\n- baseline-required: 0\n- blocked: {blocked}\n- unreachable: 0\n"
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
fn counts_preserve_unicode_decimal_and_large_integers() {
    let counts = parse_report(&report("٢", "0"), START).unwrap();
    assert_eq!(
        decide(2, &counts).unwrap().comment,
        "2 sources need an edit here."
    );
    let huge = "9".repeat(120);
    let counts = parse_report(&report(&huge, "0"), START).unwrap();
    assert_eq!(
        decide(2, &counts).unwrap().comment,
        format!("{huge} sources need an edit here.")
    );
    assert!(parse_report(&report(&"9".repeat(4301), "0"), START).is_err());
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
