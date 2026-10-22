use crate::{Result, validation_data as data};
use fancy_regex::{Captures, Regex};
use std::{fs, path::Path, sync::LazyLock};
use unicode_normalization::UnicodeNormalization;

pub fn pattern(text: &str) -> Regex {
    let word = r"[\p{L}\p{N}_]";
    let boundary = format!(r"(?:(?<={word})(?!{word})|(?<!{word})(?={word}))");
    let mut text = text
        .replace(r"\b", &boundary)
        .replace(r"\s", r"[\s\x1c-\x1f]");
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
    static MARKUP: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"(?s)<!--.*?-->|<[^>]*>").unwrap());
    static INLINE: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"!?\[([^\]\r\n]*)\]\((?:<[^>\r\n]+>|[^)\r\n]+)\)").unwrap());
    static REFERENCE: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"!?\[([^\]\r\n]*)\]\[[^\]\r\n]*\]").unwrap());
    let decoded: String = unescape_checked(text)?
        .nfkc()
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

pub fn sensitive(text: &str, waived: &[String]) -> Result<()> {
    static RULES: LazyLock<Vec<(&str, Regex)>> = LazyLock::new(|| {
        data::SENSITIVE
            .iter()
            .map(|&(label, text)| (label, pattern(text)))
            .collect()
    });
    static DATED: LazyLock<Regex> = LazyLock::new(|| pattern(data::DATED_RULE));
    let text = normalise(text)?;
    for (label, regex) in RULES.iter() {
        if !waived.iter().any(|item| item == label) && regex.is_match(&text)? {
            return Err(format!("possible {label}").into());
        }
    }
    if DATED.is_match(&text)? {
        return Err("embeds a dated/rate rule instead of a live-source check".into());
    }
    Ok(())
}
