// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use accounting_skills::skill_zips::build;
use std::{
    collections::BTreeMap,
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

/// A committed repository holding `files`.
fn fixture(root: &Path, files: &[(&str, &[u8])]) {
    for (path, bytes) in files {
        let path = root.join(path);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, bytes).unwrap();
    }
    git(root, &["init", "-q"]);
    git(root, &["add", "--all"]);
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

fn crc32(bytes: &[u8]) -> u32 {
    let table: Vec<u32> = (0..256u32)
        .map(|mut value| {
            for _ in 0..8 {
                value = if value & 1 == 1 {
                    0xEDB8_8320 ^ (value >> 1)
                } else {
                    value >> 1
                };
            }
            value
        })
        .collect();
    !bytes.iter().fold(u32::MAX, |crc, byte| {
        table[((crc ^ u32::from(*byte)) & 0xFF) as usize] ^ (crc >> 8)
    })
}

fn u16_at(bytes: &[u8], at: usize) -> usize {
    usize::from(u16::from_le_bytes([bytes[at], bytes[at + 1]]))
}

fn u32_at(bytes: &[u8], at: usize) -> u32 {
    u32::from_le_bytes(bytes[at..at + 4].try_into().unwrap())
}

/// Read a stored ZIP through its central directory, checking each local
/// header, size and CRC-32 on the way.
fn unzip(archive: &[u8]) -> BTreeMap<String, Vec<u8>> {
    let end = archive.len() - 22;
    assert_eq!(
        u32_at(archive, end),
        0x0605_4b50,
        "end of central directory"
    );
    let count = u16_at(archive, end + 10);
    let mut at = u32_at(archive, end + 16) as usize;
    let mut entries = BTreeMap::new();
    for _ in 0..count {
        assert_eq!(u32_at(archive, at), 0x0201_4b50, "central directory header");
        assert_eq!(u16_at(archive, at + 10), 0, "stored");
        let crc = u32_at(archive, at + 16);
        let size = u32_at(archive, at + 24) as usize;
        let name_length = u16_at(archive, at + 28);
        let skipped = u16_at(archive, at + 30) + u16_at(archive, at + 32);
        let local = u32_at(archive, at + 42) as usize;
        let name = String::from_utf8(archive[at + 46..at + 46 + name_length].to_vec()).unwrap();
        assert_eq!(
            u32_at(archive, local),
            0x0403_4b50,
            "local header of {name}"
        );
        assert_eq!(
            &archive[local + 30..local + 30 + name_length],
            name.as_bytes()
        );
        let data = local + 30 + name_length + u16_at(archive, local + 28);
        let bytes = archive[data..data + size].to_vec();
        assert_eq!(crc32(&bytes), crc, "CRC-32 of {name}");
        assert!(entries.insert(name, bytes).is_none(), "repeated entry");
        at += 46 + name_length + skipped;
    }
    entries
}

/// The shape both hosts document: the skill's folder is the only root entry,
/// and it holds exactly one SKILL.md, at its root.
fn assert_upload_shape(skill: &str, entries: &BTreeMap<String, Vec<u8>>) {
    let roots: Vec<&str> = entries
        .keys()
        .map(|name| name.split('/').next().unwrap())
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .collect();
    assert_eq!(roots, [skill], "root entries");
    assert!(entries.contains_key(&format!("{skill}/")));
    let manifests: Vec<&String> = entries
        .keys()
        .filter(|name| {
            name.rsplit('/')
                .next()
                .is_some_and(|file| file.eq_ignore_ascii_case("SKILL.md"))
        })
        .collect();
    assert_eq!(manifests, [&format!("{skill}/SKILL.md")]);
}

#[test]
fn the_crc_matches_the_standard_check_value() {
    assert_eq!(crc32(b"123456789"), 0xCBF4_3926);
}

#[test]
fn each_skill_becomes_one_upload_zip_of_its_committed_files() {
    let root = tempfile::tempdir().unwrap();
    fixture(
        root.path(),
        &[
            (
                ".claude/skills/alpha/SKILL.md",
                b"---\nname: alpha\n---\nAlpha\n",
            ),
            (".claude/skills/alpha/references/guide.md", b"Guide\n"),
            (".claude/skills/alpha/references/deep/table.json", b"{}\n"),
            (
                ".claude/skills/beta/SKILL.md",
                b"---\nname: beta\n---\nBeta\n",
            ),
            ("README.md", b"Not a skill\n"),
        ],
    );
    // An uncommitted edit or file does not reach the ZIP.
    fs::write(
        root.path().join(".claude/skills/beta/SKILL.md"),
        b"Edited\n",
    )
    .unwrap();
    fs::write(
        root.path().join(".claude/skills/alpha/untracked.md"),
        b"Untracked\n",
    )
    .unwrap();
    let out = tempfile::tempdir().unwrap();
    assert_eq!(build(root.path(), &out.path().join("first")).unwrap(), 2);
    let names: Vec<String> = fs::read_dir(out.path().join("first"))
        .unwrap()
        .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .collect();
    assert_eq!(names, ["alpha.zip", "beta.zip"]);

    let alpha = unzip(&fs::read(out.path().join("first/alpha.zip")).unwrap());
    assert_upload_shape("alpha", &alpha);
    let expected: BTreeMap<String, Vec<u8>> = [
        ("alpha/", &b""[..]),
        ("alpha/SKILL.md", b"---\nname: alpha\n---\nAlpha\n"),
        ("alpha/references/", b""),
        ("alpha/references/deep/", b""),
        ("alpha/references/deep/table.json", b"{}\n"),
        ("alpha/references/guide.md", b"Guide\n"),
    ]
    .into_iter()
    .map(|(name, bytes)| (name.to_owned(), bytes.to_vec()))
    .collect();
    assert_eq!(alpha, expected);
    let beta = unzip(&fs::read(out.path().join("first/beta.zip")).unwrap());
    assert_upload_shape("beta", &beta);
    assert_eq!(beta["beta/SKILL.md"], b"---\nname: beta\n---\nBeta\n");

    // The same commit gives the same bytes.
    build(root.path(), &out.path().join("second")).unwrap();
    for name in names {
        assert_eq!(
            fs::read(out.path().join("first").join(&name)).unwrap(),
            fs::read(out.path().join("second").join(&name)).unwrap()
        );
    }
    // An existing destination is refused.
    assert!(build(root.path(), &out.path().join("first")).is_err());
}

#[test]
fn a_second_skill_manifest_inside_a_skill_is_refused() {
    let root = tempfile::tempdir().unwrap();
    fixture(
        root.path(),
        &[
            (".claude/skills/alpha/SKILL.md", b"Alpha\n"),
            (".claude/skills/alpha/references/skill.md", b"Nested\n"),
        ],
    );
    let out = tempfile::tempdir().unwrap();
    let error = build(root.path(), &out.path().join("zips"))
        .unwrap_err()
        .to_string();
    assert!(error.contains("must hold exactly one SKILL.md"), "{error}");
    assert!(!out.path().join("zips").exists());
}

#[test]
fn the_command_builds_into_a_new_folder_and_refuses_a_missing_destination() {
    let root = tempfile::tempdir().unwrap();
    fixture(
        root.path(),
        &[(".claude/skills/alpha/SKILL.md", b"Alpha\n")],
    );
    let out = tempfile::tempdir().unwrap();
    let destination = out.path().join("zips");
    let run = |args: &[&std::ffi::OsStr]| {
        Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
            .arg("build-skill-zips")
            .args(args)
            .output()
            .unwrap()
    };
    let output = run(&[
        destination.as_os_str(),
        "--root".as_ref(),
        root.path().as_os_str(),
    ]);
    assert_eq!(output.status.code(), Some(0), "{output:?}");
    assert!(
        String::from_utf8(output.stdout)
            .unwrap()
            .starts_with("built 1 skill ZIPs in ")
    );
    assert!(destination.join("alpha.zip").is_file());
    assert_eq!(
        run(&["--root".as_ref(), root.path().as_os_str()])
            .status
            .code(),
        Some(2)
    );
}

#[test]
fn every_skill_in_the_repository_builds_an_upload_zip() {
    let root = fs::canonicalize(repository()).unwrap();
    let listing = String::from_utf8(git(
        &root,
        &["ls-tree", "-d", "--name-only", "HEAD", ".claude/skills/"],
    ))
    .unwrap();
    let skills: Vec<&str> = listing
        .lines()
        .map(|path| path.trim_start_matches(".claude/skills/"))
        .collect();
    let out = tempfile::tempdir().unwrap();
    assert_eq!(
        build(&root, &out.path().join("zips")).unwrap(),
        skills.len()
    );
    for skill in skills {
        let entries = unzip(&fs::read(out.path().join(format!("zips/{skill}.zip"))).unwrap());
        assert_upload_shape(skill, &entries);
    }
}
