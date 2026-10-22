use accounting_skills::validation as v;
use serde_json::json;
use std::{collections::BTreeSet, fs};
use tempfile::tempdir;

#[test]
fn card_yaml_preserves_schema_and_refuses_ambiguity() {
    let card = |id: &str, targets: &str| {
        format!("---\nid: {id}\nsynthetic: true\ntarget_skills: {targets}\n---\n# Card\n")
    };
    let (metadata, _) =
        v::parse_front_matter(&card("test-card", "[bas-preparation]"), "test-card.md").unwrap();
    assert_eq!(metadata["synthetic"], true);
    for id in [
        "2026-01-01",
        "0b101",
        "on",
        "&id test-card",
        "!!str test-card",
    ] {
        assert!(v::parse_front_matter(&card(id, "[bas-preparation]"), "test-card.md").is_err());
    }
    let duplicate = card("test-card\nid: other", "[bas-preparation]");
    assert!(
        v::parse_front_matter(&duplicate, "test-card.md")
            .unwrap_err()
            .to_string()
            .contains("duplicate YAML field")
    );
    assert!(v::parse_front_matter(&card("test-card", "[on]"), "test-card.md").is_err());
}

#[test]
fn rendered_private_patterns_remain_visible_and_waivers_are_specific() {
    let oversized = format!("&#{};", "1".repeat(4301));
    assert!(v::normalise_for_sensitive_scan(&oversized).is_err());
    assert!(v::check_sensitive_content(&oversized, &[]).is_err());
    for text in [
        "worker&#64;example.test",
        "B<!-- -->SB 123-456",
        "A**B**N 12 345 678 901",
        "effective 12%.",
        "x\u{301}Bearer abcdefghijklmnop",
    ] {
        assert!(v::check_sensitive_content(text, &[]).is_err(), "{text}");
    }
    assert!(
        v::check_sensitive_content("123456789", &["unlabelled long numeric identifier".into()])
            .is_ok()
    );
    assert!(
        v::check_sensitive_content(
            "Bearer abcdefghijklmnop",
            &["unlabelled long numeric identifier".into()]
        )
        .unwrap_err()
        .to_string()
        .contains("bearer credential")
    );
}

#[test]
fn trial_provenance_does_not_upgrade_preparation_to_a_verdict() {
    let known = BTreeSet::from(["test-card".to_owned()]);
    let mut record = json!({"schema_version":2,"model":"fixture","run_date":"2026-01-31","skills_version":"fixture","runner":"A Person","input_mode":"task-only","status":"prepared","results":{},"provenance":{"test-card":{"input_sha256":"a".repeat(64),"context_sha256":"b".repeat(64),"rubric_sha256":"c".repeat(64)}}});
    let path = "validation/results/2026-01-31-fixture.json";
    assert_eq!(
        v::check_result_file(path, &record.to_string(), &known).unwrap(),
        "prepared"
    );
    record["results"] = json!({"test-card":"pass"});
    assert!(
        v::check_result_file(path, &record.to_string(), &known)
            .unwrap_err()
            .to_string()
            .contains("human-confirmed")
    );
    assert!(
        v::strict_json(r#"{"outer":{"x":1,"x":2}}"#, "fixture")
            .unwrap_err()
            .to_string()
            .contains("duplicate JSON key")
    );
}

#[test]
fn inventory_and_reads_reject_reparse_points_and_invalid_text() {
    let root = tempdir().unwrap();
    let outside = tempdir().unwrap();
    fs::create_dir(root.path().join("validation")).unwrap();
    let raw = root.path().join("validation/raw.bin");
    fs::write(&raw, [255, 254, 0]).unwrap();
    assert!(
        v::inventory_validation_tree(root.path())
            .unwrap()
            .contains("validation/raw.bin")
    );
    assert!(v::read_utf8(&raw).is_err());
    #[cfg(unix)]
    {
        fs::create_dir(root.path().join("validation/cases")).unwrap();
        fs::write(root.path().join("validation/cases/card.md"), "card").unwrap();
        fs::write(root.path().join("validation/cases\\card.md"), [255, 254, 0]).unwrap();
        let inventory = v::inventory_validation_tree(root.path()).unwrap();
        assert!(inventory.contains("validation/cases/card.md"));
        assert!(inventory.contains("validation/cases\\card.md"));
    }
    fs::write(&raw, "hidden\u{200b}value").unwrap();
    assert!(v::read_utf8(&raw).is_err());
    let link = root.path().join("validation").join("escape");
    #[cfg(unix)]
    std::os::unix::fs::symlink(outside.path(), &link).unwrap();
    #[cfg(windows)]
    {
        let setup = std::process::Command::new("cmd")
            .args(["/c", "mklink", "/J"])
            .arg(&link)
            .arg(outside.path())
            .output()
            .unwrap();
        assert!(
            setup.status.success(),
            "junction setup: {:?}, {:?}",
            String::from_utf8_lossy(&setup.stdout),
            String::from_utf8_lossy(&setup.stderr)
        );
    }
    assert!(
        v::inventory_validation_tree(root.path())
            .unwrap_err()
            .to_string()
            .contains("symlink/reparse")
    );
}
