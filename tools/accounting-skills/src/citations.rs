// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! Checks that each ruling and legislative section a skill cites has a record
//! in that skill's `sources.json`.
//!
//! A ruling, determination, practice statement, guideline or TPB or ASIC
//! guidance number resolves when a record's title or address names the same
//! document. A section resolves when a record taken from a legislation register
//! (a Federal Register, ATO legal database or state or territory register
//! address) names the Act, regulations or instrument the section belongs to.
//! That instrument must be named in the section's own sentence: right after
//! the section ("s 8-1 of the ITAA 1997"), right before it ("ITAA 1997 s 8-1"),
//! or as the only instrument the sentence names apart from an amending Act and
//! one that owns another section. When the only Act a sentence names sits
//! right after its first section, it owns the sentence's other sections too.
//! A sentence may run across a paragraph's wrapped lines but never past a
//! blank line, heading, list item or table row. A section whose sentence names
//! no instrument, or more than one, is reported; "section 3 below" is a
//! cross-reference and is not counted. The check does not confirm that the
//! section exists or says what the skill claims.

use crate::{Result, canonical_root, discover_skills, platform_text, read_text};
use fancy_regex::{Captures, Regex};
use serde_json::Value;
use std::{
    collections::BTreeSet,
    ffi::OsString,
    fs,
    io::{self, Write},
    ops::Range,
    path::{Path, PathBuf},
    sync::LazyLock,
};

const RULING_PREFIXES: &str = r"TPB\((?:GS|I|EP)\)|PS LA|ATO ID|GSTR|GSTD|FBTR|WETR|WETD|FTR|FTD|SGR|SGD|PCG|LCR|LCG|CLR|MTR|TR|TD|CR|PR|MT|LI";
static RULING: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(&format!(
        r"(?<![A-Za-z0-9])({RULING_PREFIXES}) ?(\d{{2,4}})/(D?\d+)(?![0-9A-Za-z])"
    ))
    .unwrap()
});
static ASIC: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![A-Za-z0-9])(?:ASIC )?(RG|INFO) (\d+)(?![0-9/])").unwrap());
// An ATO legal database address runs the year and number together.
static DOCID: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r#"(?i)DocID=[A-Z]+/([A-Z]+)(\d+)(D\d+)?(?=/|$|&|"|\))"#).unwrap());
static TPB_SLUG: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)tpb-?(gs|i|ep)-?(\d+)-(\d{4})").unwrap());
static ASIC_SLUG: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)/(rg|info)-(\d+)(?![0-9])").unwrap());

/// Short names the skills use, with the full title each stands for.
const ABBREVIATIONS: &[(&str, &str)] = &[
    ("ITAA 1997", "Income Tax Assessment Act 1997"),
    ("ITAA 1936", "Income Tax Assessment Act 1936"),
    ("TAA 1953", "Taxation Administration Act 1953"),
    ("TAA", "Taxation Administration Act 1953"),
    (
        "GST Act",
        "A New Tax System (Goods and Services Tax) Act 1999",
    ),
    (
        "GST Regulations 2019",
        "A New Tax System (Goods and Services Tax) Regulations 2019",
    ),
    (
        "GST Regulations",
        "A New Tax System (Goods and Services Tax) Regulations 2019",
    ),
    ("FBTAA", "Fringe Benefits Tax Assessment Act 1986"),
    ("SGAA", "Superannuation Guarantee (Administration) Act 1992"),
    ("SIS Act", "Superannuation Industry (Supervision) Act 1993"),
    ("TASA", "Tax Agent Services Act 2009"),
    (
        "BIF Act 2017",
        "Building Industry Fairness (Security of Payment) Act 2017 (Qld)",
    ),
    (
        "BIF Act",
        "Building Industry Fairness (Security of Payment) Act 2017 (Qld)",
    ),
    (
        "BIF",
        "Building Industry Fairness (Security of Payment) Act 2017 (Qld)",
    ),
    (
        "QBCC Act 1991",
        "Queensland Building and Construction Commission Act 1991 (Qld)",
    ),
    (
        "QBCC Act",
        "Queensland Building and Construction Commission Act 1991 (Qld)",
    ),
    ("Corporations Act", "Corporations Act 2001"),
    (
        "AML/CTF Act",
        "Anti-Money Laundering and Counter-Terrorism Financing Act 2006",
    ),
    (
        "AML/CTF Rules",
        "Anti-Money Laundering and Counter-Terrorism Financing Rules 2025",
    ),
    (
        "TPB Code Determination",
        "Tax Agent Services (Code of Professional Conduct) Determination 2024",
    ),
    (
        "Code Determination",
        "Tax Agent Services (Code of Professional Conduct) Determination 2024",
    ),
    (
        "NSW SOP Act",
        "Building and Construction Industry Security of Payment Act 1999 (NSW)",
    ),
    ("Fair Work Act", "Fair Work Act 2009"),
    ("Fuel Tax Act", "Fuel Tax Act 2006"),
    (
        "CTF Act",
        "Anti-Money Laundering and Counter-Terrorism Financing Act 2006",
    ),
];
static ABBREVIATION: LazyLock<Regex> = LazyLock::new(|| {
    let mut names: Vec<_> = ABBREVIATIONS.iter().map(|(name, _)| *name).collect();
    names.sort_by_key(|name| std::cmp::Reverse(name.len()));
    // The names hold only letters, digits and spaces, so need no escaping.
    Regex::new(&format!(
        r"(?<![A-Za-z0-9])({})(?![A-Za-z0-9])",
        names.join("|")
    ))
    .unwrap()
});
const JURISDICTION: &str = "Cth|NSW|Vic|Qld|WA|SA|Tas|ACT|NT";
static TITLE_END: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(&format!(
        r"(?<![A-Za-z])(Act|Regulations?|Rules|Determination) (\d{{4}})(?![0-9])(?:\*? \(({JURISDICTION})\))?"
    ))
    .unwrap()
});
static TITLE_PARTS: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(&format!(r"^(.*?) (\d{{4}})(?: \(({JURISDICTION})\))?$")).unwrap());
const CONNECTORS: &[&str] = &["of", "and", "for", "the", "on", "in", "to", "-"];
const LEADING_NOISE: &[&str] = &[
    "The", "Under", "This", "See", "In", "Read", "Apply", "Use", "Record", "Check", "Confirm",
    "Open", "Each",
];
static REGISTER_ID: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![A-Za-z0-9])([CF]\d{4}[AL]\d{5})(?![A-Za-z0-9])").unwrap());
static PAC_ID: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"(?i)DocID=PAC/(\d{8})").unwrap());
static STATE_URL: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        r#"(?i)https?://(?:www\.)?legislation\.(?:nsw|qld|vic|sa|wa|tas|act|nt)\.gov\.au/[^\s)"\]]*"#,
    )
    .unwrap()
});
// The part of a state or territory register address that names the Act, in
// the order to try them: a Western Australian address also holds "/legislation/".
static STATE_IDS: LazyLock<Vec<Regex>> = LazyLock::new(|| {
    [
        r"law_a\d+",
        r"(?:act|sl)-\d{4}-\d+",
        r"/a/\d{4}-\d+",
        r"/acts/[a-z0-9-]+",
        r"path=/c/a/[a-z0-9 ]+",
        r"/legislation/[a-z0-9-]+",
    ]
    .iter()
    .map(|pattern| Regex::new(pattern).unwrap())
    .collect()
});
static STATE_HOST: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^https?://(?:www\.)?([^/]+)").unwrap());
static PROFESSIONAL_STANDARD: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![A-Za-z0-9])APES \d+").unwrap());
static LINK: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\[[^\]]*\]\([^)\s]+\)").unwrap());

const NUMBER: &str = r"\d+[A-Z]{0,3}(?:-\d+[A-Z]{0,3})?(?:\.\d+)?(?:\([0-9A-Za-z]{1,5}\))*";
static SECTION: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(&format!(
        r"(?<![A-Za-z0-9'’])(s|ss|[Ss]ections?|[Ss]ubsections?|regs?|regulations?) ({NUMBER}(?:(?:, | and | or | to ){NUMBER})*)"
    ))
    .unwrap()
});
static FIRST_NUMBER: LazyLock<Regex> = LazyLock::new(|| Regex::new(&format!("^{NUMBER}")).unwrap());
static LIST_SEPARATOR: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r", | and | or | to ").unwrap());
const PLURAL: &[&str] = &[
    "ss",
    "sections",
    "Sections",
    "subsections",
    "Subsections",
    "regs",
    "regulations",
];
// What may sit between a section and the Act named after it: "s 41-5 of the
// Fuel Tax Act 2006", "s 131-5 of Schedule 1 to the TAA 1953", "s 40-95 ITAA 1997",
// "s 28(2)(d) and (e) of the AML/CTF Act", "s 6-7, s 6-17 or s 6-18 of the Rules".
static FOLLOWING_GAP: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(&format!(
        r"^(?:,? (?:and|or|to) (?:\([0-9A-Za-z]{{1,5}}\))+|(?:,|,? and|,? or) (?:s|[Ss]ections?|[Ss]ubsections?|regs?|regulations?) {NUMBER})*[ *\[]*(?:of|in|under|to)? ?(?:Schedule \d+[A-Z]? (?:to|of) )?(?:the )?[ *\[]*$"
    ))
    .unwrap()
});
// A section followed by an instrument the text does not name: "s 31 of the Act".
static UNNAMED: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        r"^(?:,? (?:and|or|to) (?:\([0-9A-Za-z]{1,5}\))+)*,? (?:of|in|under) (the \*?(?:Act|Regulations?|Rules|Determination))(?![A-Za-z0-9]|\*? \d{4})",
    )
    .unwrap()
});
// What may sit between an Act and a section it names right after it:
// "Fuel Tax Act 2006 s 41-5", "*ITAA 1997* s 8-1", "[TASA](https://...) s 30-35".
// Not a bracket: "via s 50 of the Corporations Act (s 79(3))" cites another Act.
static PRECEDING_GAP: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^[*\]]*(?:\([^)\s]*\))?[ *]*$").unwrap());
// A sentence ends at a full stop, question or exclamation mark, the closing
// marks after it and a space, unless a lower-case letter or digit follows
// ("e.g. the", "No. 1"). A sentence never starts with a numeral.
static SENTENCE_END: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r#"[.!?][*_)\]'"’”]* +(?![ a-z0-9])"#).unwrap());
static LIST_ITEM: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^\s*(?:[-*+]|\d+[a-z]?[.)])\s").unwrap());

type Key = (&'static str, String);

/// An Act or other instrument named on a line. `keys` is `None` for a
/// professional standard, whose sections are not legislation.
struct Anchor {
    start: usize,
    end: usize,
    keys: Option<BTreeSet<Key>>,
}

/// A citation with no matching record.
#[derive(Debug, PartialEq, Eq)]
pub struct Unmatched {
    pub file: String,
    pub line: usize,
    pub citation: String,
    pub reason: String,
}

/// Counts over every Markdown file of every skill.
#[derive(Debug, Default)]
pub struct Report {
    pub rulings: usize,
    pub rulings_resolved: usize,
    pub sections: usize,
    pub sections_resolved: usize,
    pub unmatched: Vec<Unmatched>,
}

fn captures<'t>(regex: &Regex, text: &'t str) -> Result<Vec<Captures<'t, str>>> {
    Ok(regex
        .captures_iter(text)
        .collect::<std::result::Result<_, _>>()?)
}

fn group<'t>(captures: &Captures<'t, str>, index: usize) -> &'t str {
    captures.get(index).map_or("", |found| found.as_str())
}

fn span(captures: &Captures<'_, str>) -> (usize, usize) {
    let whole = captures.get(0).unwrap();
    (whole.start(), whole.end())
}

fn ruling_key(prefix: &str, year: &str, number: &str) -> String {
    format!(
        "{} {year}/{}",
        prefix.replace(' ', "").to_uppercase(),
        number.to_uppercase()
    )
}

/// Each ruling-style citation in `text`: where it starts, as written and as a key.
fn rulings(text: &str) -> Result<Vec<(usize, String, String)>> {
    let mut found = Vec::new();
    for found_ruling in captures(&RULING, text)? {
        found.push((
            span(&found_ruling).0,
            group(&found_ruling, 0).to_string(),
            ruling_key(
                group(&found_ruling, 1),
                group(&found_ruling, 2),
                group(&found_ruling, 3),
            ),
        ));
    }
    for guide in captures(&ASIC, text)? {
        found.push((
            span(&guide).0,
            group(&guide, 0).to_string(),
            format!("{} {}", group(&guide, 1), group(&guide, 2)),
        ));
    }
    Ok(found)
}

fn unescape(text: &str) -> String {
    text.replace("%2F", "/")
        .replace("%2f", "/")
        .replace("%28", "(")
        .replace("%29", ")")
        .replace("%20", " ")
}

/// The ruling keys a record's title and addresses name.
fn record_rulings(text: &str) -> Result<BTreeSet<String>> {
    let text = unescape(text);
    let mut keys: BTreeSet<String> = rulings(&text)?.into_iter().map(|(_, _, key)| key).collect();
    for document in captures(&DOCID, &text)? {
        let prefix = group(&document, 1).to_uppercase();
        let prefix = if prefix == "PS" {
            "PSLA".into()
        } else {
            prefix
        };
        let digits = group(&document, 2);
        let draft = group(&document, 3).to_uppercase();
        let key = if !draft.is_empty() {
            ruling_key(&prefix, digits, &draft)
        } else if digits.len() >= 5 && (digits.starts_with("19") || digits.starts_with("20")) {
            ruling_key(&prefix, &digits[..4], &digits[4..])
        } else if digits.len() >= 3 {
            ruling_key(&prefix, &digits[..2], &digits[2..])
        } else {
            continue;
        };
        keys.insert(key);
    }
    for guidance in captures(&TPB_SLUG, &text)? {
        keys.insert(ruling_key(
            &format!("TPB({})", group(&guidance, 1).to_uppercase()),
            group(&guidance, 2),
            group(&guidance, 3),
        ));
    }
    for guide in captures(&ASIC_SLUG, &text)? {
        keys.insert(format!(
            "{} {}",
            group(&guide, 1).to_uppercase(),
            group(&guide, 2)
        ));
    }
    Ok(keys)
}

fn previous(text: &str, end: usize) -> Option<(usize, char)> {
    text[..end].char_indices().next_back()
}

/// Walk back from a title's closing word over the words a title can hold, and
/// return them with the byte offset where the title starts.
fn title_words(text: &str, end: usize) -> (Vec<&str>, usize) {
    let mut words = Vec::new();
    let mut start = end;
    loop {
        let mut gap = start;
        while let Some((position, ' ' | '*')) = previous(text, gap) {
            gap = position;
        }
        let Some((position, character)) = previous(text, gap) else {
            break;
        };
        if character == ')' {
            let Some(open) = text[..position].rfind('(') else {
                break;
            };
            words.push(&text[open..gap]);
            start = open;
            continue;
        }
        let mut first = gap;
        while let Some((position, character)) = previous(text, first) {
            if character.is_alphanumeric() || matches!(character, '-' | '\'' | '’') {
                first = position;
            } else {
                break;
            }
        }
        let word = &text[first..gap];
        if word.chars().next().is_some_and(char::is_uppercase) || CONNECTORS.contains(&word) {
            words.push(word);
            start = first;
            continue;
        }
        break;
    }
    words.reverse();
    let mut skip = 0;
    while skip < words.len()
        && (CONNECTORS.contains(&words[skip])
            || LEADING_NOISE.contains(&words[skip])
            || words[skip].starts_with('('))
    {
        start += words[skip].len();
        while let Some(' ' | '*') = text[start..end].chars().next() {
            start += 1;
        }
        skip += 1;
    }
    (words.split_off(skip), start)
}

fn state_key(url: &str) -> String {
    let url = unescape(url).to_lowercase();
    let host = STATE_HOST
        .captures(url.as_str())
        .ok()
        .flatten()
        .map_or(String::new(), |found| group(&found, 1).to_string());
    let id = STATE_IDS
        .iter()
        .find_map(|pattern| pattern.find(url.as_str()).ok().flatten())
        .map_or_else(
            || {
                url.split('#')
                    .next()
                    .unwrap_or("")
                    .trim_end_matches('/')
                    .to_string()
            },
            |found| found.as_str().to_string(),
        );
    format!("{host} {id}")
}

fn full_title(title: &str) -> String {
    ABBREVIATIONS
        .iter()
        .find(|(name, _)| *name == title)
        .map_or_else(|| title.to_string(), |(_, full)| (*full).to_string())
}

/// The register identifiers and addresses in `text`: Federal Register series,
/// ATO legal database Acts and state or territory register addresses. A
/// compilation identifier names a version, not an instrument, so it is skipped.
fn identifiers(text: &str) -> Result<Vec<(usize, Key)>> {
    let mut found = Vec::new();
    for (regex, kind) in [(&*REGISTER_ID, "register"), (&*PAC_ID, "pac")] {
        for id in captures(regex, text)? {
            found.push((span(&id).0, (kind, group(&id, 1).to_string())));
        }
    }
    for url in captures(&STATE_URL, text)? {
        found.push((span(&url).0, ("state", state_key(group(&url, 0)))));
    }
    Ok(found)
}

/// Every Act or other instrument named on `line`, in order. An identifier or
/// register address adds its key to a title named in the same Markdown link;
/// alone it names nothing, since a bare compilation or amending instrument
/// number is not the Act a section belongs to.
fn anchors(line: &str) -> Result<Vec<Anchor>> {
    let mut found: Vec<Anchor> = Vec::new();
    for name in captures(&ABBREVIATION, line)? {
        let (start, end) = span(&name);
        found.push(Anchor {
            start,
            end,
            keys: Some(BTreeSet::from([("title", full_title(group(&name, 1)))])),
        });
    }
    let named: Vec<(usize, usize)> = found.iter().map(|a| (a.start, a.end)).collect();
    for title in captures(&TITLE_END, line)? {
        let (kind_start, end) = span(&title);
        if named.iter().any(|(s, e)| (*s..*e).contains(&kind_start)) {
            continue;
        }
        let (words, start) = title_words(line, kind_start);
        if words.is_empty() {
            continue;
        }
        let mut text = format!(
            "{} {} {}",
            words.join(" "),
            group(&title, 1),
            group(&title, 2)
        );
        if !group(&title, 3).is_empty() {
            text.push_str(&format!(" ({})", group(&title, 3)));
        }
        found.push(Anchor {
            start,
            end,
            keys: Some(BTreeSet::from([("title", full_title(&text))])),
        });
    }
    let identified = identifiers(line)?;
    for link in LINK.find_iter(line) {
        let link = link?;
        let range = link.start()..link.end();
        let keys: Vec<Key> = identified
            .iter()
            .filter(|(start, _)| range.contains(start))
            .map(|(_, key)| key.clone())
            .collect();
        for anchor in found
            .iter_mut()
            .filter(|anchor| range.contains(&anchor.start))
        {
            if let Some(names) = anchor.keys.as_mut() {
                names.extend(keys.iter().cloned());
            }
        }
    }
    for standard in PROFESSIONAL_STANDARD.find_iter(line) {
        let standard = standard?;
        found.push(Anchor {
            start: standard.start(),
            end: standard.end(),
            keys: None,
        });
    }
    found.sort_by_key(|anchor| anchor.start);
    Ok(found)
}

fn title_parts(title: &str) -> Option<(Vec<&str>, &str, &str)> {
    let parts = TITLE_PARTS.captures(title).ok().flatten()?;
    Some((
        group(&parts, 1).split(' ').collect(),
        group(&parts, 2),
        group(&parts, 3),
    ))
}

fn titles(keys: &BTreeSet<Key>) -> Vec<(Vec<&str>, &str, &str)> {
    keys.iter()
        .filter(|(kind, _)| *kind == "title")
        .filter_map(|(_, title)| title_parts(title))
        .collect()
}

/// Whether two sets of keys identify the same instrument. Titles match when
/// the year agrees, a stated jurisdiction agrees, and the shorter title of at
/// least 2 words ends the longer, which tolerates a word a sentence or a
/// record title puts in front.
fn same_instrument(cited: &BTreeSet<Key>, recorded: &BTreeSet<Key>) -> bool {
    if !cited.is_disjoint(recorded) {
        return true;
    }
    let recorded = titles(recorded);
    titles(cited).iter().any(|(words, year, place)| {
        recorded.iter().any(|(other, other_year, other_place)| {
            let (short, long) = if words.len() <= other.len() {
                (words, other)
            } else {
                (other, words)
            };
            year == other_year
                && (place.is_empty() || other_place.is_empty() || place == other_place)
                && short.len() >= 2
                && long.ends_with(short)
        })
    })
}

fn section_numbers(section: &Captures<'_, str>) -> Vec<String> {
    let body = group(section, 2);
    if PLURAL.contains(&group(section, 1)) {
        let mut numbers = Vec::new();
        let mut start = 0;
        for separator in LIST_SEPARATOR.find_iter(body).flatten() {
            numbers.push(body[start..separator.start()].to_string());
            start = separator.end();
        }
        numbers.push(body[start..].to_string());
        numbers
    } else {
        let first = FIRST_NUMBER.find(body).ok().flatten();
        vec![first.map_or(body, |found| found.as_str()).to_string()]
    }
}

fn markdown_files(folder: &Path, files: &mut Vec<PathBuf>) -> Result<()> {
    let mut entries = fs::read_dir(folder)?
        .map(|entry| entry.map(|entry| entry.path()))
        .collect::<io::Result<Vec<_>>>()?;
    entries.sort();
    for path in entries {
        let kind = fs::symlink_metadata(&path)?.file_type();
        if kind.is_dir() {
            markdown_files(&path, files)?;
        } else if kind.is_file() && path.extension().is_some_and(|ext| ext == "md") {
            files.push(path);
        }
    }
    Ok(())
}

/// What each record of a skill's `sources.json` names: its rulings, and the
/// instrument of each record taken from a legislation register. A record from
/// anywhere else, such as an ATO web page or a ruling, may name an Act in its
/// title without holding the Act's text, so it owns no section.
fn records(folder: &Path) -> Result<(BTreeSet<String>, Vec<BTreeSet<Key>>)> {
    let index = folder.join("sources.json");
    let mut rulings = BTreeSet::new();
    let mut instruments = Vec::new();
    if !index.is_file() {
        return Ok((rulings, instruments));
    }
    let payload: Value = serde_json::from_str(&read_text(&index)?)?;
    let sources = payload["sources"]
        .as_array()
        .ok_or_else(|| format!("{}: sources must be a list", index.display()))?;
    for (position, source) in sources.iter().enumerate() {
        let source = source.as_object().ok_or_else(|| {
            format!(
                "{}: record {} is not an object",
                index.display(),
                position + 1
            )
        })?;
        let text = ["title", "url", "final_url", "content_url"]
            .iter()
            .filter_map(|field| source.get(*field).and_then(Value::as_str))
            .collect::<Vec<_>>()
            .join(" ");
        rulings.extend(record_rulings(&text)?);
        let text = unescape(&text);
        let mut keys: BTreeSet<Key> = identifiers(&text)?
            .into_iter()
            .map(|(_, key)| key)
            .collect();
        if keys.is_empty() {
            continue;
        }
        for anchor in anchors(&text)? {
            keys.extend(anchor.keys.unwrap_or_default());
        }
        instruments.push(keys);
    }
    Ok((rulings, instruments))
}

/// A paragraph's wrapped lines joined by spaces, or a heading, table row or
/// list item with the lines that continue it, with the offset at which each
/// of its lines starts and that line's number.
struct Block {
    text: String,
    lines: Vec<(usize, usize)>,
}

impl Block {
    fn line(&self, offset: usize) -> usize {
        self.lines[self.lines.partition_point(|(start, _)| *start <= offset) - 1].1
    }
}

fn blocks(text: &str) -> Result<Vec<Block>> {
    let mut found: Vec<Block> = Vec::new();
    let mut open = false;
    for (index, line) in text.lines().enumerate() {
        let trimmed = line.trim_start();
        if trimmed.is_empty() {
            open = false;
            continue;
        }
        let opens = ["#", "|", ">", "```", "---"]
            .iter()
            .any(|mark| trimmed.starts_with(mark))
            || LIST_ITEM.is_match(line)?;
        match found.last_mut() {
            Some(block) if open && !opens => {
                block.text.push(' ');
                block.lines.push((block.text.len(), index + 1));
                block.text.push_str(trimmed);
            }
            _ => found.push(Block {
                text: line.to_string(),
                lines: vec![(0, index + 1)],
            }),
        }
        open = !["#", "|", "---"]
            .iter()
            .any(|mark| trimmed.starts_with(mark));
    }
    Ok(found)
}

fn sentences(text: &str) -> Result<Vec<Range<usize>>> {
    let mut found = Vec::new();
    let mut start = 0;
    for end in SENTENCE_END.find_iter(text) {
        let end = end?.end();
        found.push(start..end);
        start = end;
    }
    found.push(start..text.len());
    Ok(found)
}

fn same_anchor(one: &Anchor, other: &Anchor) -> bool {
    match (&one.keys, &other.keys) {
        (Some(one), Some(other)) => same_instrument(one, other),
        (None, None) => true,
        _ => false,
    }
}

/// The instrument each section in `sentence` belongs to, as an index into
/// `named`: the one named right after or right before the section, otherwise
/// the only one the sentence names, leaving out an amending Act and one named
/// right after another section, which owns that section alone unless it owns
/// the sentence's first section and no other Act is named. `Err` says why none
/// does, including for a section said to be of "the Act" without naming it.
fn owners(
    sentence: &str,
    named: &[Anchor],
    sections: &[Captures<'_, str>],
) -> Result<Vec<std::result::Result<usize, String>>> {
    let mut beside = Vec::new();
    let mut tied = vec![false; named.len()];
    for section in sections {
        let (start, end) = span(section);
        let following = match named.iter().position(|anchor| anchor.start >= end) {
            Some(next) if FOLLOWING_GAP.is_match(&sentence[end..named[next].start])? => {
                tied[next] = true;
                Some(Ok(next))
            }
            _ => UNNAMED
                .captures(&sentence[end..])?
                .map(|unnamed| Err(format!("names its Act only as '{}'", group(&unnamed, 1)))),
        };
        let preceding = match named.iter().rposition(|anchor| anchor.end <= start) {
            Some(last) if PRECEDING_GAP.is_match(&sentence[named[last].end..start])? => {
                Some(Ok(last))
            }
            _ => None,
        };
        beside.push(following.or(preceding));
    }
    // An amending Act holds amendments to other Acts, not the sections they
    // insert, so it owns only a section named right beside it.
    let amending = |anchor: &Anchor| {
        anchor.keys.as_ref().is_some_and(|keys| {
            keys.iter()
                .any(|(kind, name)| *kind == "title" && name.contains(" Amendment "))
        })
    };
    let mut distinct: Vec<usize> = Vec::new();
    for index in (0..named.len()).filter(|&index| !tied[index] && !amending(&named[index])) {
        if !distinct
            .iter()
            .any(|&other| same_anchor(&named[index], &named[other]))
        {
            distinct.push(index);
        }
    }
    // Where every Act the sentence names is beside a section, the others share
    // the Act only if it is the one Act named and it owns the opening section:
    // "Section 14ZU of the TAA 1953 requires ... the section 14ZW period".
    let opening = match beside.first() {
        Some(Some(Ok(first)))
            if !amending(&named[*first])
                && (0..named.len())
                    .filter(|&index| tied[index])
                    .all(|index| same_anchor(&named[index], &named[*first])) =>
        {
            Some(*first)
        }
        _ => None,
    };
    let shared = match (&distinct[..], opening) {
        ([], Some(first)) => Ok(first),
        ([], None) if tied.contains(&true) => {
            Err("names its Act only beside another section".to_string())
        }
        ([], None) => Err("names no Act".to_string()),
        ([only], _) => Ok(*only),
        _ => {
            let names: Vec<_> = distinct
                .iter()
                .map(|&index| sentence[named[index].start..named[index].end].trim_matches('*'))
                .collect();
            Err(format!(
                "its sentence names more than one Act ({})",
                names.join("; ")
            ))
        }
    };
    Ok(beside
        .into_iter()
        .map(|owner| owner.unwrap_or_else(|| shared.clone()))
        .collect())
}

/// Check every skill under `root`.
pub fn check(root: &Path) -> Result<Report> {
    let mut report = Report::default();
    for skill in discover_skills(root)? {
        let folder = root.join(".claude/skills").join(&skill);
        let (recorded_rulings, instruments) = records(&folder)?;
        let recorded =
            |keys: &BTreeSet<Key>| instruments.iter().any(|other| same_instrument(keys, other));
        let mut files = Vec::new();
        markdown_files(&folder, &mut files)?;
        for path in files {
            let file = path
                .strip_prefix(root)?
                .to_string_lossy()
                .replace('\\', "/");
            for block in blocks(&read_text(&path)?)? {
                let mut missing = Vec::new();
                for (start, citation, key) in rulings(&block.text)? {
                    report.rulings += 1;
                    if recorded_rulings.contains(&key) {
                        report.rulings_resolved += 1;
                    } else {
                        missing.push((start, citation, "no record names it".to_string()));
                    }
                }
                for range in sentences(&block.text)? {
                    let sentence = &block.text[range.clone()];
                    let named = anchors(sentence)?;
                    // "See section 3 below" points within the skill.
                    let mut sections = Vec::new();
                    for section in captures(&SECTION, sentence)? {
                        let rest = &sentence[span(&section).1..];
                        if !rest.starts_with(" below") && !rest.starts_with(" above") {
                            sections.push(section);
                        }
                    }
                    let owned = owners(sentence, &named, &sections)?;
                    for (section, owner) in sections.iter().zip(owned) {
                        let resolution = match owner.map(|index| &named[index].keys) {
                            Ok(None) => continue,
                            Ok(Some(keys)) => recorded(keys).then_some(()).ok_or_else(|| {
                                let names: Vec<_> =
                                    keys.iter().map(|(_, name)| name.as_str()).collect();
                                format!("no record names its Act ({})", names.join("; "))
                            }),
                            Err(reason) => Err(reason),
                        };
                        for number in section_numbers(section) {
                            report.sections += 1;
                            match &resolution {
                                Ok(()) => report.sections_resolved += 1,
                                Err(reason) => missing.push((
                                    range.start + span(section).0,
                                    format!("{} {number}", group(section, 1)),
                                    reason.clone(),
                                )),
                            }
                        }
                    }
                }
                missing.sort_by_key(|(start, _, _)| block.line(*start));
                for (start, citation, reason) in missing {
                    report.unmatched.push(Unmatched {
                        file: file.clone(),
                        line: block.line(start),
                        citation,
                        reason,
                    });
                }
            }
        }
    }
    Ok(report)
}

/// Render the report: one line per unmatched citation, then the totals.
pub fn render(report: &Report) -> String {
    let mut text = String::new();
    for missing in &report.unmatched {
        text.push_str(&format!(
            "{}:{}: {}: {}\n",
            missing.file, missing.line, missing.citation, missing.reason
        ));
    }
    let total = report.rulings + report.sections;
    let resolved = report.rulings_resolved + report.sections_resolved;
    text.push_str(&format!(
        "{resolved} of {total} citations resolve to a sources.json record: \
         {} of {} rulings and guidance, {} of {} legislative sections.\n",
        report.rulings_resolved, report.rulings, report.sections_resolved, report.sections
    ));
    text
}

/// Runs the `check-citations` command. Exit 2 when any citation is unmatched.
pub fn cli(args: impl Iterator<Item = OsString>) -> Result<u8> {
    let mut args = args;
    let mut root = std::env::current_dir()?;
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--root") => {
                root = PathBuf::from(
                    args.next()
                        .filter(|arg| !arg.as_encoded_bytes().starts_with(b"-"))
                        .ok_or("--root requires a path")?,
                );
            }
            _ => return Err("usage: accounting-skills check-citations [--root PATH]".into()),
        }
    }
    let root = canonical_root(&root)?;
    if discover_skills(&root)?.is_empty() {
        return Err("--root has no skills under .claude/skills".into());
    }
    let report = check(&root)?;
    io::stdout().write_all(platform_text(&render(&report)).as_bytes())?;
    Ok(if report.unmatched.is_empty() { 0 } else { 2 })
}

#[cfg(test)]
mod tests {
    use super::{anchors, record_rulings, rulings, same_instrument, title_words};

    #[test]
    fn ato_addresses_split_the_year_from_the_number() {
        let keys = record_rulings(
            "https://www.ato.gov.au/law/view/document?DocID=TXR/TR20103/NAT/ATO/00001 \
             https://www.ato.gov.au/law/view/document?DocID=TXR/TR9711/NAT/ATO/00001 \
             https://www.ato.gov.au/law/view/document?DocID=PSR/PS20114/NAT/ATO/00001 \
             https://www.ato.gov.au/law/view/document?DocID=DXT/TD2026D1/NAT/ATO/00001 \
             https://www.tpb.gov.au/tpb-gs-07-2011-claiming-lien-over-client-property",
        )
        .unwrap();
        for key in [
            "TR 2010/3",
            "TR 97/11",
            "PSLA 2011/4",
            "TD 2026/D1",
            "TPB(GS) 07/2011",
        ] {
            assert!(keys.contains(key), "{key} missing from {keys:?}");
        }
        assert!(!keys.contains("TR 2010/31"));
    }

    #[test]
    fn a_ruling_number_must_end_where_the_citation_ends() {
        let found: Vec<_> = rulings("TR 2010/31 and PS LA 2011/4 but not TR 2010/3A1")
            .unwrap()
            .into_iter()
            .map(|(_, _, key)| key)
            .collect();
        assert_eq!(found, ["TR 2010/31", "PSLA 2011/4"]);
    }

    #[test]
    fn a_title_starts_after_the_sentence_words_before_it() {
        let line = "Read the *Superannuation Guarantee (Administration) Act 1992* now";
        let end = line.find(" Act 1992").unwrap() + 1;
        let (words, start) = title_words(line, end);
        assert_eq!(words, ["Superannuation", "Guarantee", "(Administration)"]);
        assert_eq!(&line[start..start + 5], "Super");
    }

    #[test]
    fn titles_match_across_jurisdiction_and_leading_words_but_not_years() {
        let keys = |line: &str| anchors(line).unwrap().remove(0).keys.unwrap();
        let recorded = keys("Payroll Tax Act 2007 (NSW)");
        assert!(same_instrument(
            &keys("the Payroll Tax Act 2007"),
            &recorded
        ));
        assert!(!same_instrument(
            &keys("Payroll Tax Act 2007 (Vic)"),
            &recorded
        ));
        assert!(!same_instrument(&keys("Payroll Tax Act 2008"), &recorded));
        assert!(same_instrument(
            &keys("ITAA 1997"),
            &keys("Federal Register: Income Tax Assessment Act 1997")
        ));
    }
}
