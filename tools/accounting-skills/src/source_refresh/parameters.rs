//! Content-Type parameter rules from CPython 3.14.8 email.message/utils.
use crate::{Result, source_codec_rules, source_content as content};

fn unquote(value: &str) -> String {
    if value.len() > 1 && value.starts_with('"') && value.ends_with('"') {
        value[1..value.len() - 1]
            .replace("\\\\", "\\")
            .replace("\\\"", "\"")
    } else if value.len() > 1 && value.starts_with('<') && value.ends_with('>') {
        value[1..value.len() - 1].to_owned()
    } else {
        value.to_owned()
    }
}
fn quote(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}
fn percent_decode(value: &str) -> String {
    let mut chars = value.chars().peekable();
    let mut output = String::new();
    while let Some(ch) = chars.next() {
        if ch == '%' {
            let mut following = chars.clone();
            if let Some(a) = following.next().filter(char::is_ascii)
                && let Some(b) = following.next().filter(char::is_ascii)
                && let Some(a) = a.to_digit(16)
                && let Some(b) = b.to_digit(16)
            {
                output.push(char::from((a * 16 + b) as u8));
                chars = following;
                continue;
            }
        }
        output.push(ch);
    }
    output
}
fn parts(value: &str) -> Vec<&str> {
    let mut result = Vec::new();
    let mut start = 0;
    let mut quoted = false;
    let mut previous = '\0';
    for (index, ch) in value.char_indices() {
        if ch == '"' && previous != '\\' {
            quoted = !quoted;
        }
        if ch == ';' && !quoted {
            result.push(&value[start..index]);
            start = index + 1;
        }
        previous = ch;
    }
    result.push(&value[start..]);
    result
}
struct Fragment {
    number: Option<String>,
    value: String,
    encoded: bool,
}
fn continuation(key: &str) -> Result<Option<(&str, Option<String>)>> {
    let Some((name, tail)) = key.split_once('*') else {
        return Ok(None);
    };
    if name.is_empty() || !name.chars().all(|c| c == '_' || c.is_ascii_alphanumeric()) {
        return Ok(None);
    }
    if tail.is_empty() {
        return Ok(Some((name, None)));
    }
    let number = tail.strip_suffix('*').unwrap_or(tail);
    if number.is_empty() || !number.bytes().all(|c| c.is_ascii_digit()) {
        return Ok(None);
    }
    if number.len() > 4300 {
        return Err(format!("Exceeds the limit (4300 digits) for integer string conversion: value has {} digits; use sys.set_int_max_str_digits() to increase the limit", number.len()).into());
    }
    let trimmed = number.trim_start_matches('0');
    Ok(Some((
        name,
        Some(if trimmed.is_empty() { "0" } else { trimmed }.into()),
    )))
}
fn ascii_charset(value: String) -> Option<String> {
    value.is_ascii().then(|| value.to_ascii_lowercase())
}
fn extended_charset(value: &str) -> Result<Option<String>> {
    // decode_params quotes the concatenation before splitting charset/language;
    // get_param then unquotes the value, but not the two prefix fields.
    let quoted = quote(value);
    let split: Vec<_> = quoted.splitn(3, '\'').collect();
    let (encoding, raw) = if split.len() == 3 {
        (split[0], unquote(&format!("\"{}\"", split[2])))
    } else {
        ("", unquote(&format!("\"{quoted}\"")))
    };
    let encoding = if encoding.is_empty() {
        "us-ascii"
    } else {
        encoding
    };
    if encoding.contains('\0') {
        return Err("embedded null character".into());
    }
    let Some(name) = content::codec_name(encoding) else {
        return Ok(ascii_charset(raw));
    };
    if !source_codec_rules::is_text(name) {
        return Ok(ascii_charset(raw));
    }
    let mut bytes = Vec::new();
    for ch in raw.chars() {
        if ch as u32 <= 255 {
            bytes.push(ch as u8);
        } else if ch as u32 <= 65535 {
            bytes.extend_from_slice(format!("\\u{:04x}", ch as u32).as_bytes());
        } else {
            bytes.extend_from_slice(format!("\\U{:08x}", ch as u32).as_bytes());
        }
    }
    match content::decode_strict(&bytes, encoding) {
        Ok(value) => Ok(ascii_charset(value)),
        Err(error) if error.to_string().starts_with("Unqualified source charset ") => Err(error),
        Err(_) => Ok(ascii_charset(raw)),
    }
}

pub fn content_type(value: Option<&str>) -> Result<(String, Option<String>)> {
    let Some(value) = value else {
        return Ok(("text/plain".into(), None));
    };
    let kind = value
        .split(';')
        .next()
        .unwrap()
        .trim_matches(content::space)
        .to_lowercase();
    let kind = if kind.matches('/').count() == 1 {
        kind
    } else {
        "text/plain".into()
    };
    let mut ordinary = Vec::new();
    let mut groups: Vec<(String, Vec<Fragment>)> = Vec::new();
    for (index, part) in parts(value).into_iter().enumerate() {
        let (key, raw) = if let Some((key, raw)) = part.split_once('=') {
            (
                key.trim_matches(content::space).to_lowercase(),
                raw.trim_matches(content::space),
            )
        } else {
            (part.trim_matches(content::space).to_owned(), "")
        };
        let continued = if index == 0 {
            None
        } else {
            continuation(&key)?
        };
        if let Some((name, number)) = continued {
            if name.to_lowercase() != "charset" {
                continue;
            }
            let position = groups
                .iter()
                .position(|(key, _)| key == name)
                .unwrap_or_else(|| {
                    groups.push((name.to_owned(), Vec::new()));
                    groups.len() - 1
                });
            groups[position].1.push(Fragment {
                number,
                value: unquote(raw),
                encoded: key.ends_with('*'),
            });
        } else {
            ordinary.push((key, unquote(raw)));
        }
    }
    // decode_params appends every continuation group after ordinary parameters,
    // regardless of the positions they occupied in the original header.
    if let Some((_, value)) = ordinary
        .into_iter()
        .find(|(key, _)| key.to_lowercase() == "charset")
    {
        return Ok((kind, ascii_charset(value)));
    }
    if let Some((_, mut fragments)) = groups.into_iter().next() {
        let has_zero = fragments
            .iter()
            .any(|part| part.number.as_deref() == Some("0"));
        if has_zero {
            fragments.retain(|part| part.number.is_some());
        }
        fragments.sort_by(|a, b| {
            let a = a.number.as_deref().unwrap_or("0");
            let b = b.number.as_deref().unwrap_or("0");
            a.len().cmp(&b.len()).then_with(|| a.cmp(b))
        });
        let extended = fragments.iter().any(|part| part.encoded);
        let value: String = fragments
            .into_iter()
            .map(|part| {
                if part.encoded {
                    percent_decode(&part.value)
                } else {
                    part.value
                }
            })
            .collect();
        let charset = if extended {
            extended_charset(&value)?
        } else {
            ascii_charset(value)
        };
        return Ok((kind, charset));
    }
    Ok((kind, None))
}
