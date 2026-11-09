// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use std::{fs, path::Path, process::Command};

const CLEAN: &str = r#"{"type":"assistant","message":{"content":[{"type":"text","text":"I will not open evals/"},{"type":"tool_use","name":"Read","input":{"file_path":"/tmp/copy/skills/bas-preparation/SKILL.md"}}]}}"#;
const READ: &str = r#"{"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"/tmp/copy/evals/graders.yaml"}}]}}"#;
const READ_HIT: &str = "  Read {\"file_path\": \"/tmp/copy/evals/graders.yaml\"}";
/// Folder names that only contain a suspect word stay clean.
const NEAR_MISSES: &str = r#"{"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"/copy/evals-old/x"}},{"type":"tool_use","name":"Read","input":{"file_path":"/copy/withheld/x"}},{"type":"tool_use","name":"Read","input":{"file_path":"C:\\copy\\graders2\\x"}},{"type":"tool_use","name":"Read","input":{"file_path":"/copy/invalidation/x"}}]}}"#;

fn write(root: &Path, run: &str, lines: &[&str]) {
    let folder = root.join(run);
    fs::create_dir_all(&folder).unwrap();
    fs::write(folder.join("output.jsonl"), lines.join("\n") + "\n").unwrap();
}

fn audit(root: &Path, args: &[&str]) -> (i32, String, String) {
    let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .arg("audit-grader-reads")
        .args(args)
        .current_dir(root)
        .output()
        .unwrap();
    let text = |bytes: Vec<u8>| String::from_utf8(bytes).unwrap().replace("\r\n", "\n");
    (
        output.status.code().unwrap(),
        text(output.stdout),
        text(output.stderr),
    )
}

fn shown(run: &str) -> String {
    run.split('/')
        .chain(["output.jsonl"])
        .collect::<std::path::PathBuf>()
        .display()
        .to_string()
}

#[test]
fn a_trace_that_names_the_graders_fails_and_a_clean_one_passes() {
    let folder = tempfile::tempdir().unwrap();
    write(folder.path(), "run-1", &[CLEAN, NEAR_MISSES, ""]);
    assert_eq!(
        audit(folder.path(), &["."]),
        (0, "traces=1 flagged=0\n".into(), String::new())
    );

    write(folder.path(), "run-2", &[READ]);
    let expected = format!("FLAG {}\n{READ_HIT}\ntraces=2 flagged=1\n", shown("run-2"));
    assert_eq!(audit(folder.path(), &["."]), (1, expected, String::new()));
}

/// Python's re.I reads a dotless or dotted I as `i`.
#[test]
fn a_dotless_or_dotted_i_still_matches() {
    let folder = tempfile::tempdir().unwrap();
    let call = |input: &str| {
        format!(
            r#"{{"message":{{"content":[{{"type":"tool_use","name":"Read","input":{{"p":"{input}"}}}}]}}}}"#
        )
    };
    let (dotless, dotted) = (call("/copy/val\u{131}dat\u{131}on/x"), call("rubr\u{130}c"));
    write(folder.path(), "run", &[dotless.as_str(), dotted.as_str()]);
    let expected = format!(
        "FLAG {}\n  Read {{\"p\": \"/copy/val\u{131}dat\u{131}on/x\"}}\n  Read {{\"p\": \"rubr\u{130}c\"}}\ntraces=1 flagged=1\n",
        shown("run")
    );
    assert_eq!(audit(folder.path(), &["."]), (1, expected, String::new()));
}

/// Python's rglob and path sort ignore case on Windows only.
#[test]
fn trace_names_and_order_follow_the_platform_case_rule() {
    let folder = tempfile::tempdir().unwrap();
    write(folder.path(), "B", &[READ]);
    write(folder.path(), "a", &[READ]);
    fs::create_dir(folder.path().join("c")).unwrap();
    fs::write(folder.path().join("c/Output.JSONL"), format!("{READ}\n")).unwrap();
    let flag = |path: String| format!("FLAG {path}\n{READ_HIT}\n");
    let expected = if cfg!(windows) {
        format!(
            "{}{}{}traces=3 flagged=3\n",
            flag(shown("a")),
            flag(shown("B")),
            flag(shown("c"))
        )
    } else {
        format!(
            "{}{}traces=2 flagged=2\n",
            flag(shown("B")),
            flag(shown("a"))
        )
    };
    assert_eq!(audit(folder.path(), &["."]), (1, expected, String::new()));
}

/// The expected report is what `audit_grader_reads.py` printed for these lines,
/// apart from the Glob call: the original split its record at the raw U+2028
/// and so never saw it. Traces sort by path component, as Python sorts paths.
#[test]
fn the_report_keeps_the_original_scripts_spelling() {
    let folder = tempfile::tempdir().unwrap();
    let long = format!(
        r#"{{"message":{{"content":[{{"type":"tool_use","name":"Bash","input":{{"command":"cat C:\\copy\\HELD\\{}"}}}}]}}}}"#,
        "x".repeat(300)
    );
    let grep = r#"{"message":{"content":[{"type":"tool_use","name":"Grep","input":{"pattern":"ſkill-fired"}}]}}"#;
    let lines = [
        r#"{"message":{"content":[{"type":"tool_use","input":{"pattern":"RUBRIC","n":1e16,"x":[1,true,null,0.0001,1e15,2.5e-05],"é":"\u0007"}}]}}"#,
        long.as_str(),
        "{\"message\":{\"content\":[{\"type\":\"tool_use\",\"name\":\"Glob\",\"input\":{\"path\":\"/copy\u{2028}/evals/\"}}]}}",
        grep,
        grep,
        grep,
    ];
    write(folder.path(), "b", &lines);
    write(folder.path(), "a-b", &[grep]);
    write(folder.path(), "a/b", &[grep]);
    let cut: String = format!(
        r#"{{"command": "cat C:\\copy\\HELD\\{}"}}"#,
        "x".repeat(300)
    )
    .chars()
    .take(200)
    .collect();
    let hit = "  Grep {\"pattern\": \"ſkill-fired\"}";
    let expected = format!(
        "FLAG {}\n{hit}\nFLAG {}\n{hit}\nFLAG {}\n  None {{\"pattern\": \"RUBRIC\", \"n\": 1e+16, \"x\": [1, true, null, 0.0001, 1000000000000000.0, 2.5e-05], \"é\": \"\\u0007\"}}\n  Bash {cut}\n  Glob {{\"path\": \"/copy\u{2028}/evals/\"}}\n{hit}\n{hit}\ntraces=3 flagged=3\n",
        shown("a/b"),
        shown("a-b"),
        shown("b"),
    );
    assert_eq!(audit(folder.path(), &["./"]), (1, expected, String::new()));
}

#[test]
fn invalid_utf8_cannot_pass_the_audit() {
    let folder = tempfile::tempdir().unwrap();
    write(folder.path(), "croft-manor", &[CLEAN]);
    let trace = shown("croft-manor");
    let path = folder.path().join(&trace);
    let mut bytes = fs::read(&path).unwrap();
    bytes.extend_from_slice(
        b"{\"message\":{\"content\":[{\"type\":\"text\",\"text\":\"\xff\"}]}}\n",
    );
    fs::write(path, bytes).unwrap();

    let (code, stdout, stderr) = audit(folder.path(), &["."]);
    assert_eq!((code, stdout.as_str()), (1, "traces=1 flagged=0\n"));
    assert_eq!(
        stderr,
        format!("SKIP {trace}:2 is not a JSON object, so its tool calls were not audited\n")
    );
}

#[test]
fn an_unread_line_or_an_empty_audit_fails() {
    let folder = tempfile::tempdir().unwrap();
    write(
        folder.path(),
        "run",
        &[CLEAN, "{\"message\": {\"content\": [", "NaN", "[1, 2]"],
    );
    let (code, stdout, stderr) = audit(folder.path(), &["run"]);
    assert_eq!((code, stdout.as_str()), (1, "traces=1 flagged=0\n"));
    let trace = shown("run");
    let skipped: String = (2..=4)
        .map(|line| {
            format!(
                "SKIP {trace}:{line} is not a JSON object, so its tool calls were not audited\n"
            )
        })
        .collect();
    assert_eq!(stderr, skipped);

    fs::create_dir(folder.path().join("empty")).unwrap();
    assert_eq!(
        audit(folder.path(), &["empty"]),
        (
            1,
            "traces=0 flagged=0\n".into(),
            "no output.jsonl trace found, so nothing was audited\n".into()
        )
    );
    let (code, _, stderr) = audit(folder.path(), &["missing"]);
    assert_eq!(code, 1);
    assert!(stderr.starts_with("FAIL missing: "), "{stderr}");
    let (code, _, stderr) = audit(folder.path(), &[]);
    assert_eq!(
        (code, stderr.as_str()),
        (
            1,
            "FAIL usage: accounting-skills audit-grader-reads ROOT...\n"
        )
    );
}
