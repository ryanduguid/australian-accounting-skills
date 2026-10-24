//! Read-only checks for the repository's fabricated regression pack.
use crate::{Result, strict_yaml, validation_text as text};
use fancy_regex::Regex;
use serde::{
    Deserialize, Deserializer,
    de::{self, MapAccess, SeqAccess, Visitor},
};
use serde_json::{Map, Value, json};
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt, fs,
    path::{Path, PathBuf},
    process::Command,
    sync::LazyLock,
};

type Names = BTreeSet<String>;
const SUPPORT: &[&str] = &[
    "CLAUDE.md",
    ".claude/rules/accounting-safety.md",
    "scripts/strict_yaml.py",
    "scripts/validate_validation.py",
    "tests/test_validation_pack.py",
];
const KEYS: &[&str] = &["model", "run_date", "skills_version", "runner", "results"];
const V2_KEYS: &[&str] = &[
    "model",
    "run_date",
    "skills_version",
    "runner",
    "results",
    "schema_version",
    "input_mode",
    "status",
    "provenance",
];
const DIGESTS: &[&str] = &["input_sha256", "context_sha256", "rubric_sha256"];
const STATUSES: &[&str] = &["legacy", "prepared", "observed", "confirmed"];
const SECTIONS: &[&str] = &[
    "## Scenario",
    "## Task",
    "## Synthetic inputs",
    "## Deliberately unavailable evidence",
    "## Required checks",
    "## Must not do",
    "## Source-verification and reviewer boundary",
];
static RESULT_NAME: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^validation/results/(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.json$").unwrap()
});
static SLUG: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^[a-z0-9]+(?:-[a-z0-9]+)*\z").unwrap());

pub fn repr(text: &str) -> String {
    let quote = if text.contains('\'') && !text.contains('"') {
        '"'
    } else {
        '\''
    };
    let value = text
        .replace('\\', "\\\\")
        .replace(quote, &format!("\\{quote}"))
        .replace('\n', "\\n")
        .replace('\r', "\\r")
        .replace('\t', "\\t");
    format!("{quote}{value}{quote}")
}
fn list<'a>(items: impl IntoIterator<Item = &'a String>) -> String {
    format!(
        "[{}]",
        items
            .into_iter()
            .map(|s| repr(s))
            .collect::<Vec<_>>()
            .join(", ")
    )
}
fn names(items: &[&str]) -> Names {
    items.iter().map(|s| (*s).to_owned()).collect()
}
fn keys(value: &Value) -> Names {
    value
        .as_object()
        .map(|m| m.keys().cloned().collect())
        .unwrap_or_default()
}
fn strings(value: &Value) -> Option<Vec<String>> {
    value
        .as_array()?
        .iter()
        .map(|v| v.as_str().map(str::to_owned))
        .collect()
}
fn difference(a: &Names, b: &Names) -> String {
    list(a.difference(b))
}
fn string(value: &Value) -> &str {
    value.as_str().unwrap_or("")
}
fn matches(regex: &Regex, value: &str) -> bool {
    regex.is_match(value).unwrap_or(false)
}
pub use crate::validation_text::{
    normalise as normalise_for_sensitive_scan, read_utf8, sensitive as check_sensitive_content,
};

struct Unique(Value);
impl<'de> Deserialize<'de> for Unique {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> std::result::Result<Self, D::Error> {
        struct V;
        impl<'de> Visitor<'de> for V {
            type Value = Unique;
            fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str("JSON value")
            }
            fn visit_bool<E: de::Error>(self, v: bool) -> std::result::Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_i64<E: de::Error>(self, v: i64) -> std::result::Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_u64<E: de::Error>(self, v: u64) -> std::result::Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_f64<E: de::Error>(self, v: f64) -> std::result::Result<Unique, E> {
                Ok(Unique(json!(v)))
            }
            fn visit_str<E: de::Error>(self, v: &str) -> std::result::Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_string<E: de::Error>(self, v: String) -> std::result::Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_unit<E: de::Error>(self) -> std::result::Result<Unique, E> {
                Ok(Unique(Value::Null))
            }
            fn visit_seq<A: SeqAccess<'de>>(
                self,
                mut seq: A,
            ) -> std::result::Result<Unique, A::Error> {
                let mut values = Vec::new();
                while let Some(Unique(value)) = seq.next_element()? {
                    values.push(value);
                }
                Ok(Unique(values.into()))
            }
            fn visit_map<A: MapAccess<'de>>(
                self,
                mut map: A,
            ) -> std::result::Result<Unique, A::Error> {
                let mut values = Map::new();
                while let Some((key, Unique(value))) = map.next_entry::<String, Unique>()? {
                    if values.insert(key.clone(), value).is_some() {
                        return Err(de::Error::custom(format!(
                            "duplicate JSON key {}",
                            repr(&key)
                        )));
                    }
                }
                Ok(Unique(values.into()))
            }
        }
        deserializer.deserialize_any(V)
    }
}
pub fn strict_json(text: &str, label: &str) -> Result<Value> {
    serde_json::from_str::<Unique>(text)
        .map(|value| value.0)
        .map_err(|e| format!("{label}: not valid JSON ({e})").into())
}

pub fn parse_front_matter(text: &str, card_name: &str) -> Result<(Value, String)> {
    static FRONT: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"(?s)\A---\r?\n(.*?)\r?\n---\r?\n").unwrap());
    let cap = FRONT
        .captures(text)?
        .ok_or("front matter must be the first document block")?;
    let raw = &cap[1];
    let value = strict_yaml::card_mapping(raw).map_err(|e| {
        let message = e.to_string();
        if message.starts_with("front matter")
            || message.starts_with("YAML")
            || message.starts_with("duplicate")
        {
            message
        } else {
            format!("front matter must be valid YAML: {message}")
        }
    })?;
    if !value.is_object() {
        return Err("front matter must be a YAML mapping".into());
    }
    let expected = names(&["id", "synthetic", "target_skills"]);
    let actual = keys(&value);
    if actual != expected {
        return Err(format!(
            "front-matter fields must be exact; missing={}, unknown={}",
            difference(&expected, &actual),
            difference(&actual, &expected)
        )
        .into());
    }
    let id = value["id"]
        .as_str()
        .filter(|id| matches(&SLUG, id))
        .ok_or("id must be a lowercase hyphenated slug")?;
    let stem = Path::new(card_name)
        .file_stem()
        .and_then(|s| s.to_str())
        .ok_or("invalid card filename")?;
    if id != stem {
        return Err(format!("id must match filename stem: {stem}").into());
    }
    if value["synthetic"] != true || !Regex::new(r"(?m)^synthetic: true$")?.is_match(raw)? {
        return Err("synthetic must be the literal boolean true".into());
    }
    let skills = value["target_skills"]
        .as_array()
        .filter(|s| !s.is_empty())
        .ok_or("target_skills must be a non-empty YAML list")?;
    if !skills
        .iter()
        .all(|v| v.as_str().is_some_and(|s| matches(&SLUG, s)))
    {
        return Err("every target skill must be a lowercase hyphenated slug".into());
    }
    if skills.iter().map(string).collect::<BTreeSet<_>>().len() != skills.len() {
        return Err("target_skills contains a duplicate".into());
    }
    Ok((value, text[cap.get(0).unwrap().end()..].to_owned()))
}

pub fn is_reparse_point(path: &Path) -> Result<bool> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|e| format!("cannot inspect {}: {e}", path.display()))?;
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        Ok(metadata.file_attributes() & 0x400 != 0)
    }
    #[cfg(not(windows))]
    {
        Ok(metadata.file_type().is_symlink())
    }
}
pub fn check_expected_path(path: &Path, root: &Path) -> Result<()> {
    let safe = fs::canonicalize(path)
        .and_then(|p| fs::canonicalize(root).map(|r| p.starts_with(r)))
        .unwrap_or(false);
    if !safe {
        return Err(format!("unsafe or missing expected path: {}", path.display()).into());
    }
    let mut current = path;
    while current != root {
        if is_reparse_point(current)? {
            return Err(format!(
                "symlink or reparse point is not permitted: {}",
                current.display()
            )
            .into());
        }
        current = current.parent().ok_or("expected path is not under root")?;
    }
    if !path.is_file() {
        return Err(format!("expected regular file: {}", path.display()).into());
    }
    Ok(())
}
fn relative(path: &Path, root: &Path) -> Result<String> {
    let relative = path
        .strip_prefix(root)?
        .to_str()
        .ok_or("non-Unicode source path")?
        .to_owned();
    #[cfg(windows)]
    let relative = relative.replace('\\', "/");
    Ok(relative)
}
pub fn inventory_validation_tree(root: &Path) -> Result<Names> {
    let base = root.join("validation");
    if is_reparse_point(&base)? || !base.is_dir() {
        return Err("validation must be a real directory".into());
    }
    let mut found = Names::new();
    let mut pending = vec![base];
    while let Some(directory) = pending.pop() {
        for entry in fs::read_dir(&directory)
            .map_err(|e| format!("cannot inspect {}: {e}", directory.display()))?
        {
            let entry = entry?;
            let path = entry.path();
            let rel = relative(&path, root)?;
            if is_reparse_point(&path)? {
                return Err(format!("validation contains a symlink/reparse point: {rel}").into());
            }
            let kind = entry.file_type()?;
            if kind.is_dir() {
                pending.push(path);
            } else if kind.is_file() {
                found.insert(rel);
            } else {
                return Err(format!("validation contains a non-regular entry: {rel}").into());
            }
        }
    }
    Ok(found)
}
pub fn discover_case_names(root: &Path) -> Result<Names> {
    fs::read_dir(root.join("validation/cases"))
        .and_then(|entries| {
            entries
                .map(|entry| entry.map(|e| e.file_name()))
                .collect::<std::io::Result<Vec<_>>>()
        })
        .map_err(|e| format!("cannot inventory validation cases: {e}"))?
        .into_iter()
        .map(|name| {
            name.into_string()
                .map_err(|_| "non-Unicode case name".into())
        })
        .collect()
}
pub fn expected_validation(cases: &Names) -> Names {
    names(&["validation/README.md", "validation/results.schema.json"])
        .into_iter()
        .chain(cases.iter().map(|name| format!("validation/cases/{name}")))
        .collect()
}
pub fn case_ids(cases: &Names) -> Names {
    cases
        .iter()
        .map(|name| name.strip_suffix(".md").unwrap_or(name).to_owned())
        .collect()
}
pub fn split_result_files(input: &Names) -> (Names, Names) {
    input
        .iter()
        .cloned()
        .partition(|name| !matches(&RESULT_NAME, name))
}
pub fn git_entries(paths: &[String], root: &Path) -> Result<BTreeMap<String, String>> {
    let output = Command::new("git")
        .args(["ls-files", "--stage", "-z", "--"])
        .args(paths)
        .current_dir(root)
        .output()
        .map_err(|e| format!("cannot run Git inventory: {e}"))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let detail = if stderr.trim().is_empty() {
            output
                .status
                .code()
                .map(|code| code.to_string())
                .unwrap_or_else(|| output.status.to_string())
        } else {
            stderr.trim().to_owned()
        };
        return Err(format!("Git inventory failed: {detail}").into());
    }
    let mut entries = BTreeMap::new();
    for raw in output.stdout.split(|&b| b == 0).filter(|v| !v.is_empty()) {
        let raw =
            std::str::from_utf8(raw).map_err(|_| "Git returned an undecodable inventory entry")?;
        let (metadata, path) = raw
            .split_once('\t')
            .ok_or("Git returned an undecodable inventory entry")?;
        let mode = metadata
            .split_once(' ')
            .ok_or("Git returned an undecodable inventory entry")?
            .0;
        if !mode.is_ascii() {
            return Err("Git returned an undecodable inventory entry".into());
        }
        if entries.insert(path.to_owned(), mode.to_owned()).is_some() {
            return Err(format!("duplicate Git inventory entry: {path}").into());
        }
    }
    Ok(entries)
}
pub fn check_ignored(path: &str, root: &Path) -> Result<()> {
    let output = Command::new("git")
        .args(["check-ignore", "--no-index", "--quiet", "--", path])
        .current_dir(root)
        .output()?;
    match output.status.code() {
        Some(0) => Err(format!("tracked source is ignored by .gitignore: {path}").into()),
        Some(1) => Ok(()),
        _ => Err(format!(
            "git check-ignore failed for {path}: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        )
        .into()),
    }
}

pub fn check_results_schema(input: &str, known: &Names) -> Result<()> {
    let schema = strict_json(input, "validation/results.schema.json")?;
    let enums = strings(&schema["properties"]["results"]["propertyNames"]["enum"]);
    let verdicts = strings(&schema["properties"]["results"]["additionalProperties"]["enum"]);
    let (Some(enums), Some(verdicts)) = (enums, verdicts) else {
        return Err("results schema does not declare the case and verdict enums".into());
    };
    let declared: Names = enums.iter().cloned().collect();
    if declared != *known || enums.len() != known.len() {
        return Err(format!(
            "results schema case enum does not match the card inventory: missing={}, unknown={}",
            difference(known, &declared),
            difference(&declared, known)
        )
        .into());
    }
    let mut sorted = verdicts.clone();
    sorted.sort();
    if sorted != ["fail", "pass"] {
        return Err(format!(
            "results schema verdict enum must be exactly pass, fail, got {}",
            list(&verdicts)
        )
        .into());
    }
    let bad = || -> Box<dyn std::error::Error> {
        "results schema version 2 provenance contract has changed".into()
    };
    if keys(&schema["properties"]) != names(V2_KEYS)
        || schema["properties"]["schema_version"] != json!({"const":2,"type":"integer"})
        || schema["properties"]["status"]["enum"] != json!(["prepared", "observed", "confirmed"])
        || schema["properties"]["input_mode"]["enum"] != json!(["task-only", "whole-card"])
        || schema["additionalProperties"] != false
        || schema["required"] != json!(KEYS)
        || schema["properties"]["provenance"]["minProperties"] != 1
        || schema["properties"]["provenance"]["propertyNames"]
            != json!({"$ref":"#/properties/results/propertyNames"})
    {
        return Err(bad());
    }
    let evidence = &schema["properties"]["provenance"]["additionalProperties"];
    let digest_keys: Names = DIGESTS
        .iter()
        .chain([&"output_sha256"])
        .map(|s| (*s).to_owned())
        .collect();
    if evidence["additionalProperties"] != false
        || evidence["required"] != json!(DIGESTS)
        || keys(&evidence["properties"]) != digest_keys
    {
        return Err(bad());
    }
    for key in &digest_keys {
        if evidence["properties"][key]
            != json!({"type":"string","pattern":"^[0-9a-f]{64}$","minLength":64,"maxLength":64})
        {
            return Err(bad());
        }
    }
    let rules = schema["allOf"]
        .as_array()
        .filter(|a| a.len() == 1)
        .ok_or_else(bad)?;
    let rule = &rules[0];
    if rule["if"] != json!({"required":["schema_version"]})
        || rule["then"]["required"] != json!(["input_mode", "status", "provenance"])
        || rule["then"]["allOf"]
            != json!([
                {"if":{"properties":{"status":{"const":"confirmed"}}},"then":{"properties":{"results":{"minProperties":1}}},"else":{"properties":{"results":{"maxProperties":0}}}},
                {"if":{"properties":{"status":{"const":"prepared"}}},"then":{"properties":{"provenance":{"additionalProperties":{"not":{"required":["output_sha256"]}}}}},"else":{"properties":{"provenance":{"additionalProperties":{"required":["output_sha256"]}}}}}
            ])
        || rule["else"]
            != json!({"not":{"anyOf":[{"required":["input_mode"]},{"required":["status"]},{"required":["provenance"]}]},"properties":{"results":{"minProperties":1}}})
    {
        return Err(bad());
    }
    Ok(())
}

fn valid_date(year: i32, month: i32, day: i32) -> bool {
    let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    let days = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if leap {
                29
            } else {
                28
            }
        }
        _ => 0,
    };
    (1..=9999).contains(&year) && day > 0 && day <= days
}
fn canonical_date(input: &str) -> Option<String> {
    let compact = input.replace('-', "");
    if compact.len() == 8 && compact.bytes().all(|b| b.is_ascii_digit()) {
        let (y, m, d) = (
            compact[..4].parse().ok()?,
            compact[4..6].parse().ok()?,
            compact[6..].parse().ok()?,
        );
        if input.len() != 8
            && (input.len() != 10 || input.as_bytes()[4] != b'-' || input.as_bytes()[7] != b'-')
        {
            return None;
        }
        return valid_date(y, m, d).then(|| format!("{y:04}-{m:02}-{d:02}"));
    }
    // Python date.fromisoformat also accepts ISO week dates, including Monday defaults.
    let (year, rest) = compact.split_once('W')?;
    if year.len() != 4
        || !(rest.len() == 2 || rest.len() == 3)
        || !year.bytes().chain(rest.bytes()).all(|b| b.is_ascii_digit())
    {
        return None;
    }
    let compact_form = format!("{year}W{rest}");
    let extended_form = if rest.len() == 3 {
        format!("{year}-W{}-{}", &rest[..2], &rest[2..])
    } else {
        format!("{year}-W{rest}")
    };
    if input != compact_form && input != extended_form {
        return None;
    }
    let year: i32 = year.parse().ok()?;
    let week: i32 = rest[..2].parse().ok()?;
    let day: i32 = if rest.len() == 2 {
        1
    } else {
        rest[2..].parse().ok()?
    };
    if !(1..=9999).contains(&year) || !(1..=7).contains(&day) {
        return None;
    }
    let jan4 = |y: i32| {
        let prior = y - 1;
        prior * 365 + prior / 4 - prior / 100 + prior / 400 + 4
    };
    let monday = |y| {
        let n = jan4(y);
        n - (n - 1) % 7
    };
    if week < 1 || week > (monday(year + 1) - monday(year)) / 7 {
        return None;
    }
    let ordinal = monday(year) + (week - 1) * 7 + day - 1;
    let mut y = year;
    while ordinal < jan4(y) - 3 {
        y -= 1;
    }
    while ordinal >= jan4(y + 1) - 3 {
        y += 1;
    }
    let mut day = ordinal - (jan4(y) - 3) + 1;
    let mut month = 1;
    while !valid_date(y, month, day) && month <= 12 {
        let mut days = 31;
        while !valid_date(y, month, days) && days > 0 {
            days -= 1;
        }
        day -= days;
        month += 1;
    }
    valid_date(y, month, day).then(|| format!("{y:04}-{month:02}-{day:02}"))
}

pub fn check_result_file(rel: &str, input: &str, known: &Names) -> Result<String> {
    let cap = RESULT_NAME
        .captures(rel)?
        .ok_or("result file name must be YYYY-MM-DD-<slug>.json")?;
    let data = strict_json(input, rel)?;
    let v2 = data
        .as_object()
        .is_some_and(|m| m.contains_key("schema_version"));
    let expected = if v2 { V2_KEYS } else { KEYS };
    if !data.is_object() || keys(&data) != names(expected) {
        return Err(format!("result keys must be exactly {}; prompts, outputs and transcripts do not belong in a result file", expected.join(", ")).into());
    }
    for key in ["model", "run_date", "skills_version", "runner"] {
        let value = data[key]
            .as_str()
            .filter(|s| {
                !s.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
                    .is_empty()
            })
            .ok_or_else(|| format!("{key} must be a non-empty string"))?;
        if value.chars().count() > 120 || value.contains(['\r', '\n', '|']) {
            return Err(format!("{key} must be one line of at most 120 characters with no pipe; an output, transcript or note does not belong in a result file").into());
        }
    }
    let date = canonical_date(string(&data["run_date"]))
        .ok_or("run_date must be a real date, YYYY-MM-DD")?;
    if date != cap[1] {
        return Err("run_date must match the file name".into());
    }
    let results = &data["results"];
    let mut status = "legacy";
    if v2 {
        if data["schema_version"].as_u64() != Some(2) {
            return Err("schema_version must be 2".into());
        }
        status = string(&data["status"]);
        if !["task-only", "whole-card"].contains(&string(&data["input_mode"]))
            || !STATUSES[1..].contains(&status)
        {
            return Err("unknown trial input_mode or status".into());
        }
        let provenance = data["provenance"]
            .as_object()
            .filter(|m| !m.is_empty())
            .ok_or("provenance must identify at least one case")?;
        let mut digest_keys = names(DIGESTS);
        if status != "prepared" {
            digest_keys.insert("output_sha256".into());
        }
        for (case, evidence) in provenance {
            if !known.contains(case) {
                return Err(format!("unknown case: {}", repr(case)).into());
            }
            if !evidence.is_object() || keys(evidence) != digest_keys {
                return Err(format!("{case}: provenance fields do not match trial status").into());
            }
            if !evidence.as_object().unwrap().values().all(|v| {
                v.as_str().is_some_and(|s| {
                    s.len() == 64
                        && s.bytes()
                            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
                })
            }) {
                return Err(
                    format!("{case}: provenance must contain lower-case SHA-256 digests").into(),
                );
            }
        }
        if status != "confirmed" && results != &json!({}) {
            return Err("only human-confirmed trials may contain verdicts".into());
        }
        if status == "confirmed"
            && (!results.is_object() || keys(results) != keys(&data["provenance"]))
        {
            return Err("confirmed verdicts must cover exactly the provenance cases".into());
        }
    }
    let result_map = results
        .as_object()
        .filter(|m| !(m.is_empty() && ["legacy", "confirmed"].contains(&status)))
        .ok_or("results must map at least one card id to a verdict")?;
    for (case, verdict) in result_map {
        if !known.contains(case) {
            return Err(format!("unknown case: {}", repr(case)).into());
        }
        if !["pass", "fail"].contains(&string(verdict)) {
            return Err(format!("{case}: verdict must be pass or fail").into());
        }
    }
    for key in ["model", "skills_version", "runner"] {
        let value = string(&data[key]);
        let commit = key == "skills_version"
            && value.len() == 40
            && value
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b));
        text::sensitive(
            value,
            &if commit {
                vec!["unlabelled long numeric identifier".into()]
            } else {
                vec![]
            },
        )?;
    }
    Ok(status.to_owned())
}

pub fn check_published_inventories(skills: &Names, root: &Path) -> Result<()> {
    let marketplace = strict_json(
        &read_utf8(&root.join(".claude-plugin/marketplace.json"))?,
        ".claude-plugin/marketplace.json",
    )?;
    let declared = marketplace["plugins"]
        .as_array()
        .filter(|a| a.len() == 1)
        .and_then(|a| strings(&a[0]["skills"]))
        .ok_or(".claude-plugin/marketplace.json does not declare one plugin and its skill list")?;
    let declared = declared
        .iter()
        .map(|s| {
            s.split('/')
                .rfind(|part| !part.is_empty() && *part != ".")
                .unwrap_or("")
                .to_owned()
        })
        .collect::<Vec<_>>();
    let catalogue = read_utf8(&root.join("docs/skill-catalogue.md"))?;
    let regex = Regex::new(r"(?m)^\| *\[?`([a-z0-9][a-z0-9-]*)`")?;
    let catalogue = regex
        .captures_iter(catalogue.as_str())
        .map(|cap| cap.map(|cap| cap[1].to_owned()))
        .collect::<std::result::Result<Vec<_>, _>>()?;
    for (label, named) in [
        (".claude-plugin/marketplace.json", declared),
        ("docs/skill-catalogue.md", catalogue),
    ] {
        let actual: Names = named.iter().cloned().collect();
        if actual.len() != named.len() {
            return Err(format!("{label} names a skill twice").into());
        }
        if actual != *skills {
            return Err(format!(
                "{label} does not match the skill directory: missing={}, unknown={}",
                difference(skills, &actual),
                difference(&actual, skills)
            )
            .into());
        }
    }
    Ok(())
}
pub fn check_text(rel: &str, text: &str) -> Result<()> {
    for (index, line) in crate::splitlines(text).iter().enumerate() {
        if line.trim_end_matches([' ', '\t']) != *line {
            return Err(format!("{rel}:{} has trailing whitespace", index + 1).into());
        }
    }
    Ok(())
}

pub fn main(root: &Path) -> Result<(u8, String)> {
    let mut errors = Vec::new();
    let mut cases = Names::new();
    let mut expected = Names::new();
    let mut result_files = Names::new();
    let mut inventory = || -> Result<()> {
        cases = discover_case_names(root)?;
        expected = expected_validation(&cases);
        let (actual, results) = split_result_files(&inventory_validation_tree(root)?);
        result_files = results;
        if actual != expected {
            errors.push(format!(
                "validation inventory mismatch: missing={}, unexpected={}",
                difference(&expected, &actual),
                difference(&actual, &expected)
            ));
        }
        Ok(())
    };
    if let Err(e) = inventory() {
        errors.push(e.to_string());
    }
    let expected_all: Names = expected
        .union(&names(SUPPORT))
        .cloned()
        .chain(result_files.iter().cloned())
        .collect();
    match git_entries(&expected_all.iter().cloned().collect::<Vec<_>>(), root) {
        Err(e) => errors.push(e.to_string()),
        Ok(tracked) => {
            let actual: Names = tracked.keys().cloned().collect();
            if actual != expected_all {
                errors.push(format!(
                    "tracked inventory mismatch: missing={}, unexpected={}",
                    difference(&expected_all, &actual),
                    difference(&actual, &expected_all)
                ));
            }
            for (path, mode) in tracked {
                if !["100644", "100755"].contains(&mode.as_str()) {
                    errors.push(format!("tracked source has unsafe Git mode {mode}: {path}"));
                }
            }
        }
    }
    let mut skills = Names::new();
    let mut discover = || -> Result<()> {
        for directory in fs::read_dir(root.join(".claude/skills"))? {
            let directory = directory?;
            let path = directory.path();
            if path.is_dir() && !is_reparse_point(&path)? && path.join("SKILL.md").is_file() {
                skills.insert(
                    directory
                        .file_name()
                        .into_string()
                        .map_err(|_| "non-Unicode skill name")?,
                );
            }
        }
        Ok(())
    };
    if let Err(e) = discover() {
        errors.push(format!("cannot inventory target skills: {e}"));
    }
    if let Err(e) = check_published_inventories(&skills, root) {
        errors.push(e.to_string());
    }
    let mut sources = BTreeMap::new();
    for rel in &expected_all {
        let read = || -> Result<String> {
            let path = root.join(rel);
            check_expected_path(&path, root)?;
            check_ignored(rel, root)?;
            let text = read_utf8(&path)?;
            check_text(rel, &text)?;
            Ok(text)
        };
        match read() {
            Ok(text) => {
                sources.insert(rel.clone(), text);
            }
            Err(e) => errors.push(format!("{rel}: {e}")),
        }
    }
    let mut covered = Names::new();
    for name in &cases {
        let rel = format!("validation/cases/{name}");
        let Some(text) = sources.get(&rel) else {
            continue;
        };
        let mut check = || -> Result<()> {
            let (metadata, body) = parse_front_matter(text, name)?;
            let targets: Names = strings(&metadata["target_skills"])
                .unwrap()
                .into_iter()
                .collect();
            if !targets.is_subset(&skills) {
                return Err(
                    format!("unknown target skills: {}", difference(&targets, &skills)).into(),
                );
            }
            covered.extend(targets);
            let mut positions = Vec::new();
            for heading in SECTIONS {
                let found = body
                    .match_indices(heading)
                    .filter(|(at, _)| {
                        (*at == 0 || body.as_bytes()[at - 1] == b'\n')
                            && (*at + heading.len() == body.len()
                                || body.as_bytes()[*at + heading.len()] == b'\n')
                    })
                    .map(|(index, _)| index)
                    .collect::<Vec<_>>();
                if found.len() != 1 {
                    return Err(format!("section must appear exactly once: {heading}").into());
                }
                positions.push(found[0]);
            }
            if !positions.windows(2).all(|w| w[0] <= w[1]) {
                return Err("required sections are out of order".into());
            }
            if body
                .split('\n')
                .filter(|line| line.starts_with("# ") && !line[2..].starts_with('#'))
                .count()
                != 1
            {
                return Err("card must contain exactly one level-one title".into());
            }
            text::sensitive(&body, &[])
        };
        if let Err(e) = check() {
            errors.push(format!("{rel}: {e}"));
        }
    }
    if covered != skills {
        errors.push(format!(
            "card coverage does not exactly match skill inventory: missing={}, unknown={}",
            difference(&skills, &covered),
            difference(&covered, &skills)
        ));
    }
    let known = case_ids(&cases);
    if let Some(schema) = sources.get("validation/results.schema.json")
        && let Err(e) = check_results_schema(schema, &known)
    {
        errors.push(format!("validation/results.schema.json: {e}"));
    }
    let mut counts = BTreeMap::new();
    for status in STATUSES {
        counts.insert(*status, 0);
    }
    for rel in &result_files {
        if let Some(text) = sources.get(rel) {
            match check_result_file(rel, text, &known) {
                Ok(status) => *counts.get_mut(status.as_str()).unwrap() += 1,
                Err(e) => errors.push(format!("{rel}: {e}")),
            }
        }
    }
    if let Err(e) = text::sensitive(
        sources
            .get("validation/README.md")
            .map(String::as_str)
            .unwrap_or(""),
        &[],
    ) {
        errors.push(format!("validation/README.md: {e}"));
    }
    if !errors.is_empty() {
        let count = errors.len();
        return Ok((
            1,
            errors
                .into_iter()
                .map(|e| format!("ERROR: {e}\n"))
                .collect::<String>()
                + &format!("Validation failed with {count} error(s).\n"),
        ));
    }
    Ok((
        0,
        format!(
            "Validation pack checks passed: {} fabricated cards, {} skills, {} result records ({}), exact tracked inventory.\n",
            cases.len(),
            skills.len(),
            result_files.len(),
            STATUSES
                .iter()
                .map(|s| format!("{s}={}", counts[s]))
                .collect::<Vec<_>>()
                .join(", ")
        ),
    ))
}

pub fn cli(args: impl Iterator<Item = std::ffi::OsString>) -> Result<u8> {
    let mut root = std::env::current_dir()?;
    let mut args = args;
    while let Some(arg) = args.next() {
        if arg == "--root" {
            root = PathBuf::from(
                args.next()
                    .filter(|s| !s.as_encoded_bytes().starts_with(b"--"))
                    .ok_or("--root requires a path")?,
            );
        } else {
            return Err("usage: accounting-skills validate-validation [--root PATH]".into());
        }
    }
    let (code, output) = main(&root)?;
    use std::io::Write;
    std::io::stdout().write_all(crate::platform_text(&output).as_bytes())?;
    Ok(code)
}
