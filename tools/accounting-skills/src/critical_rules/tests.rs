// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

use super::{
    MAX_CHARS, MAX_KEYWORDS_BYTES, TRANSCRIPT_TAIL, compile_phrase, context, format_hook_output,
    load_keywords, next_match, plural_suffix_len, prompt_matches, rules, run_mode,
    transcript_matches,
};
use serde_json::{Map, Value, json};
use std::{fs, path::PathBuf};
use tempfile::TempDir;

fn canonical(root: &TempDir) -> PathBuf {
    fs::canonicalize(root.path()).unwrap()
}

fn skills(root: &TempDir) -> PathBuf {
    canonical(root).join(".claude").join("skills")
}

fn fixture_root(skills: &[(&str, &str)], keywords: Value) -> TempDir {
    let root = tempfile::tempdir().unwrap();
    let hooks = root.path().join("hooks");
    fs::create_dir_all(&hooks).unwrap();
    fs::write(hooks.join("skill-keywords.json"), keywords.to_string()).unwrap();
    for (name, body) in skills {
        let dir = root.path().join(".claude/skills").join(name);
        fs::create_dir_all(&dir).unwrap();
        fs::write(dir.join("SKILL.md"), body).unwrap();
    }
    root
}

#[test]
fn extracts_anchored_rules_with_continuations_and_multi_anchors() {
    let body = "\
# Demo\r\n\
- Do not lodge. <!-- rule: no-lodgement -->\r\n\
  Prepare only.\r\n\
  - Nested stop.\r\n\
1a) Never guess rates. <!-- rule: evidence-boundary --> <!-- rule: untrusted-instructions -->\r\n\
  Verify primary text.\r\n\
# Heading stops continuation\r\n\
Plain line <!-- rule: bad name -->\r\n";
    let root = fixture_root(&[("demo-skill", body)], json!({}));
    let extracted = rules(&skills(&root), "demo-skill").unwrap();
    assert_eq!(
        extracted,
        [
            "Do not lodge. Prepare only.",
            "Never guess rates. Verify primary text.",
        ]
    );
}

#[test]
fn matches_whole_words_plurals_and_unicode_case_folding() {
    let root = fixture_root(
        &[
            ("au-psi-review", "Rule <!-- rule: no-lodgement -->\n"),
            ("bas-preparation", "Rule <!-- rule: no-lodgement -->\n"),
            ("fbt-annual-workflow", "Rule <!-- rule: no-lodgement -->\n"),
        ],
        json!({
            "au-psi-review": ["psi"],
            "bas-preparation": ["bas"],
            "fbt-annual-workflow": ["tax", "fbt"],
        }),
    );
    let skills_dir = skills(&root);
    assert_eq!(
        prompt_matches(
            &canonical(&root),
            &skills_dir,
            "Check PS\u{0130} and taxes; not basil, fbt-like, fbt2."
        )
        .unwrap(),
        ["au-psi-review", "fbt-annual-workflow"]
    );
    assert_eq!(
        prompt_matches(
            &canonical(&root),
            &skills_dir,
            "Review taxe\u{017f} then BASes."
        )
        .unwrap(),
        ["fbt-annual-workflow", "bas-preparation"]
    );
}

#[test]
fn orders_prompt_earliest_and_compact_most_recent_within_tail() {
    let root = fixture_root(
        &[
            ("alpha-skill", "A <!-- rule: no-lodgement -->\n"),
            ("beta-skill", "B <!-- rule: no-lodgement -->\n"),
        ],
        json!({"alpha-skill": ["alpha"], "beta-skill": ["beta"]}),
    );
    let skills_dir = skills(&root);
    let transcript = root.path().join("session.jsonl");
    let padding = "x".repeat(TRANSCRIPT_TAIL as usize + 32);
    let text = format!("alpha-skill {padding} alpha-skill then beta-skill");
    fs::write(&transcript, text).unwrap();
    let compact = transcript_matches(&skills_dir, transcript.to_str().unwrap()).unwrap();
    assert_eq!(compact, ["beta-skill", "alpha-skill"]);

    let pushed_out = root.path().join("old.jsonl");
    fs::write(&pushed_out, format!("alpha-skill {padding}")).unwrap();
    assert!(
        transcript_matches(&skills_dir, pushed_out.to_str().unwrap())
            .unwrap()
            .is_empty()
    );
}

#[test]
fn enforces_max_skills_and_max_chars_in_unicode_scalars() {
    let long_rule = "é".repeat(2990);
    let body = format!("- {long_rule} <!-- rule: no-lodgement -->\n");
    let root = fixture_root(
        &[
            ("skill-a", &body),
            ("skill-b", &body),
            ("skill-c", "Short <!-- rule: no-lodgement -->\n"),
            ("skill-d", "Short <!-- rule: no-lodgement -->\n"),
        ],
        json!({}),
    );
    let skills_dir = skills(&root);
    let chosen = vec![
        "skill-a".to_owned(),
        "skill-b".to_owned(),
        "skill-c".to_owned(),
        "skill-d".to_owned(),
    ];
    let text = context(&skills_dir, &chosen, "the prompt mentions it").unwrap();
    assert!(text.chars().count() <= MAX_CHARS);
    assert!(text.contains("skill-a"));
    assert!(!text.contains("skill-b"));
    assert!(!text.contains("skill-d"));
}

#[test]
fn formats_ascii_escaped_json_and_ignores_invalid_payloads() {
    let json_line = format_hook_output("UserPromptSubmit", "aé—\u{7f}\u{1f600}").unwrap();
    assert_eq!(
        json_line,
        r#"{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "a\u00e9\u2014\u007f\ud83d\ude00"}}"#
    );
    let root = fixture_root(
        &[("bas-preparation", "R <!-- rule: no-lodgement -->\n")],
        json!({}),
    );
    let non_str = serde_json::from_value::<Map<String, Value>>(json!({"prompt": 7})).unwrap();
    assert_eq!(run_mode(root.path(), "prompt", &non_str).unwrap(), "");
    let non_compact = serde_json::from_value::<Map<String, Value>>(
        json!({"source": "startup", "transcript_path": "missing"}),
    )
    .unwrap();
    assert_eq!(run_mode(root.path(), "compact", &non_compact).unwrap(), "");
}

#[test]
fn next_match_advances_along_utf8_boundaries_on_multibyte_text() {
    let collect = |phrase: &str, haystack: &str| {
        let re = compile_phrase(phrase).unwrap();
        let mut pos = 0;
        let mut hits = Vec::new();
        while let Some(start) = next_match(&re, haystack, &mut pos, phrase.is_empty()).unwrap() {
            hits.push(start);
        }
        hits
    };
    assert_eq!(collect("", ""), vec![0]);
    assert_eq!(collect("", "é"), Vec::<usize>::new());
    assert_eq!(collect("", "é—"), vec![5]);
    assert_eq!(collect("", "—é"), vec![0]);
    assert_eq!(collect("", "—é—"), vec![0, 8]);
    assert_eq!(collect("", "——"), vec![0, 3, 6]);
    assert_eq!(collect("é", "éé—é"), vec![7]);
}

#[test]
fn keywords_must_be_a_small_object_of_string_arrays() {
    let root = fixture_root(&[], json!({"bas-preparation": ["bas", "gst"]}));
    let keywords = load_keywords(&canonical(&root)).unwrap();
    assert_eq!(keywords["bas-preparation"], ["bas", "gst"]);
    let file = root.path().join("hooks/skill-keywords.json");
    for bad in [
        r#"["bas"]"#,
        r#"{"bas-preparation": "bas"}"#,
        r#"{"bas-preparation": [7]}"#,
        r#"{"bas-preparation": []} trailing"#,
    ] {
        fs::write(&file, bad).unwrap();
        assert!(load_keywords(&canonical(&root)).is_err(), "{bad}");
    }
    let padded = format!("{{}}{}", " ".repeat(MAX_KEYWORDS_BYTES as usize - 2));
    fs::write(&file, &padded).unwrap();
    assert!(load_keywords(&canonical(&root)).unwrap().is_empty());
    fs::write(&file, padded + " ").unwrap();
    assert!(load_keywords(&canonical(&root)).is_err());
}

#[test]
fn plural_endings_follow_python_ignore_case() {
    for (rest, len) in [
        ("", 0),
        ("s", 1),
        ("S!", 1),
        ("\u{17f}", 2),
        ("es", 2),
        ("ES", 2),
        ("e\u{17f}", 3),
        ("e", 0),
        ("ex", 0),
        ("x", 0),
    ] {
        assert_eq!(plural_suffix_len(rest), len, "{rest:?}");
    }
}

#[test]
fn lone_surrogate_escapes_become_replacement_characters() {
    for (input, expected) in [
        (r#"{"prompt": "bas"}"#, r#"{"prompt": "bas"}"#),
        (r#""\ud83d\ude00""#, r#""\ud83d\ude00""#),
        (r#""\ud83d bas""#, r#""\ufffd bas""#),
        (r#""\ude00\ud83d""#, r#""\ufffd\ufffd""#),
        (r#""\\ud800""#, r#""\\ud800""#),
        (r#""\\\ud800""#, r#""\\\ufffd""#),
        (
            r#""\u00e9\uDBFF\uDFFF\udc00x""#,
            r#""\u00e9\uDBFF\uDFFF\ufffdx""#,
        ),
        (r#""\ud8"#, r#""\ud8"#),
    ] {
        assert_eq!(super::replace_lone_surrogates(input), expected, "{input}");
    }
}
