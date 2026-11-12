// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! Checks that each ruling and legislative section a skill cites has a record
//! in that skill's `sources.json`.
//!
//! A ruling, determination, practice statement, guideline or TPB or ASIC
//! guidance number resolves when a record's title or address names the same
//! document. A section resolves when a record whose address is a legislation
//! register document (on the Federal Register, the ATO legal database or a
//! state or territory register) is a copy of the Act, regulations or
//! instrument the section belongs to: the first instrument the record's title
//! names, in the register's jurisdiction, with a year its identifier allows.
//! That instrument must be named in the section's own sentence: right after
//! the section ("s 8-1 of the ITAA 1997"), right before it ("ITAA 1997 s 8-1"),
//! or as the only instrument the sentence names apart from an amending Act and
//! one that owns another section. When the only Act a sentence names sits
//! right after its first section, it owns the sentence's other sections too.
//! A sentence may run across a paragraph's wrapped lines but never past a
//! blank line, heading, list item or table row, and one that starts with a
//! section ("s 8-1 allows") is a new sentence. A section whose sentence names
//! no instrument, or more than one, or that is said to be of an instrument the
//! text does not name in full ("of the Act", "of that Act", "of the
//! Administration Act"), is reported; "section 3 below" is a cross-reference
//! and is not counted.
//!
//! Where `tools/accounting-skills/section-index/` holds the Act's section
//! list, a resolved section must also appear in it, ignoring subsection and
//! paragraph suffixes, or be listed with a reason in that folder's
//! `exceptions.txt`. A section of an Act with no list is counted as not
//! indexed. The check does not confirm that a section says what the skill
//! claims.

use crate::{Result, canonical_root, discover_skills, platform_text, read_text};
use chrono::NaiveDate;
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
// The addresses of a document on a legislation register. A Federal Register
// series identifier names an Act (A) or another instrument; a compilation (C)
// names a version, so it is not one. In an Act's identifier the year is the
// Act's, except that many Acts made before 2005 carry 2004 ("C2004A05138" is
// the Income Tax Assessment Act 1997).
static FEDERAL_DOCUMENT: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        r"^https?://(?:www\.)?legislation\.gov\.au/(?:Details/)?(([CF])(\d{4})([ABD-Z])\d{5})(?![A-Za-z0-9])",
    )
    .unwrap()
});
// The ATO legal database's copy of an Act: the year, then the Act's number.
static PAC_DOCUMENT: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)^https?://(?:www\.)?ato\.gov\.au/law/view/document\?(?:\S*&)?DocID=PAC/((\d{4})\d{4})(?![0-9])")
        .unwrap()
});
static STATE_DOCUMENT: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)^https?://(?:www\.)?legislation\.(nsw|qld|vic|sa|wa|tas|act|nt)\.gov\.au/")
        .unwrap()
});
static YEAR: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![0-9])(?:18|19|20)\d{2}(?![0-9])").unwrap());
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
static PROFESSIONAL_STANDARD: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![A-Za-z0-9])APES \d+").unwrap());
static LINK: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\[[^\]]*\]\([^)\s]+\)").unwrap());

const NUMBER: &str = r"\d+[A-Z]*(?:-\d+[A-Z]*)?(?:\.\d+[A-Z]*)?(?:\([0-9A-Za-z]{1,5}\))*";
static SECTION: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(&format!(
        r"(?<![A-Za-z0-9'’])(s|ss|[Ss]ections?|[Ss]ubsections?|[Rr]egs?|[Rr]egulations?) ({NUMBER}(?:(?:, | and | or | to ){NUMBER})*)(?![A-Za-z0-9])"
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
    "Regs",
    "regulations",
    "Regulations",
];
// What may sit between a section and the Act named after it: "s 41-5 of the
// Fuel Tax Act 2006", "s 131-5 of Schedule 1 to the TAA 1953", "s 40-95 ITAA 1997",
// "s 28(2)(d) and (e) of the AML/CTF Act", "s 6-7, s 6-17 or s 6-18 of the Rules".
static FOLLOWING_GAP: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(&format!(
        r"^(?:,? (?:and|or|to) (?:\([0-9A-Za-z]{{1,5}}\))+|(?:,|,? and|,? or) (?:s|[Ss]ections?|[Ss]ubsections?|[Rr]egs?|[Rr]egulations?) {NUMBER})*[ *\[]*(?:of|in|under|to)? ?(?:Schedule \d+[A-Z]? (?:to|of) )?(?:the )?[ *\[]*$"
    ))
    .unwrap()
});
// A section followed by an instrument the text does not name in full: "s 31 of
// the Act", "s 44 of the Administration Act", "s 8-1 of that Act".
static UNNAMED: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        r"^(?:,? (?:and|or|to) (?:\([0-9A-Za-z]{1,5}\))+)*,? (?:of|in|under) ((?:the|that|this) \*?(?:[A-Z(][\w/()'’-]* )*(?:Act|Regulations?|Rules|Determination))(?![A-Za-z0-9]|\*? \d{4})",
    )
    .unwrap()
});
// Words that describe an Act as amending another: "the X Act 2026 inserted s
// 26-155", "s 26-155 as inserted by the X Act 2026".
static AMENDS: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        r"^\*?,? (?:which |that )?(?:inserted|inserts|amended|amends|substituted|substitutes|repealed|repeals|omitted|omits)\b",
    )
    .unwrap()
});
static AMENDED_BY: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"\b(?:inserted|amended|substituted|repealed|omitted) by (?:the )?[*\[]*$").unwrap()
});
// What may sit between an Act and a section it names right after it:
// "Fuel Tax Act 2006 s 41-5", "*ITAA 1997* s 8-1", "[TASA](https://...) s 30-35".
// Not a bracket: "via s 50 of the Corporations Act (s 79(3))" cites another Act.
static PRECEDING_GAP: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^[*\]]*(?:\([^)\s]*\))?[ *]*$").unwrap());
// Case and digits do not decide sentence ownership. Only explicit
// abbreviations keep a full stop inside the sentence.
static SENTENCE_END: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r#"[.!?][*_)\]'"’”]* +"#).unwrap());
static ABBREVIATION_END: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(?:e\.g|i\.e)\.$").unwrap());
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

/// A citation with no matching record, a section absent from its Act's
/// index, or an exception no cited section needs.
#[derive(Debug, PartialEq, Eq)]
pub struct Unmatched {
    pub file: String,
    pub line: usize,
    pub citation: String,
    pub reason: String,
}

/// Counts over every Markdown file of every skill. Each resolved section is
/// counted once more: as existing, absent or a listed exception when its Act
/// has a section index, otherwise as not indexed.
#[derive(Debug, Default)]
pub struct Report {
    pub rulings: usize,
    pub rulings_resolved: usize,
    pub sections: usize,
    pub sections_resolved: usize,
    pub sections_exist: usize,
    pub sections_absent: usize,
    pub sections_excepted: usize,
    pub sections_not_indexed: usize,
    pub unmatched: Vec<Unmatched>,
}

const SECTION_INDEX: &str = "tools/accounting-skills/section-index";
const EXCEPTIONS: &str = "exceptions.txt";
static SECTION_ID: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^\d+[A-Z]*(?:-\d+[A-Z]*)?(?:\.\d+[A-Z]*)?$").unwrap());
static REGISTER_ID: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^[CF]\d{4}[A-Z]\d{5}$").unwrap());

/// The sections of one Commonwealth Act or instrument, as its register
/// compilation's table of contents lists them.
struct SectionIndex {
    register_id: String,
    title: String,
    compilation: String,
    keys: BTreeSet<Key>,
    sections: BTreeSet<String>,
    /// Whether any listed section number holds a hyphen. Only in a list with
    /// none does "ss 17A-18C" read as a range.
    hyphenated: bool,
}

/// A cited section deliberately absent from its Act's index, such as one a
/// Bill proposes or one since repealed.
struct Exception {
    line: usize,
    register_id: String,
    section: String,
    used: bool,
}

fn section_index(path: &Path) -> Result<SectionIndex> {
    let name = path.display();
    let mut fields = std::collections::BTreeMap::new();
    let mut sections = BTreeSet::new();
    for (number, line) in read_text(path)?.lines().enumerate() {
        if let Some(header) = line.strip_prefix("# ") {
            let (key, value) = header
                .split_once(": ")
                .ok_or_else(|| format!("{name}:{}: expected '# key: value'", number + 1))?;
            if fields.insert(key.to_string(), value.to_string()).is_some() {
                return Err(format!("{name}:{}: repeated field {key}", number + 1).into());
            }
        } else if SECTION_ID.is_match(line)? {
            if !sections.insert(line.to_string()) {
                return Err(format!("{name}:{}: repeated section {line}", number + 1).into());
            }
        } else {
            return Err(format!("{name}:{}: not a section number: {line}", number + 1).into());
        }
    }
    let mut field = |key: &str| {
        fields
            .remove(key)
            .filter(|value| !value.is_empty())
            .ok_or_else(|| format!("{name}: missing field {key}"))
    };
    let title = field("title")?;
    let register_id = field("register-id")?;
    let compilation = field("compilation")?;
    for provenance in ["compilation-number", "source"] {
        field(provenance)?;
    }
    for date in ["in-force-from", "retrieved"] {
        let value = field(date)?;
        if value.len() != 10 || NaiveDate::parse_from_str(&value, "%Y-%m-%d").is_err() {
            return Err(format!("{name}: {date} must be a date written YYYY-MM-DD").into());
        }
    }
    let digest = field("sha256")?;
    if digest.len() != 64
        || !digest
            .bytes()
            .all(|byte| matches!(byte, b'0'..=b'9' | b'a'..=b'f'))
    {
        return Err(format!("{name}: sha256 must be 64 lower-case hexadecimal digits").into());
    }
    if let Some(key) = fields.keys().next() {
        return Err(format!("{name}: unknown field {key}").into());
    }
    if !REGISTER_ID.is_match(&register_id)? || path.file_stem() != Some(register_id.as_ref()) {
        return Err(format!("{name}: the file must be named REGISTER-ID.txt").into());
    }
    if title_parts(&title).is_none() {
        return Err(format!("{name}: the title must end with its year").into());
    }
    Ok(SectionIndex {
        keys: BTreeSet::from([
            ("title", format!("{title} (Cth)")),
            ("register", register_id.clone()),
        ]),
        register_id,
        title,
        compilation,
        hyphenated: sections.iter().any(|section| section.contains('-')),
        sections,
    })
}

/// The section indexes under `root`, and the exceptions they allow.
fn section_indexes(root: &Path) -> Result<(Vec<SectionIndex>, Vec<Exception>)> {
    let folder = root.join(SECTION_INDEX);
    let mut indexes = Vec::new();
    let mut exceptions = Vec::new();
    if !folder.is_dir() {
        return Ok((indexes, exceptions));
    }
    let mut paths = fs::read_dir(&folder)?
        .map(|entry| entry.map(|entry| entry.path()))
        .collect::<io::Result<Vec<_>>>()?;
    paths.sort();
    for path in paths.iter().filter(|path| {
        path.extension().is_some_and(|ext| ext == "txt")
            && path.file_name() != Some(EXCEPTIONS.as_ref())
    }) {
        indexes.push(section_index(path)?);
    }
    let path = folder.join(EXCEPTIONS);
    if !path.is_file() {
        return Ok((indexes, exceptions));
    }
    for (number, line) in read_text(&path)?.lines().enumerate() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let malformed = || {
            format!(
                "{}:{}: expected 'REGISTER-ID SECTION: reason'",
                path.display(),
                number + 1
            )
        };
        let (cited, reason) = line.split_once(": ").ok_or_else(malformed)?;
        let (register_id, section) = cited.split_once(' ').ok_or_else(malformed)?;
        if reason.trim().is_empty() || !SECTION_ID.is_match(section)? {
            return Err(malformed().into());
        }
        if !indexes.iter().any(|index| index.register_id == register_id) {
            return Err(format!(
                "{}:{}: no section index for {register_id}",
                path.display(),
                number + 1
            )
            .into());
        }
        if let Some(earlier) = exceptions.iter().find(|exception: &&Exception| {
            exception.register_id == register_id && exception.section == section
        }) {
            return Err(format!(
                "{}:{}: repeats the exception on line {}",
                path.display(),
                number + 1,
                earlier.line
            )
            .into());
        }
        exceptions.push(Exception {
            line: number + 1,
            register_id: register_id.to_string(),
            section: section.to_string(),
            used: false,
        });
    }
    Ok((indexes, exceptions))
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
            if character.is_alphanumeric() || matches!(character, '-' | '\'' | '’' | '/') {
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

/// The full title a short name stands for. An explicit title keeps its own
/// year and jurisdiction: "Corporations Act 2001" is the Corporations Act, but
/// "Fair Work Act 1994 (SA)" is not the Fair Work Act 2009.
fn full_title(title: &str) -> String {
    let full = |name: &str| {
        ABBREVIATIONS
            .iter()
            .find(|(short, _)| *short == name)
            .map(|(_, full)| *full)
    };
    if let Some(full) = full(title) {
        return full.to_string();
    }
    if let Some((words, year, place)) = title_parts(title)
        && let Some(full) = full(&words.join(" "))
        && let Some((_, full_year, full_place)) = title_parts(full)
        && full_year == year
        && (place.is_empty() || place == full_place)
    {
        return full.to_string();
    }
    title.to_string()
}

/// A legislation register's copy of a document: its identifier, the
/// jurisdiction whose register holds it and, where the identifier shows it,
/// the year of the Act it is.
struct RegisterCopy {
    id: Key,
    place: &'static str,
    year: Option<(String, bool)>,
    act: Option<bool>,
}

/// The register copy at `url`, or `None` when `url` is not the address of a
/// document on a legislation register.
fn register_copy(url: &str) -> Result<Option<RegisterCopy>> {
    let url = unescape(url);
    if let Some(found) = FEDERAL_DOCUMENT.captures(url.as_str())? {
        let act = group(&found, 2) == "C" && group(&found, 4) == "A";
        return Ok(Some(RegisterCopy {
            id: ("register", group(&found, 1).to_string()),
            place: "Cth",
            year: act.then(|| (group(&found, 3).to_string(), true)),
            act: Some(act),
        }));
    }
    if let Some(found) = PAC_DOCUMENT.captures(url.as_str())? {
        return Ok(Some(RegisterCopy {
            id: ("pac", group(&found, 1).to_string()),
            place: "Cth",
            year: Some((group(&found, 2).to_string(), false)),
            act: Some(true),
        }));
    }
    let Some(found) = STATE_DOCUMENT.captures(url.as_str())? else {
        return Ok(None);
    };
    let register = group(&found, 1).to_lowercase();
    let remainder = url[span(&found).1 - 1..].to_lowercase();
    let document = remainder.split('#').next().unwrap_or("");
    // South Australia's register identifies its document with the path
    // parameter on /lz. Other query strings are not document identifiers.
    let path = if register == "sa" && document.starts_with("/lz?path=/c/a/") {
        document.split('&').next().unwrap_or("")
    } else {
        document.split('?').next().unwrap_or("")
    };
    let Some(id) = STATE_IDS
        .iter()
        .find_map(|pattern| pattern.find(path).ok().flatten())
    else {
        return Ok(None);
    };
    let place = match register.as_str() {
        "nsw" => "NSW",
        "qld" => "Qld",
        "vic" => "Vic",
        "sa" => "SA",
        "wa" => "WA",
        "tas" => "Tas",
        "act" => "ACT",
        _ => "NT",
    };
    let year = YEAR
        .find(id.as_str())?
        .map(|year| (year.as_str().to_string(), false));
    let act = if id.as_str().starts_with("sl-") {
        Some(false)
    } else if ["act-", "law_a", "/acts/", "/a/", "path=/c/a/"]
        .iter()
        .any(|prefix| id.as_str().starts_with(prefix))
    {
        Some(true)
    } else {
        None
    };
    Ok(Some(RegisterCopy {
        id: ("state", format!("{register} {}", id.as_str())),
        place,
        year,
        act,
    }))
}

/// The keys of the instrument `copy` holds, named by `title`, or `None` when
/// the copy's register or identifier names a different instrument.
fn copy_keys(copy: &RegisterCopy, title: &str) -> Option<BTreeSet<Key>> {
    let (words, year, place) = title_parts(title)?;
    if copy
        .act
        .is_some_and(|act| act != (words.last() == Some(&"Act")))
    {
        return None;
    }
    if let Some((copy_year, federal)) = &copy.year {
        let older = *federal && copy_year == "2004" && year < "2005";
        if copy_year != year && !older {
            return None;
        }
    }
    if !place.is_empty() && place != copy.place {
        return None;
    }
    Some(BTreeSet::from([
        (
            "title",
            format!("{} {year} ({})", words.join(" "), copy.place),
        ),
        copy.id.clone(),
    ]))
}

/// Every Act or other instrument named on `line`, in order. A Markdown link to
/// a legislation register document adds the document's identifier and
/// jurisdiction to the title its text starts with, unless the document is
/// another instrument; alone an address names nothing.
fn anchors(line: &str) -> Result<Vec<Anchor>> {
    let mut found: Vec<Anchor> = Vec::new();
    let explicit = captures(&TITLE_END, line)?;
    for name in captures(&ABBREVIATION, line)? {
        let (start, end) = span(&name);
        // A short name inside an explicit title, such as "Fair Work Act" in
        // "Fair Work Act 1994 (SA)", is part of that title.
        if explicit
            .iter()
            .any(|title| (start..end).contains(&span(title).0))
        {
            continue;
        }
        found.push(Anchor {
            start,
            end,
            keys: Some(BTreeSet::from([("title", full_title(group(&name, 1)))])),
        });
    }
    for title in explicit {
        let (kind_start, end) = span(&title);
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
    for standard in PROFESSIONAL_STANDARD.find_iter(line) {
        let standard = standard?;
        found.push(Anchor {
            start: standard.start(),
            end: standard.end(),
            keys: None,
        });
    }
    found.sort_by_key(|anchor| anchor.start);
    for link in LINK.find_iter(line) {
        let link = link?;
        let Some(text_end) = link.as_str().find("](") else {
            continue;
        };
        let Some(copy) = register_copy(&link.as_str()[text_end + 2..link.as_str().len() - 1])?
        else {
            continue;
        };
        let range = link.start()..link.start() + text_end;
        let first = found
            .iter_mut()
            .find(|anchor| range.contains(&anchor.start));
        if let Some(Anchor {
            keys: Some(keys), ..
        }) = first
            && let Some(copied) = copy_keys(&copy, &title(keys))
        {
            *keys = copied;
        }
    }
    Ok(found)
}

/// The title among an instrument's keys.
fn title(keys: &BTreeSet<Key>) -> String {
    keys.iter()
        .find(|(kind, _)| *kind == "title")
        .map_or_else(String::new, |(_, title)| title.clone())
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

/// Whether two sets of keys identify the same instrument. Titles must match:
/// the year agrees, a stated jurisdiction agrees, and the shorter title of at
/// least 2 words ends the longer, which tolerates a word a sentence or a
/// record title puts in front. Where both name a register copy of the same
/// kind, the copies must be the same document too.
fn same_instrument(cited: &BTreeSet<Key>, recorded: &BTreeSet<Key>) -> bool {
    let copies = |keys: &BTreeSet<Key>, kind: &str| -> BTreeSet<String> {
        keys.iter()
            .filter(|(other, _)| *other == kind)
            .map(|(_, id)| id.clone())
            .collect()
    };
    let documents_agree = ["register", "pac", "state"].iter().all(|kind| {
        let (one, other) = (copies(cited, kind), copies(recorded, kind));
        one.is_empty() || other.is_empty() || !one.is_disjoint(&other)
    });
    if !documents_agree {
        return false;
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
/// instrument of each record whose address is a legislation register document.
/// That instrument is the first one its title names, so a record of an
/// amending Act or of an instrument made under an Act does not own the Act's
/// sections, and a record whose register or identifier names another
/// instrument than its title owns none. A record from anywhere else, such as
/// an ATO web page or a ruling, may name an Act without holding its text, so it
/// owns no section either. A Federal Register record that contradicts a
/// section list's header (see `contradiction`) is returned apart, with why.
type Records = (
    BTreeSet<String>,
    Vec<BTreeSet<Key>>,
    Vec<(BTreeSet<Key>, String)>,
);

/// A named instrument whose Register addresses all agree on its identity.
fn record_instrument(source: &serde_json::Map<String, Value>) -> Result<Option<BTreeSet<Key>>> {
    let field = |name: &str| source.get(name).and_then(Value::as_str).unwrap_or("");
    let Some(named) = anchors(&unescape(field("title")))?
        .into_iter()
        .next()
        .and_then(|anchor| anchor.keys)
    else {
        return Ok(None);
    };
    let mut keys = BTreeSet::new();
    let mut agrees = true;
    for url in ["url", "final_url", "content_url"].map(field) {
        if let Some(copy) = register_copy(url)? {
            match copy_keys(&copy, &title(&named)) {
                Some(copied) if keys.is_empty() || same_instrument(&copied, &keys) => {
                    keys.extend(copied);
                }
                _ => agrees = false,
            }
        }
    }
    Ok((agrees && !keys.is_empty()).then_some(keys))
}

fn records(folder: &Path, indexes: &[SectionIndex]) -> Result<Records> {
    let index = folder.join("sources.json");
    let mut rulings = BTreeSet::new();
    let mut instruments = Vec::new();
    let mut rejected = Vec::new();
    if !index.is_file() {
        return Ok((rulings, instruments, rejected));
    }
    let payload =
        crate::validation::strict_json(&read_text(&index)?, &index.display().to_string())?;
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
        let Some(keys) = record_instrument(source)? else {
            continue;
        };
        let raw_title = source.get("title").and_then(Value::as_str).unwrap_or("");
        if let Some(reason) = contradiction(&keys, raw_title, indexes) {
            rejected.push((
                keys,
                format!("sources.json record {} {reason}", position + 1),
            ));
        } else {
            instruments.push(keys);
        }
    }
    Ok((rulings, instruments, rejected))
}

/// Why a record copied from the Federal Register contradicts a section list:
/// its register identifier has a list whose title is not the record's, or its
/// title is a list's but its identifier is not. The register identifier is
/// otherwise tied to the title only by kind and, for an Act, year, so this is
/// the only check that the address holds the instrument the title names.
fn contradiction(
    keys: &BTreeSet<Key>,
    raw_title: &str,
    indexes: &[SectionIndex],
) -> Option<String> {
    let only_titles = |keys: &BTreeSet<Key>| -> BTreeSet<Key> {
        keys.iter()
            .filter(|(kind, _)| *kind == "title")
            .cloned()
            .collect()
    };
    let ids: Vec<&str> = keys
        .iter()
        .filter(|(kind, _)| *kind == "register")
        .map(|(_, id)| id.as_str())
        .collect();
    if ids.is_empty() {
        return None;
    }
    indexes
        .iter()
        .find(|index| {
            same_instrument(&only_titles(keys), &only_titles(&index.keys))
                != ids.contains(&index.register_id.as_str())
        })
        .map(|index| {
            format!(
                "('{raw_title}' at {}) disagrees with the section list for {} ('{}')",
                ids.join(", "),
                index.register_id,
                index.title
            )
        })
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
    for boundary in SENTENCE_END.find_iter(text) {
        let boundary = boundary?;
        let end = boundary.end();
        if boundary.as_str().starts_with('.')
            && (ABBREVIATION_END.is_match(&text[..boundary.start() + 1])?
                || (text[..boundary.start()].ends_with("No")
                    && text[end..].starts_with(|character: char| character.is_ascii_digit())))
        {
            continue;
        }
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
    // insert, so it owns only a section named right beside it. It is known by
    // "Amendment" in its title or by the sentence saying it amends.
    // shortcut: an amending Act titled otherwise and not described so here,
    // such as "the Integrity Measures Act 2026 applies", still owns the
    // sentence's sections; recognising every one needs the register's metadata.
    let mut amending = Vec::new();
    for anchor in named {
        amending.push(
            anchor
                .keys
                .as_ref()
                .is_some_and(|keys| title(keys).contains(" Amendment "))
                || AMENDS.is_match(&sentence[anchor.end..])?
                || AMENDED_BY.is_match(&sentence[..anchor.start])?,
        );
    }
    let mut distinct: Vec<usize> = Vec::new();
    for index in (0..named.len()).filter(|&index| !tied[index] && !amending[index]) {
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
            if !amending[*first]
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
    let (indexes, mut exceptions) = section_indexes(root)?;
    for skill in discover_skills(root)? {
        let folder = root.join(".claude/skills").join(&skill);
        let (recorded_rulings, instruments, rejected) = records(&folder, &indexes)?;
        // None when no record names the Act; otherwise the section index, if
        // any, of the Act a matching record names. Matching the index through
        // the record keeps a state Act cited without its jurisdiction from
        // taking a Commonwealth Act's index.
        let recorded = |keys: &BTreeSet<Key>| {
            let matching: Vec<_> = instruments
                .iter()
                .filter(|other| same_instrument(keys, other))
                .collect();
            (!matching.is_empty()).then(|| {
                matching.iter().find_map(|record| {
                    indexes
                        .iter()
                        .find(|index| same_instrument(record, &index.keys))
                })
            })
        };
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
                    let title_ends = captures(&TITLE_END, sentence)?;
                    // "See section 3 below" points within the skill.
                    let mut sections = Vec::new();
                    for section in captures(&SECTION, sentence)? {
                        // A title such as "Superannuation Regulations 1994"
                        // names an instrument, not regulation 1994.
                        let (start, end) = span(&section);
                        if title_ends.iter().any(|title| {
                            let (title_start, title_end) = span(title);
                            start == title_start
                                && end <= title_end
                                && named
                                    .iter()
                                    .any(|anchor| anchor.start < start && anchor.end == title_end)
                        }) {
                            continue;
                        }
                        let rest = &sentence[span(&section).1..];
                        if !rest.starts_with(" below") && !rest.starts_with(" above") {
                            sections.push(section);
                        }
                    }
                    let owned = owners(sentence, &named, &sections)?;
                    for (section, owner) in sections.iter().zip(owned) {
                        let resolution = match owner.map(|index| &named[index].keys) {
                            Ok(None) => continue,
                            Ok(Some(keys)) => recorded(keys).ok_or_else(|| {
                                if let Some((_, reason)) = rejected
                                    .iter()
                                    .find(|(other, _)| same_instrument(keys, other))
                                {
                                    return reason.clone();
                                }
                                let names: Vec<_> =
                                    keys.iter().map(|(_, name)| name.as_str()).collect();
                                format!("no record names its Act ({})", names.join("; "))
                            }),
                            Err(reason) => Err(reason),
                        };
                        for number in section_numbers(section) {
                            report.sections += 1;
                            let citation = format!("{} {number}", group(section, 1));
                            let start = range.start + span(section).0;
                            let index = match &resolution {
                                Ok(index) => {
                                    report.sections_resolved += 1;
                                    index
                                }
                                Err(reason) => {
                                    missing.push((start, citation, reason.clone()));
                                    continue;
                                }
                            };
                            let Some(index) = index else {
                                report.sections_not_indexed += 1;
                                continue;
                            };
                            let base = number
                                .split_once('(')
                                .map_or(number.as_str(), |(base, _)| base);
                            // In an Act that numbers no section with a hyphen,
                            // "ss 17A-18C" is a range when both ends are listed.
                            let hyphen_range = !index.hyphenated
                                && base.split_once('-').is_some_and(|(first, last)| {
                                    index.sections.contains(first) && index.sections.contains(last)
                                });
                            if index.sections.contains(base) || hyphen_range {
                                report.sections_exist += 1;
                            } else if let Some(exception) =
                                exceptions.iter_mut().find(|exception| {
                                    exception.register_id == index.register_id
                                        && exception.section == base
                                })
                            {
                                exception.used = true;
                                report.sections_excepted += 1;
                            } else {
                                report.sections_absent += 1;
                                missing.push((
                                    start,
                                    citation,
                                    format!(
                                        "absent from the section index of {}, compilation {}",
                                        index.title, index.compilation
                                    ),
                                ));
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
    for exception in exceptions.iter().filter(|exception| !exception.used) {
        report.unmatched.push(Unmatched {
            file: format!("{SECTION_INDEX}/{EXCEPTIONS}"),
            line: exception.line,
            citation: format!("{} {}", exception.register_id, exception.section),
            reason: "no cited section absent from the index needs this exception".to_string(),
        });
    }
    Ok(report)
}

/// Render the report: one line per failure, then the totals.
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
    text.push_str(&format!(
        "{} of {} resolved sections checked against an index of their Act: \
         {} found, {} listed exceptions, {} absent; {} in an Act with no index.\n",
        report.sections_exist + report.sections_excepted + report.sections_absent,
        report.sections_resolved,
        report.sections_exist,
        report.sections_excepted,
        report.sections_absent,
        report.sections_not_indexed
    ));
    text
}

/// Runs the `check-citations` command. Exit 2 when any citation is unmatched,
/// any section is absent from its Act's index or any exception is unused.
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
