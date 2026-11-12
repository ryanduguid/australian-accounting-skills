// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use accounting_skills::plugin_dist::{Files, MAX_ENTRIES, MAX_TEXT_BYTES, build, check, readme};
use std::{
    collections::BTreeSet,
    fs,
    path::{Path, PathBuf},
    process::Command,
};

const REPOSITORY: &str = "https://github.com/owner/plugin";

fn repository() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn git(root: &Path, args: &[&str]) -> Vec<u8> {
    static LOCAL_ENV: std::sync::OnceLock<Vec<String>> = std::sync::OnceLock::new();
    let local_env = LOCAL_ENV.get_or_init(|| {
        let output = Command::new("git")
            .args(["rev-parse", "--local-env-vars"])
            .output()
            .unwrap();
        assert!(output.status.success(), "{output:?}");
        String::from_utf8(output.stdout)
            .unwrap()
            .lines()
            .map(str::to_owned)
            .collect()
    });
    let mut command = Command::new("git");
    for name in local_env {
        command.env_remove(name);
    }
    let output = command.args(args).current_dir(root).output().unwrap();
    assert!(output.status.success(), "{args:?}: {output:?}");
    output.stdout
}

/// A committed repository holding a fabricated plugin and files it must not ship.
fn fixture(root: &Path, skip: &str) {
    let files: [(&str, &[u8]); 12] = [
        (
            ".claude-plugin/plugin.json",
            br#"{"name": "fixture", "repository": "https://github.com/owner/plugin"}"#,
        ),
        // A PNG signature and bytes that are not UTF-8.
        (".claude-plugin/icon.png", b"\x89PNG\r\n\x1a\n\xff\xfe"),
        (".claude-plugin/marketplace.json", b"{}"),
        (
            ".claude/skills/bas-preparation/SKILL.md",
            b"Read [the guide](references/guide.md).\n",
        ),
        (
            ".claude/skills/bas-preparation/references/guide.md",
            b"Back to [the skill](../SKILL.md).\n",
        ),
        (".claude/rules/rule.md", b"Fabricated rule\n"),
        ("DISCLAIMER.md", b"Fabricated disclaimer\n"),
        ("LICENSE", b"Fabricated licence\n"),
        ("NOTICE", b"Fabricated notice\n"),
        ("PRIVACY.md", b"Fabricated privacy policy\n"),
        (
            "README.md",
            b"![Banner](assets/banner.svg)\n[Guide](docs/guide.md#start) and [licence](LICENSE).\n",
        ),
        ("tests/fixture.bin", b"\xff\xfe"),
    ];
    for (path, bytes) in files {
        if path == skip {
            continue;
        }
        let path = root.join(path);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, bytes).unwrap();
    }
    git(root, &["init", "-q"]);
    git(root, &["add", "--all"]);
}

fn commit(root: &Path) {
    git(
        root,
        &[
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "--no-verify",
            "-m",
            "Fixture",
        ],
    );
}

fn listing(root: &Path) -> BTreeSet<String> {
    let mut found = BTreeSet::new();
    let mut pending = vec![root.to_path_buf()];
    while let Some(folder) = pending.pop() {
        for entry in fs::read_dir(folder).unwrap() {
            let path = entry.unwrap().path();
            if path.is_dir() {
                pending.push(path);
            } else {
                let relative = path.strip_prefix(root).unwrap();
                found.insert(relative.to_string_lossy().replace('\\', "/"));
            }
        }
    }
    found
}

#[test]
fn the_build_ships_only_the_plugin_and_rewrites_links_that_leave_it() {
    let directory = tempfile::tempdir().unwrap();
    let root = directory.path().join("repository");
    fs::create_dir(&root).unwrap();
    fixture(&root, "");
    commit(&root);
    // An uncommitted edit is not shipped: the build reads the commit.
    fs::write(root.join("LICENSE"), "Uncommitted licence\n").unwrap();
    let destination = directory.path().join("plugin");
    assert_eq!(build(&root, &destination).unwrap(), (10, 16));
    assert_eq!(
        listing(&destination),
        BTreeSet::from(
            [
                ".claude-plugin/icon.png",
                ".claude-plugin/plugin.json",
                ".claude/rules/rule.md",
                ".claude/skills/bas-preparation/SKILL.md",
                ".claude/skills/bas-preparation/references/guide.md",
                "DISCLAIMER.md",
                "LICENSE",
                "NOTICE",
                "PRIVACY.md",
                "README.md",
            ]
            .map(str::to_owned)
        )
    );
    assert_eq!(fs::read_to_string(destination.join("LICENSE")).unwrap(), "Fabricated licence\n");
    assert_eq!(
        fs::read_to_string(destination.join("README.md")).unwrap(),
        "![Banner](https://raw.githubusercontent.com/owner/plugin/main/assets/banner.svg)\n\
         [Guide](https://github.com/owner/plugin/blob/main/docs/guide.md#start) and [licence](LICENSE).\n"
    );
    // The destination must be new.
    assert!(build(&root, &destination).is_err());
}

#[test]
fn the_build_refuses_a_missing_path_and_an_executable_file() {
    let directory = tempfile::tempdir().unwrap();
    let missing = directory.path().join("missing");
    fs::create_dir(&missing).unwrap();
    fixture(&missing, ".claude-plugin/icon.png");
    commit(&missing);
    let error = build(&missing, &directory.path().join("a")).unwrap_err();
    assert_eq!(error.to_string(), ".claude-plugin/icon.png is not committed at HEAD");

    let executable = directory.path().join("executable");
    fs::create_dir(&executable).unwrap();
    fixture(&executable, "");
    git(&executable, &["update-index", "--chmod=+x", "NOTICE"]);
    commit(&executable);
    let error = build(&executable, &directory.path().join("b")).unwrap_err();
    assert_eq!(
        error.to_string(),
        "NOTICE must be a regular, non-executable file, not mode 100755"
    );
    assert!(!directory.path().join("b").exists());
}

#[test]
fn readme_keeps_shipped_targets_anchors_urls_and_code() {
    let shipped = BTreeSet::from(["LICENSE".to_owned(), ".claude".to_owned()]);
    let text = concat!(
        "<img src=\".github/assets/banner.svg\" width=\"100%\">\n",
        "<source srcset=\"./.github/assets/banner-light.svg\">\n",
        "[![Badge](.github/assets/badges/slsa.svg)](https://example.com/x)\n",
        "[Install](#install) · [Notes](RELEASE_NOTES.md#corrections) · [Licence](LICENSE) · [Skills](.claude)\n",
        "```\n[Not a link](docs/inside-code.md)\n```\n",
    );
    assert_eq!(
        readme(text, REPOSITORY, &shipped).unwrap(),
        concat!(
            "<img src=\"https://raw.githubusercontent.com/owner/plugin/main/.github/assets/banner.svg\" width=\"100%\">\n",
            "<source srcset=\"https://raw.githubusercontent.com/owner/plugin/main/.github/assets/banner-light.svg\">\n",
            "[![Badge](https://raw.githubusercontent.com/owner/plugin/main/.github/assets/badges/slsa.svg)](https://example.com/x)\n",
            "[Install](#install) · [Notes](https://github.com/owner/plugin/blob/main/RELEASE_NOTES.md#corrections) · [Licence](LICENSE) · [Skills](.claude)\n",
            "```\n[Not a link](docs/inside-code.md)\n```\n",
        )
    );
    assert!(readme("[x](../outside.md)\n", REPOSITORY, &shipped).is_err());
    assert!(readme("", "https://gitlab.com/owner/plugin", &shipped).is_err());
}

fn files(entries: &[(&str, &[u8])]) -> Files {
    entries
        .iter()
        .map(|(path, bytes)| ((*path).to_owned(), bytes.to_vec()))
        .collect()
}

#[test]
fn check_refuses_what_the_directory_would_hold_or_a_link_that_leaves_the_plugin() {
    let error = |files: &Files| check(files).unwrap_err().to_string();
    assert_eq!(
        check(&files(&[
            ("icon.png", b"\xff"),
            ("a/SKILL.md", b"[guide](references/guide.md#top) [web](https://example.com)"),
            ("a/references/guide.md", b"[skill](../SKILL.md)"),
        ]))
        .unwrap(),
        5
    );
    assert_eq!(
        error(&files(&[("source.bin", b"\xff")])),
        "source.bin is neither UTF-8 text nor an image the directory inspects"
    );
    let large = vec![b'a'; MAX_TEXT_BYTES + 1];
    assert_eq!(
        error(&files(&[("large.json", &large)])),
        format!("large.json has {} bytes; the directory inspects up to {MAX_TEXT_BYTES}", MAX_TEXT_BYTES + 1)
    );
    let many: Files = (0..MAX_ENTRIES).map(|n| (format!("f/{n}.md"), Vec::new())).collect();
    assert_eq!(
        error(&many),
        format!("the plugin has {} files and folders; the directory reads {MAX_ENTRIES}", MAX_ENTRIES + 1)
    );
    assert_eq!(
        error(&files(&[("a/SKILL.md", b"[policy](../../PRIVACY.md)")])),
        "a/SKILL.md links to ../../PRIVACY.md, which the plugin does not ship"
    );
}

#[test]
fn the_repository_plugin_fits_the_directory() {
    let directory = tempfile::tempdir().unwrap();
    let destination = directory.path().join("plugin");
    let root = fs::canonicalize(repository()).unwrap();
    let (count, entries) = build(&root, &destination).unwrap();
    assert!(entries <= MAX_ENTRIES, "{entries}");
    let top: BTreeSet<String> = fs::read_dir(&destination)
        .unwrap()
        .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
        .collect();
    assert_eq!(
        top,
        BTreeSet::from(
            [".claude", ".claude-plugin", "DISCLAIMER.md", "LICENSE", "NOTICE", "PRIVACY.md", "README.md"]
                .map(str::to_owned)
        )
    );
    // The manifest ships as committed, so its skills path and MCP pin are unchanged.
    assert_eq!(
        fs::read(destination.join(".claude-plugin/plugin.json")).unwrap(),
        git(&root, &["show", "HEAD:.claude-plugin/plugin.json"])
    );
    let committed = String::from_utf8(git(
        &root,
        &["ls-tree", "-r", "--name-only", "HEAD", "--", ".claude"],
    ))
    .unwrap();
    // The manifest and icon, the 4 notices and the README beside .claude.
    assert_eq!(count, committed.lines().count() + 7);
}
