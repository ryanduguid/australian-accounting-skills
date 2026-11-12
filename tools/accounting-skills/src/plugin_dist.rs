// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! Build the plugin as the Claude plugin directory reads it: the files the
//! plugin loads, taken from the checked-out commit at the paths its manifest
//! names, and a README whose links still resolve. The directory reads every
//! file under the plugin folder and holds a version for review when it cannot
//! inspect one, so tests, tooling and fixtures stay behind.
use crate::{Result, platform_text};
use serde_json::Value;
use std::{
    collections::{BTreeMap, BTreeSet},
    ffi::OsString,
    fs,
    io::{self, BufRead, BufReader, Read, Write},
    path::{Path, PathBuf},
    process::{Command, Stdio},
};

/// What the plugin loads or must carry, besides the README it is listed with.
pub const SHIPPED: [&str; 8] = [
    ".claude-plugin/plugin.json",
    ".claude-plugin/icon.png",
    ".claude/skills",
    ".claude/rules",
    "DISCLAIMER.md",
    "LICENSE",
    "NOTICE",
    "PRIVACY.md",
];
const README: &str = "README.md";
const MANIFEST: &str = ".claude-plugin/plugin.json";
/// The branch a README link points to once its target is not shipped.
const SOURCE_BRANCH: &str = "main";
/// The directory holds a version with more files and folders than this.
pub const MAX_ENTRIES: usize = 512;
/// The directory holds a version with a file larger than this, images and fonts aside.
pub const MAX_TEXT_BYTES: usize = 256 * 1024;
/// The binary files the directory inspects. Every other file must be UTF-8 text.
const IMAGES: [&str; 5] = ["png", "jpg", "jpeg", "gif", "webp"];
/// SVG is text the directory reads, but a README shows it as an image.
const README_IMAGES: [&str; 6] = ["png", "jpg", "jpeg", "gif", "webp", "svg"];

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

/// The byte ranges of the Markdown link and image targets and the HTML `src`
/// and `srcset` values in `text`, outside fenced code blocks.
fn targets(text: &str) -> Vec<(usize, usize)> {
    let mut found = Vec::new();
    let (mut offset, mut fenced) = (0, false);
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
                    found.push((offset + start, offset + end));
                    from = end;
                }
            }
        }
        offset += line.len();
    }
    found.sort_unstable();
    found
}

/// The path part of a target that names a file in this repository, or `None`
/// for a URL, an anchor or an empty target.
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

/// The README with each relative target the plugin does not ship rewritten to
/// its absolute URL on the source branch of `repository`, so the listing's
/// links and images resolve. A shipped target, an anchor or a URL is kept.
pub fn readme(text: &str, repository: &str, shipped: &BTreeSet<String>) -> Result<String> {
    let project = repository
        .strip_prefix("https://github.com/")
        .filter(|project| project.split('/').count() == 2)
        .ok_or("plugin.json repository must be https://github.com/<owner>/<name>")?;
    let mut out = String::with_capacity(text.len());
    let mut copied = 0;
    for (start, end) in targets(text) {
        let target = &text[start..end];
        let Some(path) = local(target) else {
            continue;
        };
        let path = resolve("", path).ok_or_else(|| format!("README link {target} leaves the repository"))?;
        if shipped.contains(&path) {
            continue;
        }
        let fragment = &target[target.find('#').unwrap_or(target.len())..];
        out.push_str(&text[copied..start]);
        if README_IMAGES.contains(&extension(&path).as_str()) {
            out.push_str(&format!(
                "https://raw.githubusercontent.com/{project}/{SOURCE_BRANCH}/{path}{fragment}"
            ));
        } else {
            out.push_str(&format!(
                "https://github.com/{project}/blob/{SOURCE_BRANCH}/{path}{fragment}"
            ));
        }
        copied = end;
    }
    out.push_str(&text[copied..]);
    Ok(out)
}

/// Refuse a plugin the directory would hold for files it cannot inspect, or
/// one whose Markdown links leave it, and return its count of files and folders.
pub fn check(files: &Files) -> Result<usize> {
    let folders = folders(files);
    let entries = files.len() + folders.len();
    if entries > MAX_ENTRIES {
        return Err(format!(
            "the plugin has {entries} files and folders; the directory reads {MAX_ENTRIES}"
        )
        .into());
    }
    for (path, bytes) in files {
        if IMAGES.contains(&extension(path).as_str()) {
            continue;
        }
        if bytes.len() > MAX_TEXT_BYTES {
            return Err(format!(
                "{path} has {} bytes; the directory inspects up to {MAX_TEXT_BYTES}",
                bytes.len()
            )
            .into());
        }
        let text = std::str::from_utf8(bytes)
            .map_err(|_| format!("{path} is neither UTF-8 text nor an image the directory inspects"))?;
        if extension(path) != "md" {
            continue;
        }
        let base = path.rsplit_once('/').map_or("", |(folder, _)| folder);
        for (start, end) in targets(text) {
            let target = &text[start..end];
            let Some(target_path) = local(target) else {
                continue;
            };
            let found = resolve(base, target_path)
                .is_some_and(|resolved| files.contains_key(&resolved) || folders.contains(&resolved));
            if !found {
                return Err(format!("{path} links to {target}, which the plugin does not ship").into());
            }
        }
    }
    Ok(entries)
}

/// The shipped files and the README at HEAD, as stored in Git. Anything other
/// than a regular, non-executable file is refused, as is a missing path.
fn committed(root: &Path) -> Result<Files> {
    let mut args = vec!["ls-tree", "-r", "-z", "--full-tree", "HEAD", "--"];
    args.extend(SHIPPED);
    args.push(README);
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
            return Err(format!("{path} must be a regular, non-executable file, not mode {mode}").into());
        }
        entries.push((path.to_owned(), oid.to_owned()));
    }
    for required in SHIPPED.iter().chain([&README]) {
        let prefix = format!("{required}/");
        if !entries
            .iter()
            .any(|(path, _)| path == required || path.starts_with(&prefix))
        {
            return Err(format!("{required} is not committed at HEAD").into());
        }
    }
    let oids: Vec<String> = entries.iter().map(|(_, oid)| oid.clone()).collect();
    let blobs = blobs(root, &oids)?;
    Ok(entries.into_iter().map(|(path, _)| path).zip(blobs).collect())
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
    let mut files = committed(root)?;
    let manifest: Value = serde_json::from_slice(&files[MANIFEST])?;
    let repository = manifest["repository"]
        .as_str()
        .ok_or("plugin.json has no repository")?;
    let mut shipped: BTreeSet<String> = files.keys().cloned().collect();
    shipped.extend(folders(&files));
    let text = std::str::from_utf8(&files[README])?;
    let rewritten = readme(text, repository, &shipped)?;
    files.insert(README.to_owned(), rewritten.into_bytes());
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
            Some("--root") => match args.next().filter(|value| !value.as_encoded_bytes().starts_with(b"-")) {
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
