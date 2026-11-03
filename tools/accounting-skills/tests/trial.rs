use accounting_skills::trial;
use serde_json::{Value, json};
use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
};

fn card() -> Vec<u8> {
    b"---\nid: example\nsynthetic: true\ntarget_skills: [example]\n---\n## Scenario\n\nFabricated\n\n## Task\n\nPrepare\n\n## Synthetic inputs\n\nNone\n\n## Deliberately unavailable evidence\n\nMissing\n\n## Required checks\n\nWithheld\n".to_vec()
}
fn setup(root: &Path) {
    fs::create_dir_all(root.join("validation/cases")).unwrap();
    fs::write(root.join("validation/cases/example.md"), card()).unwrap();
    fs::create_dir_all(root.join(".claude/skills/example/references")).unwrap();
    fs::write(
        root.join(".claude/skills/example/SKILL.md"),
        b"Fabricated skill\n",
    )
    .unwrap();
    fs::write(
        root.join(".claude/skills/example/references/context.md"),
        b"Fabricated context\r\n",
    )
    .unwrap();
}

#[test]
fn packet_has_exact_rubric_hashes_and_task_sections_without_answers() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    setup(root.path());
    let destination = outside.path().join("trial");
    trial::prepare("example", &destination, "model-𝄞", "runtime", root.path()).unwrap();
    let rubric = fs::read(destination.join("rubric.md")).unwrap();
    let task = fs::read(destination.join("input.md")).unwrap();
    assert_eq!(rubric, card());
    assert!(!String::from_utf8_lossy(&task).contains("Withheld"));
    let raw = fs::read(destination.join("context.json")).unwrap();
    assert!(raw.is_ascii());
    assert!(!raw.contains(&b'\r'));
    let context: Value = serde_json::from_slice(&raw).unwrap();
    assert_eq!(context["model"], "model-𝄞");
    assert_eq!(context["input_sha256"], trial::digest(&task));
    assert_eq!(context["rubric_sha256"], trial::digest(&rubric));
    let files = context["files"].as_object().unwrap();
    // Nested files are recorded; their directories are not. The order follows
    // the platform's path ordering, so compare the names alone.
    let mut names: Vec<_> = files.keys().map(String::as_str).collect();
    names.sort_unstable();
    assert_eq!(
        names,
        [
            ".claude/skills/example/SKILL.md",
            ".claude/skills/example/references/context.md"
        ]
    );
    for (name, hash) in files {
        assert_eq!(
            hash,
            &Value::String(trial::digest(&fs::read(root.path().join(name)).unwrap()))
        );
    }
    assert!(
        trial::prepare("example", &destination, "x", "y", root.path())
            .unwrap_err()
            .to_string()
            .contains("already exists")
    );
    assert_eq!(fs::read(destination.join("rubric.md")).unwrap(), rubric);
}

#[test]
fn privacy_names_and_missing_skills_fail_without_creating_a_packet() {
    for name in [
        "x.key",
        "x.KEY",
        "x.PEM",
        "x.Key",
        "x.tokenſ",
        ".ENV",
        ".env.local",
        "directory.tokens",
    ] {
        let root = tempfile::tempdir().unwrap();
        let outside = tempfile::tempdir().unwrap();
        setup(root.path());
        fs::write(
            root.path().join(".claude/skills/example").join(name),
            b"Fabricated non-secret sentinel",
        )
        .unwrap();
        let destination = outside.path().join("trial");
        assert!(
            trial::prepare("example", &destination, "x", "y", root.path())
                .unwrap_err()
                .to_string()
                .contains("credential files")
        );
        assert!(!destination.exists());
    }
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    setup(root.path());
    fs::remove_file(root.path().join(".claude/skills/example/SKILL.md")).unwrap();
    assert!(
        trial::prepare(
            "example",
            &outside.path().join("trial"),
            "x",
            "y",
            root.path()
        )
        .unwrap_err()
        .to_string()
        .contains("missing skill")
    );
}

#[test]
fn schema_and_duplicate_grading_sections_are_checked() {
    let mut bytes = card();
    bytes.extend_from_slice(b"\n## Required checks\nDuplicate\n");
    assert!(
        trial::task_input(&bytes, "example.md")
            .unwrap_err()
            .to_string()
            .contains("duplicate section")
    );
    let bytes = String::from_utf8(card())
        .unwrap()
        .replace("synthetic: true", "synthetic: false");
    assert!(trial::task_input(bytes.as_bytes(), "example.md").is_err());
    for bad in ["../example", "Example", "example/other", ""] {
        let root = tempfile::tempdir().unwrap();
        assert!(
            trial::prepare(bad, &root.path().join("new"), "x", "y", root.path())
                .unwrap_err()
                .to_string()
                .contains("slug")
        );
    }
}

#[cfg(any(unix, windows))]
#[test]
fn linked_card_and_context_ancestors_are_rejected_before_contents() {
    for target in ["validation/cases/example.md", ".claude"] {
        let root = tempfile::tempdir().unwrap();
        let outside = tempfile::tempdir().unwrap();
        setup(root.path());
        let source = root.path().join(target);
        let saved = root.path().join("saved");
        fs::rename(&source, &saved).unwrap();
        #[cfg(unix)]
        std::os::unix::fs::symlink(&saved, &source).unwrap();
        #[cfg(windows)]
        if saved.is_dir() {
            std::os::windows::fs::symlink_dir(&saved, &source).unwrap();
        } else {
            std::os::windows::fs::symlink_file(&saved, &source).unwrap();
        }
        let destination = outside.path().join("trial");
        assert!(
            trial::prepare("example", &destination, "x", "y", root.path())
                .unwrap_err()
                .to_string()
                .contains("symbolic links")
        );
        assert!(!destination.exists());
    }
}

#[cfg(any(unix, windows))]
#[test]
fn a_linked_skill_folder_or_skill_file_is_rejected_before_packet_creation() {
    for target in [".claude/skills/example", ".claude/skills/example/SKILL.md"] {
        let root = tempfile::tempdir().unwrap();
        let outside = tempfile::tempdir().unwrap();
        setup(root.path());
        let source = root.path().join(target);
        let saved = outside.path().join("saved");
        fs::rename(&source, &saved).unwrap();
        #[cfg(unix)]
        std::os::unix::fs::symlink(&saved, &source).unwrap();
        #[cfg(windows)]
        if saved.is_dir() {
            std::os::windows::fs::symlink_dir(&saved, &source).unwrap();
        } else {
            std::os::windows::fs::symlink_file(&saved, &source).unwrap();
        }
        let destination = outside.path().join("trial");
        let error = trial::prepare("example", &destination, "x", "y", root.path()).unwrap_err();
        assert!(error.to_string().contains("symbolic links"), "{target}");
        assert!(!destination.exists());
    }
}

fn repository() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

const CASE: &str = "month-end-mismatched-period";

#[test]
fn every_current_card_can_be_prepared_without_its_grading_sections() {
    let mut cards = 0;
    for entry in fs::read_dir(repository().join("validation/cases")).unwrap() {
        let path = entry.unwrap().path();
        if path.extension().is_none_or(|suffix| suffix != "md") {
            continue;
        }
        let name = path.file_name().unwrap().to_str().unwrap();
        let (task, skills) = trial::task_input(&fs::read(&path).unwrap(), name).unwrap();
        let task = String::from_utf8(task).unwrap();
        assert!(!skills.is_empty(), "{name}");
        assert_eq!(task.matches("## ").count(), 4, "{name}");
        for withheld in [
            "## Required checks",
            "## Must not do",
            "## Source-verification and reviewer boundary",
        ] {
            assert!(!task.contains(withheld), "{name}");
        }
        cards += 1;
    }
    assert!(cards > 100, "{cards}");
}

#[test]
fn a_current_card_binds_exact_repository_bytes() {
    let outside = tempfile::tempdir().unwrap();
    let destination = outside.path().join("trial");
    trial::prepare(
        CASE,
        &destination,
        "unselected",
        "unselected",
        &repository(),
    )
    .unwrap();
    let context: Value =
        serde_json::from_slice(&fs::read(destination.join("context.json")).unwrap()).unwrap();
    let files = context["files"].as_object().unwrap();
    assert!(!files.is_empty());
    for (relative, expected) in files {
        assert_eq!(
            expected,
            &Value::String(trial::digest(
                &fs::read(repository().join(relative)).unwrap()
            )),
            "{relative}"
        );
    }
    assert_eq!(
        context["rubric_sha256"],
        trial::digest(&fs::read(repository().join(format!("validation/cases/{CASE}.md"))).unwrap())
    );
}

#[test]
fn repository_output_and_missing_task_sections_are_refused() {
    let error = trial::prepare(
        CASE,
        &repository().join("trial"),
        "unselected",
        "unselected",
        &repository(),
    )
    .unwrap_err();
    assert!(
        error.to_string().contains("outside the repository"),
        "{error}"
    );
    assert!(!repository().join("trial").exists());
    let card =
        fs::read_to_string(repository().join(format!("validation/cases/{CASE}.md"))).unwrap();
    let name = format!("{CASE}.md");
    let error = trial::task_input(card.replace("## Task", "## Omitted").as_bytes(), &name)
        .unwrap_err()
        .to_string();
    assert!(
        error.starts_with("missing task sections: ['Task']"),
        "{error}"
    );
    let error = trial::task_input(
        format!("{card}\n## Task\nInjected answer\n").as_bytes(),
        &name,
    )
    .unwrap_err()
    .to_string();
    assert_eq!(error, "duplicate section: Task");
}

fn command(args: &[&std::ffi::OsStr], root: &Path) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .arg("prepare-trial")
        .args(args)
        .arg("--root")
        .arg(root)
        .output()
        .unwrap()
}

#[test]
fn the_command_keeps_the_selected_model_and_runtime_and_refuses_bad_use() {
    let root = tempfile::tempdir().unwrap();
    let outside = tempfile::tempdir().unwrap();
    setup(root.path());
    let destination = outside.path().join("trial");
    let output = command(
        &[
            "example".as_ref(),
            destination.as_os_str(),
            "--model".as_ref(),
            "test-model".as_ref(),
            "--runtime".as_ref(),
            "test-runtime".as_ref(),
        ],
        root.path(),
    );
    assert_eq!(output.status.code(), Some(0), "{output:?}");
    let context: Value =
        serde_json::from_slice(&fs::read(destination.join("context.json")).unwrap()).unwrap();
    assert_eq!(
        (&context["model"], &context["runtime"]),
        (&json!("test-model"), &json!("test-runtime"))
    );
    let saved = fs::read(destination.join("context.json")).unwrap();
    let inside = root.path().join("trial");
    let traversal = outside.path().join("traversal");
    let missing = outside.path().join("missing");
    for (args, code) in [
        (vec!["example".as_ref(), destination.as_os_str()], 1),
        (vec!["example".as_ref(), inside.as_os_str()], 1),
        (vec!["../example".as_ref(), traversal.as_os_str()], 1),
        (vec!["absent".as_ref(), missing.as_os_str()], 1),
        (vec![], 2),
        (vec!["example".as_ref()], 2),
        (
            vec!["example".as_ref(), missing.as_os_str(), "--other".as_ref()],
            2,
        ),
        (
            vec!["example".as_ref(), missing.as_os_str(), "--model".as_ref()],
            2,
        ),
    ] {
        let output = command(&args, root.path());
        assert_eq!(output.status.code(), Some(code), "{args:?}: {output:?}");
    }
    assert_eq!(fs::read(destination.join("context.json")).unwrap(), saved);
    for path in [inside, traversal, missing] {
        assert!(!path.exists());
    }
}
