use accounting_skills::{source_passages as p, source_refresh::Fetched};
use serde_json::{Value, json};
use std::{fs, path::Path};

const URL: &str = "https://www.ato.gov.au/fabricated-passages";
fn index(root: &Path) -> std::path::PathBuf {
    let skills = root.join(".claude/skills");
    fs::create_dir_all(skills.join("example")).unwrap();
    fs::write(
        skills.join("example/sources.json"),
        json!({"sources":[{"url":URL}]}).to_string(),
    )
    .unwrap();
    skills
}
fn value(text: &str) -> Value {
    json!({"url":URL,"final_url":URL,"available":true,"text_truncated":false,"source_digest":"a".repeat(64),"text":text,"text_sha256":accounting_skills::source_refresh::content_digest(text)})
}

#[test]
fn capture_checks_membership_before_fetch_and_preserves_the_index() {
    let root = tempfile::tempdir().unwrap();
    let skills = index(root.path());
    let file = skills.join("example/sources.json");
    let before = fs::read(&file).unwrap();
    let result = p::snapshot_with(&format!("{URL}#fragment"), &skills, |target| {
        assert_eq!(target, URL);
        Ok(Fetched {
            status: Some(200),
            final_url: URL.into(),
            digest: "a".repeat(64),
            text: "fabricated".into(),
            ..Default::default()
        })
    })
    .unwrap();
    assert_eq!(result["available"], true);
    assert_eq!(result["url"], URL);
    assert!(
        p::snapshot_with("https://www.ato.gov.au/unindexed", &skills, |_| panic!(
            "must not fetch"
        ))
        .is_err()
    );
    assert_eq!(fs::read(file).unwrap(), before);
}

#[test]
fn snapshot_validation_checks_flags_digest_and_unicode_character_bounds() {
    let root = tempfile::tempdir().unwrap();
    let skills = index(root.path());
    let path = root.path().join("snapshot.json");
    let base = value(&"𝄞".repeat(32768));
    fs::write(&path, base.to_string()).unwrap();
    assert_eq!(p::load_snapshot(&path, &skills).unwrap(), base);
    for key in ["available", "text_truncated"] {
        for bad in [json!(0), json!(1), json!("true"), Value::Null] {
            let mut bad_value = base.clone();
            bad_value[key] = bad;
            fs::write(&path, bad_value.to_string()).unwrap();
            assert!(p::load_snapshot(&path, &skills).is_err());
        }
    }
    for bad in [value(&"𝄞".repeat(32769)), json!({"text":7})] {
        fs::write(&path, bad.to_string()).unwrap();
        assert!(p::load_snapshot(&path, &skills).is_err());
    }
    fs::write(&path, vec![b'x'; 1024 * 1024 + 1]).unwrap();
    assert!(
        p::load_snapshot(&path, &skills)
            .unwrap_err()
            .to_string()
            .contains("1 MiB")
    );
}

#[test]
fn comparison_marks_all_truncation_causes_including_unshown_lines() {
    let old = value("a");
    for text in ["new\n".repeat(100), "𝄞".repeat(240), "a\n".repeat(401)] {
        let result = p::compare(&old, &value(&text)).unwrap();
        assert_eq!(result["comparison_truncated"], true);
        let lines = result["passage_diff"].as_array().unwrap();
        assert!(lines.len() <= 60);
        assert!(
            lines
                .iter()
                .all(|line| line.as_str().unwrap().chars().count() <= 240)
        );
    }
    assert_eq!(p::compare(&old, &old).unwrap()["status"], "same");
    let mut changed = old.clone();
    changed["source_digest"] = json!("b".repeat(64));
    let result = p::compare(&old, &changed).unwrap();
    assert_eq!(result["status"], "different");
    assert_eq!(result["passage_diff"], json!([]));
    changed["available"] = json!(false);
    assert_eq!(p::compare(&old, &changed).unwrap()["status"], "unavailable");
}

#[test]
fn cli_exclusively_creates_external_outputs_and_refuses_repository_paths() {
    let root = tempfile::tempdir().unwrap();
    let external = tempfile::tempdir().unwrap();
    index(root.path());
    let snapshot = external.path().join("before.json");
    fs::write(&snapshot, value("fabricated").to_string()).unwrap();
    let output = external.path().join("nested/report.json");
    let run = |output: &Path| {
        p::cli(
            [
                "compare".into(),
                "--root".into(),
                root.path().into(),
                "--before".into(),
                snapshot.clone().into(),
                "--after".into(),
                snapshot.clone().into(),
                "--output".into(),
                output.into(),
            ]
            .into_iter(),
        )
        .unwrap()
    };
    assert_eq!(run(&output), 0);
    let bytes = fs::read(&output).unwrap();
    assert_eq!(run(&output), 2);
    assert_eq!(fs::read(&output).unwrap(), bytes);
    assert_eq!(run(&root.path().join("new/sub/report.json")), 2);
    assert!(!root.path().join("new").exists());
}

#[cfg(unix)]
#[test]
fn output_resolution_follows_links_before_parent_components() {
    use std::os::unix::fs::symlink;
    let root = tempfile::tempdir().unwrap();
    let external = tempfile::tempdir().unwrap();
    index(root.path());
    fs::create_dir(root.path().join("nested")).unwrap();
    symlink(root.path().join("nested"), external.path().join("link")).unwrap();
    let output = external.path().join("link/../forbidden.json");
    let args = [
        "snapshot".into(),
        "--url".into(),
        URL.into(),
        "--root".into(),
        root.path().into(),
        "--output".into(),
        output.into(),
    ];
    assert_eq!(p::cli(args.into_iter()).unwrap(), 2);
    assert!(!root.path().join("forbidden.json").exists());
}

#[cfg(any(unix, windows))]
fn directory_link(target: &Path, link: &Path) {
    #[cfg(unix)]
    std::os::unix::fs::symlink(target, link).unwrap();
    #[cfg(windows)]
    std::os::windows::fs::symlink_dir(target, link).unwrap();
}

#[cfg(any(unix, windows))]
#[test]
fn resolution_failure_is_processing_error_and_never_fetches_or_writes() {
    let root = tempfile::tempdir().unwrap();
    let external = tempfile::tempdir().unwrap();
    index(root.path());
    let link = external.path().join("cycle");
    directory_link(&link, &link);
    let output = link.join("report.json");
    let args = [
        "snapshot".into(),
        "--url".into(),
        URL.into(),
        "--root".into(),
        root.path().into(),
        "--output".into(),
        output.into(),
    ];
    assert_eq!(p::cli(args.into_iter()).unwrap(), 1);
    assert!(!root.path().join("report.json").exists());
}

#[cfg(windows)]
#[test]
fn inverse_windows_link_parent_spelling_is_refused_before_fetch() {
    let root = tempfile::tempdir().unwrap();
    let external = tempfile::tempdir().unwrap();
    index(root.path());
    let nested = external.path().join("nested");
    fs::create_dir(&nested).unwrap();
    let link = root.path().join("outside-link");
    directory_link(&nested, &link);
    let output = link.join("../report.json");
    let args = [
        "snapshot".into(),
        "--url".into(),
        URL.into(),
        "--root".into(),
        root.path().into(),
        "--output".into(),
        output.into(),
    ];
    assert_eq!(p::cli(args.into_iter()).unwrap(), 2);
    assert!(!root.path().join("report.json").exists());
    assert!(!external.path().join("report.json").exists());
}
