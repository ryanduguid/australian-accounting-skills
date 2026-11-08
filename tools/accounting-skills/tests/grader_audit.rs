// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use std::{fs, path::Path, process::Command};

const CLEAN: &str = r#"{"type":"assistant","message":{"content":[{"type":"text","text":"I will not open evals/"},{"type":"tool_use","name":"Read","input":{"file_path":"/tmp/copy/skills/bas-preparation/SKILL.md"}}]}}"#;

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
    write(folder.path(), "run-1", &[CLEAN, ""]);
    assert_eq!(
        audit(folder.path(), &["."]),
        (0, "traces=1 flagged=0\n".into(), String::new())
    );

    let read = r#"{"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"/tmp/copy/evals/graders.yaml"}}]}}"#;
    write(folder.path(), "run-2", &[read]);
    let expected = format!(
        "FLAG {}\n  Read {{\"file_path\": \"/tmp/copy/evals/graders.yaml\"}}\ntraces=2 flagged=1\n",
        shown("run-2")
    );
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
fn an_unread_line_or_an_empty_audit_fails() {
    let folder = tempfile::tempdir().unwrap();
    write(
        folder.path(),
        "run",
        &[CLEAN, "{\"message\": {\"content\": [", "NaN"],
    );
    let (code, stdout, stderr) = audit(folder.path(), &["run"]);
    assert_eq!((code, stdout.as_str()), (1, "traces=1 flagged=0\n"));
    let trace = shown("run");
    assert_eq!(
        stderr,
        format!(
            "SKIP {trace}:2 is not JSON, so its tool calls were not audited\nSKIP {trace}:3 is not JSON, so its tool calls were not audited\n"
        )
    );

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
