// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Claude Code plugin hook: attach matching skills' anchored critical rules.
//!
//! `prompt` mode (`UserPromptSubmit`) matches the prompt against each skill's
//! name and `hooks/skill-keywords.json` phrases. `compact` mode
//! (`SessionStart` after compaction) matches skill names in the last 1 MiB of
//! the session transcript. Both fail open with empty stdout and exit 0.
//!
//! The plugin root comes only from `--root` or `CLAUDE_PLUGIN_ROOT`, never
//! the working directory, so a project the user opens cannot supply rules
//! under the plugin's name. Every file is read through its canonical path,
//! inside the root and with no link on the way.

use crate::{Result, platform_text, splitlines};
use fancy_regex::Regex;
use serde::Deserialize;
use serde_json::{Map, Value};
use std::{
    borrow::Cow,
    cmp::Reverse,
    collections::BTreeMap,
    ffi::OsString,
    fs::{self, File},
    io::{self, Read, Seek, SeekFrom, Write},
    path::{Path, PathBuf},
    sync::LazyLock,
};

const PLUGIN: &str = "australian-accounting-skills";
const MAX_SKILLS: usize = 3;
const MAX_CHARS: usize = 6000;
// Antifragile tail bound: read only the last 1 MiB rather than absorbing a multi-GB transcript.
const TRANSCRIPT_TAIL: u64 = 1024 * 1024;
/// The largest `skill-keywords.json` parsed; the file is about 8 KiB.
const MAX_KEYWORDS_BYTES: u64 = 1024 * 1024;
const PLURAL_S: [&str; 3] = ["s", "S", "\u{17f}"];

static ITEM_START: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^(?:[\s\x1c-\x1f]*(?:[-*+]|\d+[a-z]?[.)])[\s\x1c-\x1f]|#)").unwrap()
});
static MARKER: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^[\s\x1c-\x1f]*(?:[-*+]|\d+[a-z]?[.)])[\s\x1c-\x1f]+").unwrap());
static WORD_OR_HYPHEN: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"^[\p{L}\p{N}_-]$").unwrap());

fn py_strip(text: &str) -> &str {
    text.trim_matches(crate::source_content::space)
}

fn strip_rule_anchor(line: &str) -> Option<&str> {
    let body = line.strip_suffix(" -->")?;
    let (prefix, name) = body.rsplit_once(" <!-- rule: ")?;
    (!name.is_empty()
        && name
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte == b'-'))
    .then_some(prefix)
}

fn is_word_or_hyphen(ch: char) -> bool {
    if ch.is_ascii() {
        ch.is_ascii_alphanumeric() || ch == '_' || ch == '-'
    } else {
        let mut buf = [0u8; 4];
        WORD_OR_HYPHEN
            .is_match(ch.encode_utf8(&mut buf))
            .unwrap_or(false)
    }
}

fn fold_turkish_i(text: &str) -> Cow<'_, str> {
    if text.contains(['\u{130}', '\u{131}']) {
        Cow::Owned(text.replace(['\u{130}', '\u{131}'], "i"))
    } else {
        Cow::Borrowed(text)
    }
}

/// The length of a leading `s` (`S` or long `ſ`, as Python's `re.I` matches).
fn s_len(text: &str) -> usize {
    PLURAL_S
        .iter()
        .find(|s| text.starts_with(**s))
        .map_or(0, |s| s.len())
}

/// The length of the optional `(?:e?s)` plural ending at the start of `rest`.
fn plural_suffix_len(rest: &str) -> usize {
    match rest.strip_prefix(['e', 'E']).map(s_len) {
        Some(len) if len > 0 => 1 + len,
        _ => s_len(rest),
    }
}

fn compile_phrase(phrase: &str) -> Result<Regex> {
    let folded = fold_turkish_i(phrase);
    let escaped = fancy_regex::escape(folded.as_ref());
    Ok(Regex::new(&format!("(?i){escaped}"))?)
}

fn next_match(
    re: &Regex,
    haystack: &str,
    pos: &mut usize,
    empty_phrase: bool,
) -> Result<Option<usize>> {
    loop {
        if *pos > haystack.len() || (*pos == haystack.len() && !empty_phrase) {
            return Ok(None);
        }
        let Some(found) = re.find(&haystack[*pos..])? else {
            return Ok(None);
        };
        let start = *pos + found.start();
        let mid = *pos + found.end();
        let end = mid + plural_suffix_len(&haystack[mid..]);
        let prev_ok = !haystack[..start]
            .chars()
            .next_back()
            .is_some_and(is_word_or_hyphen);
        let next_ok = !haystack[end..]
            .chars()
            .next()
            .is_some_and(is_word_or_hyphen);
        let step = haystack[start..].chars().next().map_or(1, char::len_utf8);
        if prev_ok && next_ok {
            *pos = if end == start { start + step } else { end };
            return Ok(Some(start));
        }
        *pos = start + step;
    }
}

/// The canonical path of `dir/name`, or `None` when it is missing, a link or
/// a junction, or resolves outside `dir`. `dir` must be canonical.
fn entry_in(dir: &Path, name: impl AsRef<Path>) -> Option<PathBuf> {
    let spelled = dir.join(name);
    let target = fs::canonicalize(&spelled).ok()?;
    if !target.starts_with(dir) {
        return None;
    }
    (target == spelled).then_some(target)
}

/// The regular file `dir/folder/file`, with no link on the way.
fn file_in(dir: &Path, folder: impl AsRef<Path>, file: &str) -> Option<PathBuf> {
    entry_in(dir, folder)
        .and_then(|folder| entry_in(&folder, file))
        .filter(|path| path.is_file())
}

/// The plugin's `.claude/skills` folder under the canonical `root`.
fn skills_dir(root: &Path) -> Option<PathBuf> {
    entry_in(root, ".claude")
        .and_then(|claude| entry_in(&claude, "skills"))
        .filter(|skills| skills.is_dir())
}

fn skill_names(skills_dir: &Path) -> Result<Vec<String>> {
    let mut names = Vec::new();
    for entry in fs::read_dir(skills_dir)? {
        let name = entry?.file_name();
        if file_in(skills_dir, &name, "SKILL.md").is_some() {
            let name = name
                .into_string()
                .map_err(|_| "skill folder name is not UTF-8")?;
            names.push(name);
        }
    }
    names.sort();
    Ok(names)
}

fn rules(skills_dir: &Path, skill: &str) -> Result<Vec<String>> {
    let path = file_in(skills_dir, skill, "SKILL.md")
        .ok_or("SKILL.md must be a regular file in the skill's folder")?;
    let text = fs::read_to_string(&path)?;
    let lines = splitlines(&text);
    let mut items = Vec::new();
    for (index, &raw_line) in lines.iter().enumerate() {
        let Some(mut line) = strip_rule_anchor(raw_line) else {
            continue;
        };
        while let Some(stripped) = strip_rule_anchor(line) {
            line = stripped;
        }
        let cleaned = MARKER.replace(line, "");
        let mut item = vec![py_strip(cleaned.as_ref())];
        for &following in &lines[index + 1..] {
            let trimmed = py_strip(following);
            if trimmed.is_empty() || ITEM_START.is_match(following)? {
                break;
            }
            item.push(trimmed);
        }
        items.push(item.join(" "));
    }
    Ok(items)
}

/// `hooks/skill-keywords.json` under the canonical `root`: an object of
/// string arrays, at most `MAX_KEYWORDS_BYTES` long.
fn load_keywords(root: &Path) -> Result<BTreeMap<String, Vec<String>>> {
    let path = file_in(root, "hooks", "skill-keywords.json")
        .ok_or("hooks/skill-keywords.json must be a regular file in the plugin root")?;
    let mut bytes = Vec::new();
    File::open(&path)?
        .take(MAX_KEYWORDS_BYTES + 1)
        .read_to_end(&mut bytes)?;
    if bytes.len() as u64 > MAX_KEYWORDS_BYTES {
        return Err("skill-keywords.json is larger than 1 MiB".into());
    }
    let mut parser = serde_json::Deserializer::from_slice(&bytes);
    let keywords = BTreeMap::<String, Vec<String>>::deserialize(&mut parser)?;
    parser.end()?;
    Ok(keywords)
}

fn prompt_matches(root: &Path, skills_dir: &Path, prompt: &str) -> Result<Vec<String>> {
    let keywords = load_keywords(root)?;
    let folded_prompt = fold_turkish_i(prompt);
    let mut found: Vec<(usize, String)> = Vec::new();
    for skill in skill_names(skills_dir)? {
        let mut earliest: Option<usize> = None;
        let extra = keywords.get(&skill).map_or(&[][..], Vec::as_slice);
        for phrase in std::iter::once(skill.as_str()).chain(extra.iter().map(String::as_str)) {
            let re = compile_phrase(phrase)?;
            let mut pos = 0;
            if let Some(start) =
                next_match(&re, folded_prompt.as_ref(), &mut pos, phrase.is_empty())?
            {
                earliest = Some(earliest.map_or(start, |best| best.min(start)));
            }
        }
        if let Some(pos) = earliest {
            found.push((pos, skill));
        }
    }
    found.sort_by(|(pos_a, name_a), (pos_b, name_b)| {
        pos_a.cmp(pos_b).then_with(|| name_a.cmp(name_b))
    });
    Ok(found.into_iter().map(|(_, skill)| skill).collect())
}

fn read_transcript_tail(path: &Path) -> Result<String> {
    let mut file = File::open(path)?;
    if !file.metadata()?.is_file() {
        return Err("transcript path is not a regular file".into());
    }
    let size = file.seek(SeekFrom::End(0))?;
    file.seek(SeekFrom::Start(size.saturating_sub(TRANSCRIPT_TAIL)))?;
    let mut bytes = Vec::new();
    file.take(TRANSCRIPT_TAIL).read_to_end(&mut bytes)?;
    Ok(String::from_utf8_lossy(&bytes).into_owned())
}

fn transcript_matches(skills_dir: &Path, transcript_path: &str) -> Result<Vec<String>> {
    let tail = read_transcript_tail(Path::new(transcript_path))?;
    let folded_tail = fold_turkish_i(&tail);
    let mut found: Vec<(usize, String)> = Vec::new();
    for skill in skill_names(skills_dir)? {
        let re = compile_phrase(&skill)?;
        let mut pos = 0;
        let mut last = None;
        while let Some(start) = next_match(&re, folded_tail.as_ref(), &mut pos, skill.is_empty())? {
            last = Some(start);
        }
        if let Some(pos) = last {
            found.push((pos, skill));
        }
    }
    found.sort_by(|(pos_a, name_a), (pos_b, name_b)| {
        Reverse(*pos_a)
            .cmp(&Reverse(*pos_b))
            .then_with(|| name_a.cmp(name_b))
    });
    Ok(found.into_iter().map(|(_, skill)| skill).collect())
}

fn context(skills_dir: &Path, skills: &[String], reason: &str) -> Result<String> {
    let mut text = String::new();
    let mut text_chars = 0usize;
    for skill in skills.iter().take(MAX_SKILLS) {
        let mut block = format!("Critical rules of the {PLUGIN} skill {skill} ({reason}):\n");
        for item in rules(skills_dir, skill)? {
            block.push_str("- ");
            block.push_str(&item);
            block.push('\n');
        }
        let block_chars = block.chars().count();
        if text_chars + block_chars > MAX_CHARS {
            break;
        }
        text.push_str(&block);
        text_chars += block_chars;
    }
    Ok(py_strip(&text).to_owned())
}

fn json_escape_ascii(text: &str) -> String {
    use std::fmt::Write;
    let mut out = String::with_capacity(text.len());
    for ch in text.chars() {
        if ch < '\u{7f}' {
            out.push(ch);
        } else {
            for unit in ch.encode_utf16(&mut [0; 2]) {
                let _ = write!(out, "\\u{unit:04x}");
            }
        }
    }
    out
}

fn format_hook_output(event: &str, text: &str) -> Result<String> {
    let raw = format!(
        "{{\"hookSpecificOutput\": {{\"hookEventName\": {}, \"additionalContext\": {}}}}}",
        serde_json::to_string(event)?,
        serde_json::to_string(text)?,
    );
    Ok(json_escape_ascii(&raw))
}

fn run_mode(root: &Path, mode: &str, payload: &Map<String, Value>) -> Result<String> {
    let root = fs::canonicalize(root)?;
    let Some(skills_dir) = skills_dir(&root) else {
        return Ok(String::new());
    };
    let (event, reason, matched) = match mode {
        "prompt" => {
            let Some(prompt) = payload.get("prompt").and_then(Value::as_str) else {
                return Ok(String::new());
            };
            let skills = prompt_matches(&root, &skills_dir, prompt)?;
            ("UserPromptSubmit", "the prompt mentions it", skills)
        }
        "compact" => {
            let is_compact = payload.get("source").and_then(Value::as_str) == Some("compact");
            let Some(transcript) = payload.get("transcript_path").and_then(Value::as_str) else {
                return Ok(String::new());
            };
            if !is_compact {
                return Ok(String::new());
            }
            let skills = transcript_matches(&skills_dir, transcript)?;
            ("SessionStart", "used before compaction", skills)
        }
        _ => return Ok(String::new()),
    };
    let text = context(&skills_dir, &matched, reason)?;
    if text.is_empty() {
        return Ok(String::new());
    }
    format_hook_output(event, &text)
}

/// `input` with each lone surrogate escape (`\ud800` to `\udfff` outside a
/// pair) replaced by `�`. Python's `json.loads` accepts one, and a
/// JavaScript client writes one for a prompt holding half an emoji; serde
/// refuses it. Neither prints the prompt, so the hook's output is unchanged.
fn replace_lone_surrogates(input: &str) -> Cow<'_, str> {
    fn escape_at(bytes: &[u8], at: usize) -> Option<u16> {
        let hex = bytes.get(at..at + 6)?.strip_prefix(b"\\u")?;
        u16::from_str_radix(std::str::from_utf8(hex).ok()?, 16).ok()
    }
    if !input.contains("\\u") {
        return Cow::Borrowed(input);
    }
    let bytes = input.as_bytes();
    let mut out = String::with_capacity(input.len());
    let (mut copied, mut at) = (0, 0);
    while at < bytes.len() {
        if bytes[at] != b'\\' {
            at += 1;
            continue;
        }
        let Some(unit) = escape_at(bytes, at) else {
            at += 2;
            continue;
        };
        let paired = (0xd800..0xdc00).contains(&unit)
            && escape_at(bytes, at + 6).is_some_and(|low| (0xdc00..0xe000).contains(&low));
        if paired {
            at += 12;
        } else if (0xd800..0xe000).contains(&unit) {
            out.push_str(&input[copied..at]);
            out.push_str("\\ufffd");
            at += 6;
            copied = at;
        } else {
            at += 6;
        }
    }
    out.push_str(&input[copied..]);
    Cow::Owned(out)
}

/// The root from `--root PATH`, `--root=PATH` or else `CLAUDE_PLUGIN_ROOT`,
/// and the one mode argument; `None` for anything else.
fn parse_args(mut args: impl Iterator<Item = OsString>) -> Option<(PathBuf, String)> {
    let mut root: Option<PathBuf> = None;
    let mut positionals = Vec::new();
    while let Some(arg) = args.next() {
        if arg == "--root" {
            root = Some(PathBuf::from(args.next()?));
        } else if let Some(value) = arg.to_str().and_then(|text| text.strip_prefix("--root=")) {
            root = Some(PathBuf::from(value));
        } else {
            positionals.push(arg);
        }
    }
    let [mode] = positionals.as_slice() else {
        return None;
    };
    let root = root.or_else(|| {
        std::env::var_os("CLAUDE_PLUGIN_ROOT")
            .filter(|root| !root.is_empty())
            .map(PathBuf::from)
    })?;
    Some((root, mode.to_str()?.to_owned()))
}

pub fn cli(args: impl Iterator<Item = OsString>) -> Result<u8> {
    let Some((root, mode)) = parse_args(args) else {
        return Ok(0);
    };
    if !matches!(mode.as_str(), "prompt" | "compact") {
        return Ok(0);
    }
    let mut raw = Vec::new();
    if io::stdin().lock().read_to_end(&mut raw).is_err() {
        return Ok(0);
    }
    let Ok(input) = String::from_utf8(raw) else {
        return Ok(0);
    };
    let input = replace_lone_surrogates(&input);
    let Ok(Value::Object(payload)) = serde_json::from_str::<Value>(&input) else {
        return Ok(0);
    };
    let Ok(output) = run_mode(&root, &mode, &payload) else {
        return Ok(0);
    };
    if !output.is_empty() {
        let mut stdout = io::stdout().lock();
        stdout.write_all(platform_text(&format!("{output}\n")).as_bytes())?;
        stdout.flush()?;
    }
    Ok(0)
}

#[cfg(test)]
mod tests;
