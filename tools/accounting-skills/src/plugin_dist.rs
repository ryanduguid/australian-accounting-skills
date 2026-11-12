// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! Build the plugin as the Claude plugin directory reads it. The directory
//! refuses, from an organisation it has not verified, a local MCP server, a
//! file type other than Markdown, text, JSON, YAML or an image, and skills
//! outside `skills/`. So this build takes from the checked-out commit only the
//! skills and the files the listing needs, moves the skills to `skills/` and
//! ships a manifest without the MCP server. The full plugin stays on `main`.
use crate::{Result, platform_text};
use serde_json::{Map, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    ffi::OsString,
    fs,
    io::{self, BufRead, BufReader, Read, Write},
    path::{Path, PathBuf},
    process::{Command, Stdio},
};

/// Each committed path or folder the build ships, and where it ships it.
pub const SOURCES: [(&str, &str); 9] = [
    (MANIFEST, MANIFEST),
    (".claude-plugin/icon.png", ".claude-plugin/icon.png"),
    (".claude/skills", "skills"),
    ("DISCLAIMER.md", "DISCLAIMER.md"),
    ("LICENSE", "LICENSE"),
    ("NOTICE", "NOTICE"),
    ("PRIVACY.md", "PRIVACY.md"),
    // DISCLAIMER.md and PRIVACY.md link to it.
    ("SECURITY.md", "SECURITY.md"),
    ("docs/plugin-directory-readme.md", "README.md"),
];
const MANIFEST: &str = ".claude-plugin/plugin.json";
/// The manifest keys the build ships unchanged. Any other key fails the build,
/// so a component added on `main` is never shipped or dropped unnoticed.
const MANIFEST_KEYS: [&str; 13] = [
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "privacyPolicyUrl",
    "documentationUrl",
    "supportUrl",
    "keywords",
    "skills",
];
/// The directory refuses a version with this many files and folders or more.
pub const MAX_ENTRIES: usize = 512;
/// The directory refuses a file larger than this, images aside.
pub const MAX_TEXT_BYTES: usize = 256 * 1024;
const TEXT: [&str; 5] = ["md", "txt", "json", "yaml", "yml"];
const IMAGES: [&str; 6] = ["png", "jpg", "jpeg", "gif", "webp", "ico"];
/// Text files without an extension that may sit at the plugin root.
const BARE_TEXT: [&str; 2] = ["LICENSE", "NOTICE"];
/// Names the directory refuses whatever their type: component files the
/// manifest does not name, and package manager configs.
const REFUSED_NAMES: [&str; 13] = [
    "hooks.json",
    ".mcp.json",
    ".lsp.json",
    "monitors.json",
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    ".yarnrc.yml",
    "bower.json",
    "composer.json",
    "deno.json",
];

/// Files keyed by their path relative to the plugin folder.
pub type Files = BTreeMap<String, Vec<u8>>;

fn extension(path: &str) -> String {
    Path::new(path)
        .extension()
        .and_then(|extension| extension.to_str())
        .unwrap_or_default()
        .to_ascii_lowercase()
}

/// Every folder that holds a file, without the plugin folder itself.
fn folders(files: &Files) -> BTreeSet<String> {
    files
        .keys()
        .flat_map(|path| {
            path.match_indices('/')
                .map(move |(slash, _)| path[..slash].to_owned())
        })
        .collect()
}

/// The Markdown link and image targets and the HTML `src` and `srcset`
/// values in `text`, outside fenced code blocks.
fn targets(text: &str) -> Vec<&str> {
    let mut found = Vec::new();
    let mut fenced = false;
    for line in text.split_inclusive('\n') {
        let trimmed = line.trim_start();
        if trimmed.starts_with("```") || trimmed.starts_with("~~~") {
            fenced = !fenced;
        } else if !fenced {
            for opener in ["](", "src=\"", "srcset=\""] {
                let mut from = 0;
                while let Some(at) = line[from..].find(opener) {
                    let start = from + at + opener.len();
                    let end = line[start..]
                        .find([')', '"', ' ', '\t', '\n'])
                        .map_or(line.len(), |length| start + length);
                    found.push(&line[start..end]);
                    from = end;
                }
            }
        }
    }
    found
}

/// The path part of a target that names a file in this plugin, or `None` for
/// a URL, an anchor or an empty target.
fn local(target: &str) -> Option<&str> {
    let path = target.split('#').next().unwrap_or_default();
    (!path.is_empty() && !target.contains(':')).then_some(path)
}

/// `path` relative to `base`, with `.` and `..` resolved, or `None` when it
/// climbs out of the plugin folder.
fn resolve(base: &str, path: &str) -> Option<String> {
    let mut parts: Vec<&str> = base.split('/').filter(|part| !part.is_empty()).collect();
    for part in path.split('/') {
        match part {
            "" | "." => {}
            ".." => {
                parts.pop()?;
            }
            _ => parts.push(part),
        }
    }
    Some(parts.join("/"))
}

/// Whether `version` is X.Y.Z without leading zeros. The workflow publishes
/// only a higher version, compared with `sort -V`, which orders a pre-release
/// above its release and 0.6.00 above 0.6.0.
fn plain_version(version: &str) -> bool {
    let parts: Vec<&str> = version.split('.').collect();
    let plain = |part: &&str| {
        !part.is_empty()
            && part.bytes().all(|byte| byte.is_ascii_digit())
            && (*part == "0" || !part.starts_with('0'))
    };
    parts.len() == 3 && parts.iter().all(plain)
}

/// The manifest the directory reads: `main`'s, without its MCP servers and
/// with the skills at `./skills`.
pub fn manifest(bytes: &[u8]) -> Result<Vec<u8>> {
    let mut manifest: Map<String, Value> = serde_json::from_slice(bytes)?;
    manifest.shift_remove("mcpServers");
    if let Some(key) = manifest
        .keys()
        .find(|key| !MANIFEST_KEYS.contains(&key.as_str()))
    {
        return Err(format!("plugin.json key {key} is not one the directory build ships").into());
    }
    let version = manifest.get("version").and_then(Value::as_str);
    if !version.is_some_and(plain_version) {
        return Err("plugin.json version must be X.Y.Z".into());
    }
    manifest.insert("skills".to_owned(), Value::from("./skills"));
    let mut out = serde_json::to_vec_pretty(&manifest)?;
    out.push(b'\n');
    Ok(out)
}

/// Refuse a file the directory would refuse, and say whether it is Markdown,
/// whose links `check` then resolves.
fn accept(path: &str, bytes: &[u8]) -> Result<bool> {
    let parts: Vec<&str> = path.split('/').collect();
    if parts.contains(&".claude") || parts[1..].contains(&".claude-plugin") {
        return Err(format!("{path} is in a folder the directory refuses").into());
    }
    if REFUSED_NAMES.contains(&parts[parts.len() - 1]) {
        return Err(format!("{path} is a file the directory refuses").into());
    }
    if bytes.starts_with(b"#!") {
        return Err(format!("{path} starts with #!, which the directory refuses").into());
    }
    let kind = extension(path);
    if IMAGES.contains(&kind.as_str()) {
        return Ok(false);
    }
    if !TEXT.contains(&kind.as_str()) && !BARE_TEXT.contains(&path) {
        return Err(format!("{path} is not a file type the directory accepts").into());
    }
    if bytes.len() > MAX_TEXT_BYTES {
        return Err(format!(
            "{path} has {} bytes; the directory accepts up to {MAX_TEXT_BYTES}",
            bytes.len()
        )
        .into());
    }
    if std::str::from_utf8(bytes).is_err() || bytes.contains(&0) {
        return Err(format!("{path} must be UTF-8 text without NUL bytes").into());
    }
    Ok(kind == "md")
}

/// Refuse a plugin the directory would refuse, or one whose Markdown links
/// leave it, and return its count of files and folders.
pub fn check(files: &Files) -> Result<usize> {
    let folders = folders(files);
    let entries = files.len() + folders.len();
    if entries >= MAX_ENTRIES {
        return Err(format!(
            "the plugin has {entries} files and folders; the directory needs fewer than {MAX_ENTRIES}"
        )
        .into());
    }
    for (path, bytes) in files {
        if !accept(path, bytes)? {
            continue;
        }
        let text = std::str::from_utf8(bytes)?;
        let base = path.rsplit_once('/').map_or("", |(folder, _)| folder);
        for target in targets(text) {
            let Some(target_path) = local(target) else {
                continue;
            };
            let found = resolve(base, target_path).is_some_and(|resolved| {
                files.contains_key(&resolved) || folders.contains(&resolved)
            });
            if !found {
                return Err(
                    format!("{path} links to {target}, which the plugin does not ship").into(),
                );
            }
        }
    }
    Ok(entries)
}

/// The files under each `(source, destination)` path at HEAD, as stored in
/// Git, at the paths they ship to. Anything other than a regular,
/// non-executable file is refused, as is a missing source.
pub(crate) fn committed(root: &Path, sources: &[(&str, &str)]) -> Result<Files> {
    let mut args = vec!["ls-tree", "-r", "-z", "--full-tree", "HEAD", "--"];
    args.extend(sources.iter().map(|(source, _)| *source));
    let listing = crate::git(root, &args)?;
    let mut entries = Vec::new();
    for record in listing.split('\0').filter(|record| !record.is_empty()) {
        let (meta, path) = record
            .split_once('\t')
            .ok_or("unexpected git ls-tree output")?;
        let fields: Vec<&str> = meta.split(' ').collect();
        let [mode, _, oid] = fields[..] else {
            return Err("unexpected git ls-tree output".into());
        };
        if mode != "100644" {
            return Err(
                format!("{path} must be a regular, non-executable file, not mode {mode}").into(),
            );
        }
        let shipped = sources
            .iter()
            .find_map(|(source, destination)| {
                if path == *source {
                    Some((*destination).to_owned())
                } else {
                    path.strip_prefix(&format!("{source}/"))
                        .map(|rest| format!("{destination}/{rest}"))
                }
            })
            .ok_or_else(|| format!("git ls-tree listed {path}, which the build does not ship"))?;
        entries.push((shipped, oid.to_owned()));
    }
    for &(source, destination) in sources {
        let prefix = format!("{destination}/");
        if !entries
            .iter()
            .any(|(path, _)| path == destination || path.starts_with(&prefix))
        {
            return Err(format!("{source} is not committed at HEAD").into());
        }
    }
    let oids: Vec<String> = entries.iter().map(|(_, oid)| oid.clone()).collect();
    let blobs = blobs(root, &oids)?;
    Ok(entries
        .into_iter()
        .map(|(path, _)| path)
        .zip(blobs)
        .collect())
}

/// Read `oids` through one `git cat-file --batch`, in order.
fn blobs(root: &Path, oids: &[String]) -> Result<Vec<Vec<u8>>> {
    let mut child = Command::new("git")
        .args(["cat-file", "--batch"])
        .current_dir(root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .map_err(|error| format!("cannot run git: {error}"))?;
    let mut stdin = child.stdin.take().ok_or("git cat-file has no stdin")?;
    let request: String = oids.iter().map(|oid| format!("{oid}\n")).collect();
    // Written from a thread, so a full output pipe cannot stall the request.
    let writer = std::thread::spawn(move || stdin.write_all(request.as_bytes()));
    let mut output = BufReader::new(child.stdout.take().ok_or("git cat-file has no stdout")?);
    let mut blobs = Vec::with_capacity(oids.len());
    for oid in oids {
        let mut header = String::new();
        output.read_line(&mut header)?;
        let size = header
            .trim_end()
            .strip_prefix(&format!("{oid} blob "))
            .and_then(|size| size.parse::<usize>().ok())
            .ok_or_else(|| format!("git cat-file gave {header:?} for {oid}"))?;
        // Each object is followed by a newline.
        let mut blob = vec![0; size + 1];
        output.read_exact(&mut blob)?;
        blob.pop();
        blobs.push(blob);
    }
    writer.join().map_err(|_| "git cat-file request failed")??;
    if !child.wait()?.success() {
        return Err("git cat-file failed".into());
    }
    Ok(blobs)
}

/// Write the plugin at HEAD of `root` into the new folder `destination` and
/// return its counts of files and of files and folders.
pub fn build(root: &Path, destination: &Path) -> Result<(usize, usize)> {
    let mut files = committed(root, &SOURCES)?;
    let generated = manifest(&files[MANIFEST])?;
    files.insert(MANIFEST.to_owned(), generated);
    let entries = check(&files)?;
    fs::create_dir_all(destination.parent().ok_or("destination has no parent")?)?;
    fs::create_dir(destination)?;
    for (path, bytes) in &files {
        let target = destination.join(path);
        fs::create_dir_all(target.parent().ok_or("file has no parent")?)?;
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&target)?
            .write_all(bytes)?;
    }
    Ok((files.len(), entries))
}

pub fn cli(mut args: impl Iterator<Item = OsString>) -> Result<u8> {
    let usage = "usage: accounting-skills build-plugin-dist DESTINATION [--root PATH]";
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
    let (count, entries) = build(&root, &destination)?;
    io::stdout().write_all(
        platform_text(&format!(
            "built {count} files ({entries} files and folders) in {}\n",
            destination.display()
        ))
        .as_bytes(),
    )?;
    Ok(0)
}
