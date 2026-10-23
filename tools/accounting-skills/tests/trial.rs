use accounting_skills::trial;
use serde_json::Value;
use std::{fs, path::Path};

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
    for (name, hash) in context["files"].as_object().unwrap() {
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
