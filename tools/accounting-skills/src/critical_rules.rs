// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Claude Code plugin hook: attach matching skills' anchored critical rules.
//!
//! `prompt` mode (`UserPromptSubmit`) matches the prompt against each skill's
//! name and `hooks/skill-keywords.json` phrases. `compact` mode
//! (`SessionStart` after compaction) matches skill names in the last 1 MiB of
//! the session transcript. Both fail open with empty stdout and exit 0.

use crate::{Result, platform_text, splitlines, validation::is_reparse_point};
use fancy_regex::Regex;
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

static ITEM_START: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^(?:[\s\x1c-\x1f]*(?:[-*+]|\d+[a-z]?[.)])[\s\x1c-\x1f]|#)").unwrap()
});
static MARKER: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^[\s\x1c-\x1f]*(?:[-*+]|\d+[a-z]?[.)])[\s\x1c-\x1f]+").unwrap());
static WORD_OR_HYPHEN: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"^[\p{L}\p{N}_-]$").unwrap());

enum ParsedArgs {
    Run { root: PathBuf, mode: String },
    NoOp,
}

fn py_strip(text: &str) -> &str {
    text.trim_matches(|ch: char| ch.is_whitespace() || matches!(ch, '\u{1c}'..='\u{1f}'))
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

fn plural_suffix_len(rest: &str) -> usize {
    let mut chars = rest.chars();
    match (chars.next(), chars.next()) {
        (Some('e' | 'E'), Some(s @ ('s' | 'S' | '\u{017f}'))) => 1 + s.len_utf8(),
        (Some(s @ ('s' | 'S' | '\u{017f}')), _) => s.len_utf8(),
        _ => 0,
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
            *pos = if end == start && start == haystack.len() {
                haystack.len() + 1
            } else {
                end.max(start + usize::from(end == start))
            };
            return Ok(Some(start));
        }
        *pos = start + step;
    }
}

fn skill_names(skills_dir: &Path) -> Result<Vec<String>> {
    match fs::symlink_metadata(skills_dir) {
        Ok(meta) if meta.is_dir() && !is_reparse_point(skills_dir)? => {}
        Ok(_) => return Ok(Vec::new()),
        Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(Vec::new()),
        Err(error) => return Err(error.into()),
    }
    let mut names = Vec::new();
    for entry in fs::read_dir(skills_dir)? {
        let path = entry?.path();
        if is_reparse_point(&path)? || !path.is_dir() {
            continue;
        }
        let skill_md = path.join("SKILL.md");
        if fs::symlink_metadata(&skill_md).is_ok_and(|meta| meta.is_file()) {
            let name = path
                .file_name()
                .and_then(|name| name.to_str())
                .ok_or("skill folder name is not UTF-8")?
                .to_owned();
            names.push(name);
        }
    }
    names.sort();
    Ok(names)
}

fn rules(skills_dir: &Path, skill: &str) -> Result<Vec<String>> {
    let path = skills_dir.join(skill).join("SKILL.md");
    if !fs::symlink_metadata(&path).is_ok_and(|meta| meta.is_file()) {
        return Err("SKILL.md must be a regular file".into());
    }
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

fn load_keywords(path: &Path) -> Result<BTreeMap<String, Vec<String>>> {
    if !fs::symlink_metadata(path).is_ok_and(|meta| meta.is_file()) {
        return Err("skill-keywords.json must be a regular file".into());
    }
    let text = fs::read_to_string(path)?;
    let Value::Object(object) = serde_json::from_str::<Value>(&text)? else {
        return Err("skill-keywords.json must be a JSON object".into());
    };
    let mut map = BTreeMap::new();
    for (skill, value) in object {
        let Value::Array(items) = value else {
            return Err("skill keywords must be an array".into());
        };
        let mut phrases = Vec::with_capacity(items.len());
        for item in items {
            let Value::String(phrase) = item else {
                return Err("keyword must be a string".into());
            };
            phrases.push(phrase);
        }
        map.insert(skill, phrases);
    }
    Ok(map)
}

fn prompt_matches(root: &Path, skills_dir: &Path, prompt: &str) -> Result<Vec<String>> {
    let keywords = load_keywords(&root.join("hooks").join("skill-keywords.json"))?;
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
    let skills_dir = root.join(".claude").join("skills");
    let (event, reason, matched) = match mode {
        "prompt" => {
            let Some(prompt) = payload.get("prompt").and_then(Value::as_str) else {
                return Ok(String::new());
            };
            let skills = prompt_matches(root, &skills_dir, prompt)?;
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

fn default_root() -> Result<PathBuf> {
    if let Some(root) = std::env::var_os("CLAUDE_PLUGIN_ROOT")
        && !root.is_empty()
    {
        return Ok(PathBuf::from(root));
    }
    Ok(std::env::current_dir()?)
}

fn parse_args(mut args: impl Iterator<Item = OsString>) -> Result<ParsedArgs> {
    let mut root: Option<PathBuf> = None;
    let mut positionals = Vec::new();
    while let Some(arg) = args.next() {
        if arg == "--root" {
            let Some(value) = args.next() else {
                return Ok(ParsedArgs::NoOp);
            };
            root = Some(PathBuf::from(value));
        } else if let Some(value) = arg.to_str().and_then(|text| text.strip_prefix("--root=")) {
            root = Some(PathBuf::from(value));
        } else {
            positionals.push(arg);
        }
    }
    if positionals.len() != 1 {
        return Ok(ParsedArgs::NoOp);
    }
    let Some(mode) = positionals[0].to_str() else {
        return Ok(ParsedArgs::NoOp);
    };
    let root = match root {
        Some(path) => path,
        None => default_root()?,
    };
    Ok(ParsedArgs::Run {
        root,
        mode: mode.to_owned(),
    })
}

pub fn cli(args: impl Iterator<Item = OsString>) -> Result<u8> {
    let Ok(ParsedArgs::Run { root, mode }) = parse_args(args) else {
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
mod tests {
    use super::{
        MAX_CHARS, TRANSCRIPT_TAIL, context, format_hook_output, prompt_matches, rules, run_mode,
        transcript_matches,
    };
    use serde_json::{Map, Value, json};
    use std::fs;
    use tempfile::TempDir;

    fn fixture_root(skills: &[(&str, &str)], keywords: Value) -> TempDir {
        let root = tempfile::tempdir().unwrap();
        let hooks = root.path().join("hooks");
        fs::create_dir_all(&hooks).unwrap();
        fs::write(hooks.join("skill-keywords.json"), keywords.to_string()).unwrap();
        for (name, body) in skills {
            let dir = root.path().join(".claude/skills").join(name);
            fs::create_dir_all(&dir).unwrap();
            fs::write(dir.join("SKILL.md"), body).unwrap();
        }
        root
    }

    #[test]
    fn extracts_anchored_rules_with_continuations_and_multi_anchors() {
        let body = "\
# Demo\r\n\
- Do not lodge. <!-- rule: no-lodgement -->\r\n\
  Prepare only.\r\n\
  - Nested stop.\r\n\
1a) Never guess rates. <!-- rule: evidence-boundary --> <!-- rule: untrusted-instructions -->\r\n\
  Verify primary text.\r\n\
# Heading stops continuation\r\n\
Plain line <!-- rule: bad name -->\r\n";
        let root = fixture_root(&[("demo-skill", body)], json!({}));
        let extracted = rules(&root.path().join(".claude/skills"), "demo-skill").unwrap();
        assert_eq!(
            extracted,
            [
                "Do not lodge. Prepare only.",
                "Never guess rates. Verify primary text.",
            ]
        );
    }

    #[test]
    fn matches_whole_words_plurals_and_unicode_case_folding() {
        let root = fixture_root(
            &[
                ("au-psi-review", "Rule <!-- rule: no-lodgement -->\n"),
                ("bas-preparation", "Rule <!-- rule: no-lodgement -->\n"),
                ("fbt-annual-workflow", "Rule <!-- rule: no-lodgement -->\n"),
            ],
            json!({
                "au-psi-review": ["psi"],
                "bas-preparation": ["bas"],
                "fbt-annual-workflow": ["tax", "fbt"],
            }),
        );
        let skills_dir = root.path().join(".claude/skills");
        assert_eq!(
            prompt_matches(
                root.path(),
                &skills_dir,
                "Check PS\u{0130} and taxes; not basil, fbt-like, fbt2."
            )
            .unwrap(),
            ["au-psi-review", "fbt-annual-workflow"]
        );
        assert_eq!(
            prompt_matches(root.path(), &skills_dir, "Review taxe\u{017f} then BASes.").unwrap(),
            ["fbt-annual-workflow", "bas-preparation"]
        );
    }

    #[test]
    fn orders_prompt_earliest_and_compact_most_recent_within_tail() {
        let root = fixture_root(
            &[
                ("alpha-skill", "A <!-- rule: no-lodgement -->\n"),
                ("beta-skill", "B <!-- rule: no-lodgement -->\n"),
            ],
            json!({"alpha-skill": ["alpha"], "beta-skill": ["beta"]}),
        );
        let skills_dir = root.path().join(".claude/skills");
        let transcript = root.path().join("session.jsonl");
        let padding = "x".repeat(TRANSCRIPT_TAIL as usize + 32);
        let text = format!("alpha-skill {padding} alpha-skill then beta-skill");
        fs::write(&transcript, text).unwrap();
        let compact = transcript_matches(&skills_dir, transcript.to_str().unwrap()).unwrap();
        assert_eq!(compact, ["beta-skill", "alpha-skill"]);

        let pushed_out = root.path().join("old.jsonl");
        fs::write(&pushed_out, format!("alpha-skill {padding}")).unwrap();
        assert!(
            transcript_matches(&skills_dir, pushed_out.to_str().unwrap())
                .unwrap()
                .is_empty()
        );
    }

    #[test]
    fn enforces_max_skills_and_max_chars_in_unicode_scalars() {
        let long_rule = "é".repeat(2990);
        let body = format!("- {long_rule} <!-- rule: no-lodgement -->\n");
        let root = fixture_root(
            &[
                ("skill-a", &body),
                ("skill-b", &body),
                ("skill-c", "Short <!-- rule: no-lodgement -->\n"),
                ("skill-d", "Short <!-- rule: no-lodgement -->\n"),
            ],
            json!({}),
        );
        let skills_dir = root.path().join(".claude/skills");
        let chosen = vec![
            "skill-a".to_owned(),
            "skill-b".to_owned(),
            "skill-c".to_owned(),
            "skill-d".to_owned(),
        ];
        let text = context(&skills_dir, &chosen, "the prompt mentions it").unwrap();
        assert!(text.chars().count() <= MAX_CHARS);
        assert!(text.contains("skill-a"));
        assert!(!text.contains("skill-b"));
        assert!(!text.contains("skill-d"));
    }

    #[test]
    fn formats_ascii_escaped_json_and_ignores_invalid_payloads() {
        let json_line = format_hook_output("UserPromptSubmit", "aé—\u{7f}\u{1f600}").unwrap();
        assert_eq!(
            json_line,
            r#"{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "a\u00e9\u2014\u007f\ud83d\ude00"}}"#
        );
        let root = fixture_root(
            &[("bas-preparation", "R <!-- rule: no-lodgement -->\n")],
            json!({}),
        );
        let non_str = serde_json::from_value::<Map<String, Value>>(json!({"prompt": 7})).unwrap();
        assert_eq!(run_mode(root.path(), "prompt", &non_str).unwrap(), "");
        let non_compact = serde_json::from_value::<Map<String, Value>>(
            json!({"source": "startup", "transcript_path": "missing"}),
        )
        .unwrap();
        assert_eq!(run_mode(root.path(), "compact", &non_compact).unwrap(), "");
    }
}
