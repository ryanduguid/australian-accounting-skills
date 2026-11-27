// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

use crate::{Result, validation_data as data};
use fancy_regex::{Captures, Regex};
use std::{fs, path::Path, sync::LazyLock};
use unicode_normalization::UnicodeNormalization;

/// The code points Python 3.15's `\w` (Unicode 17.0) matches that the regex
/// crate's Unicode 16.0 `[\p{L}\p{N}_]` lacks: 4,657 in all. They include
/// every code point the 2 versions read differently: U+A7F1, the only NFKC
/// change, and the Tolong Siki digits U+11DE0 to U+11DE9.
const UNICODE_17_WORD: &[(u32, u32)] = &[
    (0x088F, 0x088F),
    (0x0C5C, 0x0C5C),
    (0x0CDC, 0x0CDC),
    (0xA7CE, 0xA7CF),
    (0xA7D2, 0xA7D2),
    (0xA7D4, 0xA7D4),
    (0xA7F1, 0xA7F1),
    (0x10940, 0x10959),
    (0x10EC5, 0x10EC7),
    (0x11DB0, 0x11DDB),
    (0x11DE0, 0x11DE9),
    (0x16EA0, 0x16EB8),
    (0x16EBB, 0x16ED3),
    (0x16FF2, 0x16FF6),
    (0x187F8, 0x187FF),
    (0x18D09, 0x18D1E),
    (0x18D80, 0x18DF2),
    (0x1E6C0, 0x1E6DE),
    (0x1E6E0, 0x1E6E2),
    (0x1E6E4, 0x1E6E5),
    (0x1E6E7, 0x1E6ED),
    (0x1E6F0, 0x1E6F4),
    (0x1E6FE, 0x1E6FF),
    (0x2B73A, 0x2B73F),
    (0x2CEA2, 0x2CEAD),
    (0x323B0, 0x33479),
];

/// Translates a Python pattern as Python 3.14 (Unicode 16.0) reads it, or as
/// Python 3.15 (Unicode 17.0) does when `unicode_17` is set.
pub fn pattern(text: &str, unicode_17: bool) -> Regex {
    let (extra_word, digit) = if unicode_17 {
        // Python 3.15's `\d` also matches the Tolong Siki digits. No pattern
        // puts `\d` inside a bracket class, so the plain swap is safe.
        let ranges = UNICODE_17_WORD.iter();
        let extra = ranges.map(|(a, b)| format!(r"\x{{{a:X}}}-\x{{{b:X}}}"));
        (extra.collect(), "[\\d\u{11DE0}-\u{11DE9}]")
    } else {
        (String::new(), r"\d")
    };
    let word = format!(r"[\p{{L}}\p{{N}}_{extra_word}]");
    let boundary = format!(r"(?:(?<={word})(?!{word})|(?<!{word})(?={word}))");
    let mut text = text
        .replace(r"\b", &boundary)
        .replace(r"\s", r"[\s\x1c-\x1f]")
        .replace(r"\d", digit);
    if text.starts_with("(?i)") {
        text = text.replace("[A-Z", "[A-Zİı").replace("[a-z", "[a-zİı");
    }
    Regex::new(&text).expect("retained validator regex")
}

fn within(c: char, ranges: &[(u32, u32)]) -> bool {
    let point = c as u32;
    let index = ranges.partition_point(|&(_, end)| end < point);
    ranges.get(index).is_some_and(|&(start, _)| start <= point)
}

pub fn read_utf8(path: &Path) -> Result<String> {
    let bytes = fs::read(path).map_err(|e| format!("cannot read {}: {e}", path.display()))?;
    let text = String::from_utf8(bytes)
        .map_err(|e| format!("{} is not strict UTF-8: {e}", path.display()))?;
    if text.contains('\0') {
        return Err(format!("{} contains a NUL byte", path.display()).into());
    }
    let text = text.replace("\r\n", "\n");
    if text.contains('\r') {
        return Err(format!("{} contains a bare carriage return", path.display()).into());
    }
    if let Some(c) = text
        .chars()
        .find(|&c| c != '\n' && c != '\t' && within(c, data::CONTROLS))
    {
        return Err(format!(
            "{} contains a Unicode control/format character U+{:04X}",
            path.display(),
            c as u32
        )
        .into());
    }
    Ok(text)
}

pub fn unescape(text: &str) -> String {
    static ENTITY: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(r"&(#(?:[0-9]+|[xX][0-9a-fA-F]+);?|[^\t\n\x0c <&#;]{1,32};?)").unwrap()
    });
    ENTITY
        .replace_all(text, |cap: &Captures<'_, str>| {
            let name = &cap[1];
            if let Some(number) = name.strip_prefix('#') {
                let number = number.trim_end_matches(';');
                let value = if let Some(hex) = number
                    .strip_prefix('x')
                    .or_else(|| number.strip_prefix('X'))
                {
                    u32::from_str_radix(hex, 16)
                } else {
                    number.parse()
                }
                .unwrap_or(0x110000);
                if let Ok(index) =
                    data::NUMERIC_ENTITIES.binary_search_by_key(&value, |item| item.0)
                {
                    return data::NUMERIC_ENTITIES[index].1.to_owned();
                }
                if value > 0x10ffff || (0xd800..=0xdfff).contains(&value) {
                    return "�".to_owned();
                }
                if (0xfdd0..=0xfdef).contains(&value) || value & 0xffff >= 0xfffe {
                    return String::new();
                }
                return char::from_u32(value).unwrap().to_string();
            }
            for end in name
                .char_indices()
                .map(|(index, _)| index)
                .chain([name.len()])
                .rev()
            {
                if end == 0 {
                    continue;
                }
                if let Ok(index) = data::ENTITIES.binary_search_by(|item| item.0.cmp(&name[..end]))
                {
                    return format!("{}{}", data::ENTITIES[index].1, &name[end..]);
                }
            }
            cap[0].to_owned()
        })
        .into_owned()
}

pub fn unescape_checked(text: &str) -> Result<String> {
    static DECIMAL: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"&#([0-9]+)").unwrap());
    for reference in DECIMAL.captures_iter(text) {
        if reference?[1].len() > 4300 {
            return Err("decimal HTML entity exceeds Python's 4,300-digit conversion limit".into());
        }
    }
    Ok(unescape(text))
}

pub fn normalise(text: &str) -> Result<String> {
    normalise_as(text, true)
}

/// NFKC as Python 3.15 applies it, or as Python 3.14 does: Unicode 16.0 has
/// no U+A7F1, so it stays put and nothing composes across it.
fn nfkc(text: &str, unicode_17: bool) -> String {
    if unicode_17 {
        return text.nfkc().collect();
    }
    text.split('\u{A7F1}')
        .map(|part| part.nfkc().collect::<String>())
        .collect::<Vec<_>>()
        .join("\u{A7F1}")
}

fn normalise_as(text: &str, unicode_17: bool) -> Result<String> {
    static MARKUP: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"(?s)<!--.*?-->|<[^>]*>").unwrap());
    static INLINE: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"!?\[([^\]\r\n]*)\]\((?:<[^>\r\n]+>|[^)\r\n]+)\)").unwrap());
    static REFERENCE: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"!?\[([^\]\r\n]*)\]\[[^\]\r\n]*\]").unwrap());
    let decoded: String = nfkc(&unescape_checked(text)?, unicode_17)
        .chars()
        .filter(|&c| !within(c, data::FORMATS))
        .collect();
    let visible = MARKUP.replace_all(&decoded, "");
    let visible = INLINE.replace_all(&visible, "$1");
    let visible = REFERENCE.replace_all(&visible, "$1");
    let strip = |text: &str, underscore: bool| {
        text.chars()
            .filter(|c| !"\\`*~[]()".contains(*c) && (!underscore || *c != '_'))
            .collect::<String>()
    };
    Ok([
        decoded.clone(),
        strip(&decoded, false),
        strip(&decoded, true),
        strip(&visible, false),
        strip(&visible, true),
    ]
    .join("\n::scan-variant-boundary::\n"))
}

/// Refuses what Python 3.14 or Python 3.15 refuses: their Unicode tables
/// differ, and neither one's verdicts contain the other's.
pub fn sensitive(text: &str, waived: &[String]) -> Result<()> {
    type Both = [Regex; 2];
    fn both(text: &str) -> Both {
        [pattern(text, false), pattern(text, true)]
    }
    static RULES: LazyLock<Vec<(&str, Both)>> = LazyLock::new(|| {
        data::SENSITIVE
            .iter()
            .map(|&(label, text)| (label, both(text)))
            .collect()
    });
    static DATED: LazyLock<Both> = LazyLock::new(|| both(data::DATED_RULE));
    let old = normalise_as(text, false)?;
    let new = normalise_as(text, true)?;
    // Without a code point the 2 versions read differently, both passes agree,
    // so the Unicode 16.0 pass runs only when one is present.
    let differs = old.chars().any(|c| within(c, UNICODE_17_WORD));
    let matches = |regexes: &Both| -> Result<bool> {
        Ok(regexes[1].is_match(&new)? || (differs && regexes[0].is_match(&old)?))
    };
    for (label, regexes) in RULES.iter() {
        if !waived.iter().any(|item| item == label) && matches(regexes)? {
            return Err(format!("possible {label}").into());
        }
    }
    if matches(&DATED)? {
        return Err("embeds a dated/rate rule instead of a live-source check".into());
    }
    Ok(())
}
