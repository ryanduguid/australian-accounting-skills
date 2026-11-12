// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use accounting_skills::plugin_dist::{Files, MAX_ENTRIES, MAX_TEXT_BYTES, build, check, manifest};
use serde_json::{Value, json};
use std::{
    collections::BTreeSet,
    fs,
    path::{Path, PathBuf},
    process::Command,
};

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
    let files: [(&str, &[u8]); 13] = [
        (
            ".claude-plugin/plugin.json",
            br#"{"name": "fixture", "version": "1.0.0", "skills": "./.claude/skills", "mcpServers": {"local": {"command": "uvx"}}}"#,
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
        ("README.md", b"The repository README\n"),
        ("docs/plugin-directory-readme.md", b"The listing README\n"),
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
fn the_build_ships_the_skills_in_skills_without_the_mcp_server() {
    let directory = tempfile::tempdir().unwrap();
    let root = directory.path().join("repository");
    fs::create_dir(&root).unwrap();
    fixture(&root, "");
    commit(&root);
    // An uncommitted edit is not shipped: the build reads the commit.
    fs::write(root.join("LICENSE"), "Uncommitted licence\n").unwrap();
    let destination = directory.path().join("plugin");
    assert_eq!(build(&root, &destination).unwrap(), (9, 13));
    assert_eq!(
        listing(&destination),
        BTreeSet::from(
            [
                ".claude-plugin/icon.png",
                ".claude-plugin/plugin.json",
                "DISCLAIMER.md",
                "LICENSE",
                "NOTICE",
                "PRIVACY.md",
                "README.md",
                "skills/bas-preparation/SKILL.md",
                "skills/bas-preparation/references/guide.md",
            ]
            .map(str::to_owned)
        )
    );
    assert_eq!(
        fs::read_to_string(destination.join("LICENSE")).unwrap(),
        "Fabricated licence\n"
    );
    assert_eq!(
        fs::read_to_string(destination.join("README.md")).unwrap(),
        "The listing README\n"
    );
    let shipped: Value =
        serde_json::from_slice(&fs::read(destination.join(".claude-plugin/plugin.json")).unwrap())
            .unwrap();
    assert_eq!(
        shipped,
        json!({"name": "fixture", "version": "1.0.0", "skills": "./skills"})
    );
    // The destination must be new.
    assert!(build(&root, &destination).is_err());
}

#[test]
fn the_build_refuses_a_missing_path_and_an_executable_file() {
    let directory = tempfile::tempdir().unwrap();
    let missing = directory.path().join("missing");
    fs::create_dir(&missing).unwrap();
    fixture(&missing, "docs/plugin-directory-readme.md");
    commit(&missing);
    let error = build(&missing, &directory.path().join("a")).unwrap_err();
    assert_eq!(
        error.to_string(),
        "docs/plugin-directory-readme.md is not committed at HEAD"
    );

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
fn manifest_drops_only_the_mcp_servers_and_refuses_an_unknown_component() {
    let source = br#"{"$schema": "s", "name": "n", "version": "2.0.0", "skills": "./.claude/skills", "keywords": ["a"], "mcpServers": {}}"#;
    let shipped = String::from_utf8(manifest(source).unwrap()).unwrap();
    // Key order is kept, with the skills path in place.
    assert_eq!(
        shipped,
        "{\n  \"$schema\": \"s\",\n  \"name\": \"n\",\n  \"version\": \"2.0.0\",\n  \"skills\": \"./skills\",\n  \"keywords\": [\n    \"a\"\n  ]\n}\n"
    );
    for key in ["hooks", "lspServers", "monitors", "commands", "agents"] {
        let source = format!(r#"{{"name": "n", "{key}": "./x"}}"#);
        assert_eq!(
            manifest(source.as_bytes()).unwrap_err().to_string(),
            format!("plugin.json key {key} is not one the directory build ships")
        );
    }
}

fn files(entries: &[(&str, &[u8])]) -> Files {
    entries
        .iter()
        .map(|(path, bytes)| ((*path).to_owned(), bytes.to_vec()))
        .collect()
}

#[test]
fn check_refuses_what_the_directory_would_refuse_or_a_link_that_leaves_the_plugin() {
    let error = |files: &Files| check(files).unwrap_err().to_string();
    assert_eq!(
        check(&files(&[
            ("icon.png", b"\xff"),
            ("LICENSE", b"Licence"),
            (
                "skills/a/SKILL.md",
                b"[guide](references/guide.md#top) [web](https://example.com)"
            ),
            ("skills/a/references/guide.md", b"[skill](../SKILL.md)"),
            ("skills/a/sources.json", b"{}"),
            ("notes.txt", b""),
            ("config.yaml", b""),
        ]))
        .unwrap(),
        10
    );
    for (path, message) in [
        (
            "source.bin",
            "source.bin is not a file type the directory accepts",
        ),
        (
            "skills/a/verify.py",
            "skills/a/verify.py is not a file type the directory accepts",
        ),
        (
            "skills/LICENSE",
            "skills/LICENSE is not a file type the directory accepts",
        ),
        (
            ".claude/skills/a/SKILL.md",
            ".claude/skills/a/SKILL.md is in a folder the directory refuses",
        ),
        (
            "skills/.claude-plugin/plugin.json",
            "skills/.claude-plugin/plugin.json is in a folder the directory refuses",
        ),
        (
            "skills/a/hooks.json",
            "skills/a/hooks.json is a file the directory refuses",
        ),
        (".mcp.json", ".mcp.json is a file the directory refuses"),
        (
            "package.json",
            "package.json is a file the directory refuses",
        ),
    ] {
        assert_eq!(error(&files(&[(path, b"{}")])), message);
    }
    for bytes in [&b"\xff"[..], b"a\0b", b"#!/bin/sh\n"] {
        assert_eq!(
            error(&files(&[("a.md", bytes)])),
            "a.md must be UTF-8 text without NUL bytes or a #! line"
        );
    }
    let large = vec![b'a'; MAX_TEXT_BYTES + 1];
    assert_eq!(
        error(&files(&[("large.json", &large)])),
        format!(
            "large.json has {} bytes; the directory accepts up to {MAX_TEXT_BYTES}",
            MAX_TEXT_BYTES + 1
        )
    );
    // 510 files and their folder are 511 entries, which fits; one more file does not.
    let fits: Files = (0..MAX_ENTRIES - 2)
        .map(|n| (format!("f/{n}.md"), Vec::new()))
        .collect();
    assert_eq!(check(&fits).unwrap(), MAX_ENTRIES - 1);
    let many: Files = (0..MAX_ENTRIES - 1)
        .map(|n| (format!("f/{n}.md"), Vec::new()))
        .collect();
    assert_eq!(
        error(&many),
        format!(
            "the plugin has {MAX_ENTRIES} files and folders; the directory needs fewer than {MAX_ENTRIES}"
        )
    );
    assert_eq!(
        error(&files(&[(
            "skills/a/SKILL.md",
            b"[policy](../../../PRIVACY.md)"
        )])),
        "skills/a/SKILL.md links to ../../../PRIVACY.md, which the plugin does not ship"
    );
}

#[test]
fn the_repository_plugin_fits_the_directory() {
    let directory = tempfile::tempdir().unwrap();
    let destination = directory.path().join("plugin");
    let root = fs::canonicalize(repository()).unwrap();
    let (count, entries) = build(&root, &destination).unwrap();
    assert!(entries < MAX_ENTRIES, "{entries}");
    let top: BTreeSet<String> = fs::read_dir(&destination)
        .unwrap()
        .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
        .collect();
    assert_eq!(
        top,
        BTreeSet::from(
            [
                ".claude-plugin",
                "DISCLAIMER.md",
                "LICENSE",
                "NOTICE",
                "PRIVACY.md",
                "README.md",
                "skills"
            ]
            .map(str::to_owned)
        )
    );
    // The shipped manifest is main's without its MCP server, skills moved.
    let mut expected: Value =
        serde_json::from_slice(&git(&root, &["show", "HEAD:.claude-plugin/plugin.json"])).unwrap();
    expected
        .as_object_mut()
        .unwrap()
        .remove("mcpServers")
        .unwrap();
    expected["skills"] = json!("./skills");
    let shipped: Value =
        serde_json::from_slice(&fs::read(destination.join(".claude-plugin/plugin.json")).unwrap())
            .unwrap();
    assert_eq!(shipped, expected);
    let committed = String::from_utf8(git(
        &root,
        &[
            "ls-tree",
            "-r",
            "--name-only",
            "HEAD",
            "--",
            ".claude/skills",
        ],
    ))
    .unwrap();
    // Every committed skill file ships byte for byte under skills/.
    for path in committed.lines() {
        let shipped = destination.join(path.strip_prefix(".claude/").unwrap());
        assert_eq!(
            fs::read(&shipped).unwrap(),
            git(&root, &["show", &format!("HEAD:{path}")]),
            "{path}"
        );
    }
    // The manifest, icon, README and 4 notices beside the skills.
    assert_eq!(count, committed.lines().count() + 7);
}
