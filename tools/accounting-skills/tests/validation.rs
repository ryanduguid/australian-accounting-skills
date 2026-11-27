// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

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
    // An unbroken run of 12 or more digits, such as a card number, including
    // one that ends a sentence or clause; money amounts still pass.
    for text in [
        "123456789012",
        "4111111111111111",
        "Card 4111111111111111.",
        "4111111111111111, expiring",
        "no.4111111111111111",
        // Dot or comma grouping that is not thousands grouping.
        "4111.1111.1111.1111",
        "12345678,2",
        "4750.00,4111111111111111",
        "-4750.00,12345678,Transfer",
        "4750.00,51824753556",
        "062.000,12345678",
    ] {
        let error = v::check_sensitive_content(text, &[])
            .unwrap_err()
            .to_string();
        assert!(
            error.contains("unlabelled long numeric identifier"),
            "{text}: {error}"
        );
    }
    for text in [
        "$12345678.90",
        "0.123456789012",
        "12,345,678.90",
        "1,234,567",
        "18450.00,4450.00,14000.00,10000.00",
    ] {
        assert!(v::check_sensitive_content(text, &[]).is_ok(), "{text}");
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
fn unicode_17_spellings_are_refused_as_python_3_15_refuses_them() {
    // Each expected result is CPython 3.15.0's (Unicode 17.0) verdict from
    // scripts/validate_validation.py; Python 3.14.8 (Unicode 16.0) passes
    // every one. U+A7F1 normalises to `S`; U+11DE0 to U+11DE9 are digits.
    let digits: String = ('\u{11DE0}'..='\u{11DE9}').collect();
    let one = '\u{11DE1}';
    for (text, label) in [
        (
            "\u{A7F1}k_abcdef**ghijkl**mnop".to_owned(),
            "API credential",
        ),
        ("\u{A7F1}k_abcdefghijklmnop".to_owned(), "API credential"),
        (format!("BSB {one}"), "BSB or bank account"),
        (format!("TFN {one}"), "labelled Australian identifier"),
        (format!("phone {one}"), "phone number"),
        (
            digits.chars().cycle().take(12).collect(),
            "unlabelled long numeric identifier",
        ),
        (
            digits.chars().take(8).collect(),
            "unlabelled long numeric identifier",
        ),
        (format!("effective {one}%"), "dated/rate rule"),
    ] {
        let error = v::check_sensitive_content(&text, &[])
            .unwrap_err()
            .to_string();
        assert!(error.contains(label), "{text:?}: {error}");
    }
    for text in [format!("x{one}"), format!("sk_abcdef{one}")] {
        assert!(v::check_sensitive_content(&text, &[]).is_ok(), "{text:?}");
    }
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
fn run_date_is_only_the_extended_calendar_form() {
    let known = BTreeSet::from(["test-card".to_owned()]);
    let path = "validation/results/2026-01-31-fixture.json";
    let mut record = json!({"model":"fixture","run_date":"2026-01-31","skills_version":"fixture","runner":"A Person","results":{"test-card":"pass"}});
    assert_eq!(
        v::check_result_file(path, &record.to_string(), &known).unwrap(),
        "legacy"
    );
    for value in ["20260131", "2026-W05-6", "2026W056", "+026-01-31"] {
        record["run_date"] = json!(value);
        assert!(
            v::check_result_file(path, &record.to_string(), &known)
                .unwrap_err()
                .to_string()
                .contains("run_date must be a real date, YYYY-MM-DD"),
            "{value}"
        );
    }
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

#[test]
fn check_ignore_reports_only_the_ignored_paths() {
    let root = tempdir().unwrap();
    let init = std::process::Command::new("git")
        .args(["init", "-q"])
        .current_dir(root.path())
        .status()
        .unwrap();
    assert!(init.success());
    fs::write(root.path().join(".gitignore"), "/b.md\n").unwrap();
    let paths = ["a.md", "b.md", "c.md"].map(String::from);
    assert_eq!(
        v::ignored_paths(&paths, root.path()).unwrap(),
        BTreeSet::from(["b.md".to_owned()])
    );
    assert!(
        v::ignored_paths(&paths[..1], root.path())
            .unwrap()
            .is_empty()
    );
    let broken = tempdir().unwrap();
    fs::write(broken.path().join(".git"), "not a repository\n").unwrap();
    assert!(
        v::ignored_paths(&paths, broken.path())
            .unwrap_err()
            .to_string()
            .starts_with("git check-ignore failed: ")
    );
}

/// The cases `tests/test_validation_pack.py` also runs, from the same file.
fn figure_fixtures() -> serde_json::Value {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../tests/figure_card_fixtures.json"
    );
    serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap()
}

#[test]
fn figures_cards_agree_with_the_shared_python_cases() {
    let fixtures = figure_fixtures();
    let skills: BTreeSet<String> = fixtures["skills"]
        .as_array()
        .unwrap()
        .iter()
        .map(|skill| skill.as_str().unwrap().to_owned())
        .collect();
    for case in fixtures["cards"].as_array().unwrap() {
        let mut card = fixtures["base"].clone();
        if let Some(set) = case["set"].as_object() {
            for (key, value) in set {
                card[key] = value.clone();
            }
        }
        if let Some(drop) = case["drop"].as_str() {
            card.as_object_mut().unwrap().remove(drop);
        }
        let text = case["text"].as_str().map_or_else(
            || serde_json::to_string_pretty(&card).unwrap() + "\n",
            str::to_owned,
        );
        let rel = case["rel"]
            .as_str()
            .unwrap_or("validation/figures/fixture-card.json");
        let name = &case["name"];
        match v::check_figure_card(rel, &text, &skills) {
            Ok(fields) => assert_eq!(json!(fields), case["fields"], "{name}"),
            Err(error) => {
                let expected = case["error"]
                    .as_str()
                    .unwrap_or_else(|| panic!("{name}: {error}"));
                assert!(error.to_string().contains(expected), "{name}: {error}");
            }
        }
    }
}

#[test]
fn figure_scores_and_schemas_agree_with_the_shared_python_cases() {
    let fixtures = figure_fixtures();
    for case in fixtures["scores"].as_array().unwrap() {
        let fields: BTreeSet<String> = case["fields"]
            .as_array()
            .unwrap()
            .iter()
            .map(|field| field.as_str().unwrap().to_owned())
            .collect();
        let name = &case["name"];
        match v::score_figures(&fields, &case["verdicts"]) {
            Ok((fields, matched, label_right)) => assert_eq!(
                json!({"fields": fields, "match": matched, "label_right": label_right}),
                case["counts"],
                "{name}"
            ),
            Err(error) => {
                let expected = case["error"]
                    .as_str()
                    .unwrap_or_else(|| panic!("{name}: {error}"));
                assert!(error.to_string().contains(expected), "{name}: {error}");
            }
        }
    }
    for case in fixtures["schemas"].as_array().unwrap() {
        let text = case["text"]
            .as_str()
            .map_or_else(|| case["schema"].to_string(), str::to_owned);
        let result = v::check_figures_schema(&text);
        assert_eq!(result.is_ok(), case["ok"] == true, "{}", case["name"]);
        if let Some(expected) = case["error"].as_str() {
            assert!(
                result.unwrap_err().to_string().contains(expected),
                "{}",
                case["name"]
            );
        }
    }
    let published = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../validation/figures.schema.json"
    );
    v::check_figures_schema(&fs::read_to_string(published).unwrap()).unwrap();
    let (fixed, figures) = v::split_figure_cards(&BTreeSet::from([
        "validation/figures.schema.json".to_owned(),
        "validation/figures/fixture-card.json".to_owned(),
        "validation/figures/Notes.json".to_owned(),
    ]));
    assert_eq!(
        figures,
        BTreeSet::from(["validation/figures/fixture-card.json".to_owned()])
    );
    assert_eq!(fixed.len(), 2);
}
