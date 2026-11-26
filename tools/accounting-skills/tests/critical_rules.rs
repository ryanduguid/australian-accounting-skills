// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

use serde_json::{Value, json};
use std::{
    collections::BTreeMap,
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

#[test]
fn without_a_root_the_working_directory_is_not_read() {
    let out = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args(["critical-rules-hook", "prompt"])
        .current_dir(repository())
        .env_remove("CLAUDE_PLUGIN_ROOT")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .and_then(|mut child| {
            child
                .stdin
                .take()
                .unwrap()
                .write_all(br#"{"prompt": "bas-preparation"}"#)?;
            child.wait_with_output()
        })
        .unwrap();
    assert_eq!(
        (
            out.status.code(),
            out.stdout.as_slice(),
            out.stderr.as_slice()
        ),
        (Some(0), b"".as_slice(), b"".as_slice())
    );
}

/// A symbolic link on Unix and a junction on Windows, which needs no privilege.
fn link_folder(target: &Path, link: &Path) {
    #[cfg(unix)]
    std::os::unix::fs::symlink(target, link).unwrap();
    #[cfg(windows)]
    assert!(
        Command::new("cmd")
            .args(["/c", "mklink", "/J"])
            .arg(link)
            .arg(target)
            .output()
            .unwrap()
            .status
            .success()
    );
}

fn write_skill(skills: &Path, name: &str) {
    fs::create_dir_all(skills.join(name)).unwrap();
    fs::write(
        skills.join(name).join("SKILL.md"),
        format!("- {name} rule. <!-- rule: no-lodgement -->\n"),
    )
    .unwrap();
}

/// A plugin root holding `inside-skill`, and a keywords folder (a link to
/// `hooks_link_target` when given) whose file maps it to 'zebra'.
fn plugin_root(hooks_link_target: Option<&Path>) -> tempfile::TempDir {
    let root = tempfile::tempdir().unwrap();
    write_skill(&root.path().join(".claude").join("skills"), "inside-skill");
    match hooks_link_target {
        Some(target) => link_folder(target, &root.path().join("hooks")),
        None => {
            fs::create_dir_all(root.path().join("hooks")).unwrap();
            fs::write(root.path().join("hooks").join("skill-keywords.json"), ZEBRA).unwrap();
        }
    }
    root
}

const ZEBRA: &str = r#"{"inside-skill": ["zebra"]}"#;

fn prompt_output(root: &Path, text: &str) -> Output {
    run_hook(
        Some(root),
        None,
        &["prompt"],
        json!({"prompt": text}).to_string().as_bytes(),
    )
}

#[test]
fn linked_folders_are_not_followed_out_of_the_root() {
    let outside = tempfile::tempdir().unwrap();
    write_skill(outside.path(), "outside-skill");
    fs::create_dir_all(outside.path().join("hooks")).unwrap();
    fs::write(
        outside.path().join("hooks").join("skill-keywords.json"),
        ZEBRA,
    )
    .unwrap();

    // Real folders: the keyword attaches the inside skill; a linked skill never attaches.
    let root = plugin_root(None);
    let skills = root.path().join(".claude").join("skills");
    link_folder(
        &outside.path().join("outside-skill"),
        &skills.join("linked-skill"),
    );
    let text = attached(
        &prompt_output(root.path(), "zebra linked-skill outside-skill"),
        "UserPromptSubmit",
    );
    assert!(text.contains("inside-skill rule."), "{text}");
    assert!(!text.contains("outside-skill rule."), "{text}");

    // The keywords folder is a link: nothing is read through it.
    let linked_hooks = plugin_root(Some(&outside.path().join("hooks")));
    assert_eq!(prompt_output(linked_hooks.path(), "zebra").stdout, b"");

    // The skills folder itself is a link.
    let other = tempfile::tempdir().unwrap();
    fs::create_dir_all(other.path().join(".claude")).unwrap();
    fs::create_dir_all(other.path().join("hooks")).unwrap();
    fs::write(
        other.path().join("hooks").join("skill-keywords.json"),
        ZEBRA,
    )
    .unwrap();
    link_folder(&skills, &other.path().join(".claude").join("skills"));
    assert_eq!(
        prompt_output(other.path(), "zebra inside-skill").stdout,
        b""
    );
}

fn python_hook(mode: &str, stdin_bytes: &[u8]) -> Output {
    let python = std::env::var_os("PYTHON").unwrap_or_else(|| "python".into());
    let mut child = Command::new(python)
        .arg("-I")
        .arg(repository().join("hooks/critical_rules.py"))
        .arg(mode)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("Python runs hooks/critical_rules.py; set PYTHON to its path");
    child.stdin.take().unwrap().write_all(stdin_bytes).unwrap();
    child.wait_with_output().unwrap()
}

/// Runs both hooks on `stdin_bytes`, asserts the same exit code and output,
/// and says whether they attached anything.
fn assert_parity(mode: &str, stdin_bytes: &[u8]) -> bool {
    let rust = run_hook(Some(&repository()), None, &[mode], stdin_bytes);
    let python = python_hook(mode, stdin_bytes);
    let input = String::from_utf8_lossy(stdin_bytes);
    for (name, output) in [("Python", &python), ("Rust", &rust)] {
        assert!(
            output.stderr.is_empty(),
            "{name} {input}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    assert_eq!(
        (rust.status.code(), String::from_utf8_lossy(&rust.stdout)),
        (
            python.status.code(),
            String::from_utf8_lossy(&python.stdout)
        ),
        "{mode} {input}"
    );
    !rust.stdout.is_empty()
}

fn parity_prompts(keywords: &BTreeMap<String, Vec<String>>) -> Vec<String> {
    let skills: Vec<&String> = keywords.keys().collect();
    let mut prompts: Vec<String> = [
        "Draft the Negative Gearing schedule for 2026-27",
        "run au-pre-lodgement-review",
        "What time is it in Perth?",
        "basil pesto",
        "",
        "notfbtx",
        "Check PS\u{130} and PS\u{131} taxes; FBT, BAS, Div 7A and payroll tax",
        "taxe\u{17f} and BASes, fbt-like, fbt2, fbt_x, -bas, bas-",
        "\u{ff22}\u{ff21}\u{ff33} and \u{1d401}AS, \u{212a}, \u{e9}t\u{e9}, \u{1f600} bas",
    ]
    .map(str::to_owned)
    .to_vec();
    prompts.push(
        skills
            .iter()
            .map(|skill| skill.as_str())
            .collect::<Vec<_>>()
            .join(" "),
    );
    for chunk in skills.chunks(3) {
        prompts.push(format!(
            "{} then {}S, and {}es.",
            chunk[0].to_uppercase(),
            chunk.get(1).map_or("", |skill| skill.as_str()),
            chunk[chunk.len() - 1]
        ));
    }
    let phrases: Vec<&String> = keywords.values().flatten().collect();
    for chunk in phrases.chunks(3) {
        prompts.push(format!(
            "x{} {}; {}s? {}",
            chunk[0],
            chunk[chunk.len() - 1].to_uppercase(),
            chunk.get(1).map_or("", |phrase| phrase.as_str()),
            chunk[0]
        ));
    }
    prompts
}

/// The ported hook and `hooks/critical_rules.py` give the same exit code and
/// bytes on the same inputs: every skill name and keyword, case and plural
/// variants, near misses, the caps, bad payloads and compaction transcripts.
#[test]
fn matches_the_python_hook_on_the_same_inputs() {
    let repo = repository();
    let keywords: BTreeMap<String, Vec<String>> =
        serde_json::from_str(&fs::read_to_string(repo.join("hooks/skill-keywords.json")).unwrap())
            .unwrap();
    let prompts = parity_prompts(&keywords);
    let attached_count = prompts
        .iter()
        .filter(|prompt| assert_parity("prompt", json!({"prompt": prompt}).to_string().as_bytes()))
        .count();
    assert!(
        attached_count > prompts.len() / 2,
        "{attached_count} of {}",
        prompts.len()
    );

    for raw in [
        &b"\xff\xfe{"[..],
        b"not json",
        b"",
        b"[\"fbt\"]",
        br#"{"prompt": 7}"#,
        br#"{"prompt": "bas \ud83d then fbt"}"#,
        br#"{"prompt": "fbt", "prompt": "bas"}"#,
    ] {
        assert_parity("prompt", raw);
    }
    assert_parity("other", b"{}");

    let dir = tempfile::tempdir().unwrap();
    let mut transcripts = vec![
        b"{\"skill\":\"australian-accounting-skills:bas-preparation\"}\n\
          {\"skill\":\"australian-accounting-skills:fbt-annual-workflow\"}\n"
            .to_vec(),
        format!("bas-preparation {}", "x".repeat(1024 * 1024 + 16)).into_bytes(),
        keywords
            .keys()
            .map(|skill| format!("{skill}\n"))
            .collect::<String>()
            .into_bytes(),
    ];
    // A two-byte character cut by the 1 MiB tail, then invalid UTF-8.
    let mut cut = "\u{e9}".repeat(600 * 1024).into_bytes();
    cut.extend_from_slice(b" au-rental-property \xff\xfe fbt-annual-workflow");
    transcripts.push(cut);
    for (index, bytes) in transcripts.iter().enumerate() {
        let path = dir.path().join(format!("{index}.jsonl"));
        fs::write(&path, bytes).unwrap();
        for source in ["compact", "startup"] {
            let payload = json!({"source": source, "transcript_path": path}).to_string();
            assert_parity("compact", payload.as_bytes());
        }
    }
    let missing = json!({"source": "compact", "transcript_path": dir.path().join("absent")});
    assert_parity("compact", missing.to_string().as_bytes());
}
