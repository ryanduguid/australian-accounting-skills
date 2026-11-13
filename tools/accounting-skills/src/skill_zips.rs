// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! Build one upload ZIP per skill for hosts without a terminal. Each ZIP's only
//! root entry is the skill's folder, holding exactly one `SKILL.md`: the shape
//! Anthropic's article and OpenAI's Skills API guide describe. Each ZIP holds
//! the skill's files as committed at HEAD, in a fixed order with fixed
//! timestamps, so the same commit always gives the same bytes.
use crate::{Result, platform_text, plugin_dist::Files};
use std::{
    collections::{BTreeMap, BTreeSet},
    ffi::OsString,
    fs,
    io::{self, Write},
    path::{Path, PathBuf},
};

const SKILLS: &str = ".claude/skills";
/// 1 January 1980 at midnight in MS-DOS date and time fields, the earliest a
/// ZIP can record.
const DOS_TIME: u16 = 0;
const DOS_DATE: u16 = (1 << 5) | 1;
/// Version 2.0, the first with folders, needed to extract every entry.
const VERSION: u16 = 20;
/// File names are UTF-8.
const UTF8: u16 = 1 << 11;
/// The MS-DOS folder attribute.
const FOLDER: u32 = 0x10;

/// The skills at HEAD of `root`, each as its files' paths from inside the
/// skill folder `.claude/skills/NAME`, with their bytes.
pub fn skills(root: &Path) -> Result<BTreeMap<String, Files>> {
    let mut skills: BTreeMap<String, Files> = BTreeMap::new();
    for (path, bytes) in crate::plugin_dist::committed(root, &[(SKILLS, SKILLS)])? {
        // Git on Linux accepts `\` in a name; an extractor that reads it as a
        // separator could write outside its folder.
        if path.contains('\\') || path.split('/').any(|part| matches!(part, "" | "." | "..")) {
            return Err(format!("{path:?} cannot be a ZIP entry name").into());
        }
        let inside = path
            .strip_prefix(&format!("{SKILLS}/"))
            .ok_or("git listed a path outside the skills folder")?;
        let (skill, rest) = inside
            .split_once('/')
            .ok_or_else(|| format!("{path} is not inside a skill folder"))?;
        skills
            .entry(skill.to_owned())
            .or_default()
            .insert(rest.to_owned(), bytes);
    }
    for (skill, files) in &skills {
        let manifests: Vec<&String> = files
            .keys()
            .filter(|path| {
                path.rsplit('/')
                    .next()
                    .is_some_and(|name| name.eq_ignore_ascii_case("SKILL.md"))
            })
            .collect();
        if manifests != ["SKILL.md"] {
            return Err(format!(
                "{SKILLS}/{skill} must hold exactly one SKILL.md, at its root; found {manifests:?}"
            )
            .into());
        }
    }
    Ok(skills)
}

fn crc32(bytes: &[u8]) -> u32 {
    let mut crc = u32::MAX;
    for byte in bytes {
        crc ^= u32::from(*byte);
        for _ in 0..8 {
            crc = if crc & 1 == 1 {
                (crc >> 1) ^ 0xEDB8_8320
            } else {
                crc >> 1
            };
        }
    }
    !crc
}

/// A ZIP of `entries` stored without compression: a name ending in `/` is a
/// folder. shortcut: stored, not deflated, because skills are small text
/// files; deflate them if a host's upload limit ever bites.
fn zip(entries: &BTreeMap<String, &[u8]>) -> Result<Vec<u8>> {
    let narrow = |value: usize| u32::try_from(value).map_err(|_| "a ZIP over 4 GiB needs ZIP64");
    let mut archive = Vec::new();
    let mut directory = Vec::new();
    for (name, bytes) in entries {
        let offset = narrow(archive.len())?;
        let size = narrow(bytes.len())?;
        let length = u16::try_from(name.len()).map_err(|_| "a ZIP entry name is too long")?;
        let crc = crc32(bytes);
        let mut common = Vec::new();
        for field in [VERSION, UTF8, 0, DOS_TIME, DOS_DATE] {
            common.extend(field.to_le_bytes());
        }
        for field in [crc, size, size] {
            common.extend(field.to_le_bytes());
        }
        common.extend(length.to_le_bytes());
        // No extra field.
        common.extend(0u16.to_le_bytes());

        archive.extend(0x0403_4b50u32.to_le_bytes());
        archive.extend(&common);
        archive.extend(name.as_bytes());
        archive.extend(*bytes);

        directory.extend(0x0201_4b50u32.to_le_bytes());
        // Made by version 2.0 on MS-DOS, so the attributes below are DOS ones.
        directory.extend(VERSION.to_le_bytes());
        directory.extend(&common);
        // No comment, disk 0, no internal attributes.
        for field in [0u16, 0, 0] {
            directory.extend(field.to_le_bytes());
        }
        let attributes = if name.ends_with('/') { FOLDER } else { 0 };
        directory.extend(attributes.to_le_bytes());
        directory.extend(offset.to_le_bytes());
        directory.extend(name.as_bytes());
    }
    let count =
        u16::try_from(entries.len()).map_err(|_| "a ZIP over 65,535 entries needs ZIP64")?;
    let start = narrow(archive.len())?;
    let length = narrow(directory.len())?;
    archive.extend(directory);
    archive.extend(0x0605_4b50u32.to_le_bytes());
    // This disk and the directory's disk are both 0.
    for field in [0u16, 0, count, count] {
        archive.extend(field.to_le_bytes());
    }
    archive.extend(length.to_le_bytes());
    archive.extend(start.to_le_bytes());
    // No comment.
    archive.extend(0u16.to_le_bytes());
    Ok(archive)
}

/// The upload ZIP of one skill: its folder, each subfolder and each file,
/// under the skill's name.
pub fn skill_zip(skill: &str, files: &Files) -> Result<Vec<u8>> {
    let mut entries: BTreeMap<String, &[u8]> = BTreeMap::new();
    let mut folders = BTreeSet::from([format!("{skill}/")]);
    for (path, bytes) in files {
        if let Some((parent, _)) = path.rsplit_once('/') {
            let mut folder = format!("{skill}/");
            for part in parent.split('/') {
                folder.push_str(part);
                folder.push('/');
                folders.insert(folder.clone());
            }
        }
        entries.insert(format!("{skill}/{path}"), bytes);
    }
    for folder in folders {
        entries.insert(folder, &[]);
    }
    zip(&entries)
}

/// Write `NAME.zip` for each skill at HEAD of `root` into the new folder
/// `destination`, and return how many were written.
pub fn build(root: &Path, destination: &Path) -> Result<usize> {
    let skills = skills(root)?;
    fs::create_dir_all(destination.parent().ok_or("destination has no parent")?)?;
    fs::create_dir(destination)?;
    for (skill, files) in &skills {
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(destination.join(format!("{skill}.zip")))?
            .write_all(&skill_zip(skill, files)?)?;
    }
    Ok(skills.len())
}

pub fn cli(mut args: impl Iterator<Item = OsString>) -> Result<u8> {
    let usage = "usage: accounting-skills build-skill-zips DESTINATION [--root PATH]";
    let mut destination = None;
    let mut root = std::env::current_dir()?;
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--help" | "-h") => {
                println!("{usage}");
                return Ok(0);
            }
            Some("--root") => match args
                .next()
                .filter(|value| !value.as_encoded_bytes().starts_with(b"-"))
            {
                Some(value) => root = value.into(),
                None => {
                    eprintln!("{usage}");
                    return Ok(2);
                }
            },
            Some(value) if !value.starts_with('-') && destination.is_none() => {
                destination = Some(PathBuf::from(&arg));
            }
            _ => {
                eprintln!("{usage}");
                return Ok(2);
            }
        }
    }
    let Some(destination) = destination else {
        eprintln!("{usage}");
        return Ok(2);
    };
    let root = crate::canonical_root(&root)?;
    let count = build(&root, &destination)?;
    io::stdout().write_all(
        platform_text(&format!(
            "built {count} skill ZIPs in {}\n",
            destination.display()
        ))
        .as_bytes(),
    )?;
    Ok(0)
}
