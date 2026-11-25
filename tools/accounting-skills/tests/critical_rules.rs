// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

use serde_json::{Value, json};
use std::{
    fs,
    io::Write,
    path::{Path, PathBuf},
    process::{Command, Output, Stdio},
};

fn repository() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn run_hook(
    root: Option<&Path>,
    env_root: Option<&Path>,
    args: &[&str],
    stdin_bytes: &[u8],
) -> Output {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_accounting-skills"));
    cmd.arg("critical-rules-hook").args(args);
    if let Some(root) = root {
        cmd.arg("--root").arg(root);
    }
    match env_root {
        Some(path) => {
            cmd.env("CLAUDE_PLUGIN_ROOT", path);
        }
        None => {
            cmd.env_remove("CLAUDE_PLUGIN_ROOT");
        }
    }
    cmd.stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = cmd.spawn().unwrap();
    child.stdin.take().unwrap().write_all(stdin_bytes).unwrap();
    child.wait_with_output().unwrap()
}

fn attached(output: &Output, expected_event: &str) -> String {
    assert_eq!(output.status.code(), Some(0));
    assert!(
        output.stderr.is_empty(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let text = String::from_utf8(output.stdout.clone()).unwrap();
    let data: Value = serde_json::from_str(text.trim_end()).unwrap();
    assert_eq!(data["hookSpecificOutput"]["hookEventName"], expected_event);
    data["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap()
        .to_owned()
}

#[test]
fn prompt_mode_attaches_rules_via_root_and_claude_plugin_root() {
    let repo = repository();
    let payload = json!({"prompt": "Draft the Negative Gearing schedule for 2026-27"}).to_string();
    let via_flag = run_hook(Some(&repo), None, &["prompt"], payload.as_bytes());
    let text = attached(&via_flag, "UserPromptSubmit");
    assert!(text.contains("skill au-rental-property (the prompt mentions it)"));
    assert!(text.contains("Never supply rates, thresholds, labels or deadlines from memory."));
    assert!(!text.contains("<!--"));

    let outside = tempfile::tempdir().unwrap();
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_accounting-skills"));
    cmd.args(["critical-rules-hook", "prompt"])
        .current_dir(outside.path())
        .env("CLAUDE_PLUGIN_ROOT", &repo)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = cmd.spawn().unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(payload.as_bytes())
        .unwrap();
    let via_env = child.wait_with_output().unwrap();
    assert_eq!(via_env.stdout, via_flag.stdout);
}

#[test]
fn compact_mode_reads_tail_and_ignores_non_compact_or_missing_transcript() {
    let repo = repository();
    let dir = tempfile::tempdir().unwrap();
    let transcript = dir.path().join("session.jsonl");
    fs::write(
        &transcript,
        "{\"skill\":\"australian-accounting-skills:bas-preparation\"}\n\
         {\"skill\":\"australian-accounting-skills:fbt-annual-workflow\"}\n",
    )
    .unwrap();
    let payload = json!({"source": "compact", "transcript_path": transcript}).to_string();
    let out = run_hook(Some(&repo), None, &["compact"], payload.as_bytes());
    let text = attached(&out, "SessionStart");
    assert!(text.find("fbt-annual-workflow").unwrap() < text.find("bas-preparation").unwrap());
    assert!(text.contains("used before compaction"));

    let tail_only = dir.path().join("large.jsonl");
    fs::write(
        &tail_only,
        format!("bas-preparation {}", "x".repeat(1024 * 1024 + 16)),
    )
    .unwrap();
    let tail_payload = json!({"source": "compact", "transcript_path": tail_only}).to_string();
    let tail_out = run_hook(Some(&repo), None, &["compact"], tail_payload.as_bytes());
    assert_eq!(
        (
            tail_out.status.code(),
            tail_out.stdout.as_slice(),
            tail_out.stderr.as_slice()
        ),
        (Some(0), b"".as_slice(), b"".as_slice())
    );

    let missing = dir.path().join("absent.jsonl");
    let miss_payload = json!({"source": "compact", "transcript_path": missing}).to_string();
    let miss_out = run_hook(Some(&repo), None, &["compact"], miss_payload.as_bytes());
    assert_eq!(
        (
            miss_out.status.code(),
            miss_out.stdout.as_slice(),
            miss_out.stderr.as_slice()
        ),
        (Some(0), b"".as_slice(), b"".as_slice())
    );
}

#[test]
fn bad_inputs_and_unknown_modes_fail_open_silently() {
    let repo = repository();
    for (args, input) in [
        (&["prompt"][..], b"\xff\xfe{" as &[u8]),
        (&["prompt"][..], b"not json"),
        (&["prompt"][..], b""),
        (&["prompt"][..], b"[\"fbt\"]"),
        (&["prompt"][..], br#"{"prompt": 7}"#),
        (&["other"][..], b"{}"),
        (&[][..], b"{}"),
        (&["prompt", "extra"][..], br#"{"prompt": "bas"}"#),
    ] {
        let out = run_hook(Some(&repo), None, args, input);
        assert_eq!(
            (
                out.status.code(),
                out.stdout.as_slice(),
                out.stderr.as_slice()
            ),
            (Some(0), b"".as_slice(), b"".as_slice()),
            "args={args:?}"
        );
    }
    let missing_root = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args(["critical-rules-hook", "--root"])
        .stdin(Stdio::null())
        .output()
        .unwrap();
    assert_eq!(
        (
            missing_root.status.code(),
            missing_root.stdout.as_slice(),
            missing_root.stderr.as_slice()
        ),
        (Some(0), b"".as_slice(), b"".as_slice())
    );
}
