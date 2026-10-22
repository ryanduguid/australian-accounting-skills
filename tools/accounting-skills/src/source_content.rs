//! Readable-text interpretation, following Python 3.14 html.parser callbacks.
use crate::{Result, source_html_rules as rules, validation_text};
use fancy_regex::Regex;
use sha2::{Digest, Sha256};
use std::sync::LazyLock;
use unicode_normalization::UnicodeNormalization;

pub fn space(c: char) -> bool {
    c.is_whitespace() || matches!(c, '\u{1c}'..='\u{1f}')
}
pub fn decode(body: &[u8], charset: Option<&str>) -> Result<String> {
    let supplied = charset.filter(|name| !name.is_empty()).unwrap_or("utf-8");
    let mut normal = String::new();
    let mut punct = false;
    for c in supplied.to_lowercase().chars() {
        if c.is_alphanumeric() || c == '.' {
            if punct && !normal.is_empty() {
                normal.push('_');
            }
            if c.is_ascii() {
                normal.push(c);
            }
            punct = false;
        } else {
            punct = true;
        }
    }
    // shortcut: other Python codecs require exact native decoding tables before
    // this candidate can replace those reads. Refuse rather than change a digest.
    let name = crate::source_codec_rules::canonical(&normal).ok_or_else(|| format!("Unqualified source charset {supplied:?}; use the original Python reader for manual review."))?;
    Ok(match name {
        "utf-8-sig" => String::from_utf8_lossy(body.strip_prefix(&[239, 187, 191]).unwrap_or(body))
            .into_owned(),
        "utf-16" | "utf-16-le" | "utf-16-be" | "utf16" | "utf-32" | "utf-32-le" | "utf-32-be"
        | "utf32" => {
            let wide = name.contains("32");
            let mut little = !name.ends_with("be");
            let mut bytes = body;
            if name == "utf-16" || name == "utf16" {
                if body.starts_with(&[255, 254]) {
                    bytes = &body[2..];
                    little = true;
                } else if body.starts_with(&[254, 255]) {
                    bytes = &body[2..];
                    little = false;
                }
            }
            if name == "utf-32" || name == "utf32" {
                if body.starts_with(&[255, 254, 0, 0]) {
                    bytes = &body[4..];
                    little = true;
                } else if body.starts_with(&[0, 0, 254, 255]) {
                    bytes = &body[4..];
                    little = false;
                }
            }
            let width = if wide { 4 } else { 2 };
            let mut out = String::new();
            if wide {
                for &b in bytes.as_chunks::<4>().0 {
                    let n = if little {
                        u32::from_le_bytes(b)
                    } else {
                        u32::from_be_bytes(b)
                    };
                    out.push(char::from_u32(n).unwrap_or('�'));
                }
            } else {
                let units = bytes.as_chunks::<2>().0.iter().map(|b| {
                    if little {
                        u16::from_le_bytes([b[0], b[1]])
                    } else {
                        u16::from_be_bytes([b[0], b[1]])
                    }
                });
                out.extend(char::decode_utf16(units).map(|r| r.unwrap_or('�')));
            }
            let grouped_tail = !wide && bytes.len() >= 3 && {
                let i = bytes.len() / 2 * 2 - 2;
                let unit = if little {
                    u16::from_le_bytes([bytes[i], bytes[i + 1]])
                } else {
                    u16::from_be_bytes([bytes[i], bytes[i + 1]])
                };
                (0xd800..=0xdbff).contains(&unit)
            };
            if !bytes.len().is_multiple_of(width) && !grouped_tail {
                out.push('�');
            }
            out
        }
        "utf-8" => String::from_utf8_lossy(body).into_owned(),
        "ascii" => body
            .iter()
            .map(|&b| if b < 128 { b as char } else { '�' })
            .collect(),
        "iso8859-1" => body.iter().map(|&b| b as char).collect(),
        "cp1252" => body
            .iter()
            .map(|&b| char::from_u32(crate::source_codec_rules::CP1252[b as usize]).unwrap())
            .collect(),
        _ => unreachable!("canonical codec table and decoder disagree"),
    })
}
pub fn sha256(body: &[u8]) -> String {
    Sha256::digest(body)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn anchored<'a>(regex: &Regex, text: &'a str) -> Result<Option<fancy_regex::Captures<'a, str>>> {
    Ok(regex
        .captures(text)?
        .filter(|c| c.get(0).unwrap().start() == 0))
}

pub fn readable_text(body: &[u8], charset: Option<&str>) -> Result<String> {
    static TAG: LazyLock<Regex> = LazyLock::new(|| Regex::new(rules::TAGFIND_TOLERANT).unwrap());
    static ATTR: LazyLock<Regex> = LazyLock::new(|| Regex::new(rules::ATTRFIND_TOLERANT).unwrap());
    static END: LazyLock<Regex> = LazyLock::new(|| Regex::new(rules::LOCATETAGEND).unwrap());
    static COMMENT: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"--!?>").unwrap());
    let text = decode(body, charset)?;
    let (mut whole, mut main) = (String::new(), String::new());
    let main_seen = std::cell::Cell::new(false);
    let (mut skip, mut depth) = (0usize, 0usize);
    let (mut position, mut raw, mut escapable) = (0usize, None::<String>, true);
    let append = |value: &str,
                  escape: bool,
                  skip: usize,
                  depth: usize,
                  whole: &mut String,
                  main: &mut String|
     -> Result<()> {
        if skip == 0 {
            let decoded = if escape {
                validation_text::unescape_checked(value)?
            } else {
                value.to_owned()
            };
            whole.push_str(&decoded);
            if depth > 0 {
                if !value.is_empty() {
                    main_seen.set(true);
                }
                main.push_str(&decoded);
            }
        }
        Ok(())
    };
    while position < text.len() {
        let next = if let Some(ref tag) = raw {
            if tag == "plaintext" {
                None
            } else {
                let spelling: String = tag
                    .chars()
                    .map(|c| format!("[{c}{}]", c.to_ascii_uppercase()))
                    .collect();
                Regex::new(&format!(r"</{spelling}(?=[\t\n\r\x0c />])"))?
                    .find(&text[position..])?
                    .map(|m| position + m.start())
            }
        } else {
            text[position..].find('<').map(|i| position + i)
        };
        let Some(start) = next else {
            append(
                &text[position..],
                escapable,
                skip,
                depth,
                &mut whole,
                &mut main,
            )?;
            break;
        };
        append(
            &text[position..start],
            escapable,
            skip,
            depth,
            &mut whole,
            &mut main,
        )?;
        let tail = &text[start..];
        if let Some(content) = tail.strip_prefix("<!--") {
            let end = if content.starts_with('>') {
                Some(1)
            } else if content.starts_with("->") {
                Some(2)
            } else {
                COMMENT.find(content)?.map(|m| m.end())
            };
            position = match end {
                Some(i) => start + 4 + i,
                None => text.len(),
            };
            continue;
        }
        if let Some(content) = tail.strip_prefix("<![CDATA[") {
            position = content
                .find("]]>")
                .map(|i| start + 12 + i)
                .unwrap_or(text.len());
            continue;
        }
        if tail.starts_with("<!") || tail.starts_with("<?") {
            position = tail.find('>').map(|i| start + i + 1).unwrap_or(text.len());
            continue;
        }
        let closing = tail.starts_with("</");
        let offset = if closing { 2 } else { 1 };
        if !tail
            .as_bytes()
            .get(offset)
            .is_some_and(u8::is_ascii_alphabetic)
        {
            if closing {
                if tail == "</" {
                    append(tail, true, skip, depth, &mut whole, &mut main)?;
                    break;
                }
                position = tail.find('>').map(|i| start + i + 1).unwrap_or(text.len());
            } else {
                append("<", false, skip, depth, &mut whole, &mut main)?;
                position = start + 1;
            }
            continue;
        }
        let Some(end) = anchored(&END, &tail[offset..])? else {
            break;
        };
        let end = offset + end.get(0).unwrap().end();
        if !tail[..end].ends_with('>') {
            break;
        }
        let tag_match = anchored(&TAG, &tail[offset..])?.unwrap();
        let tag = tag_match[1].to_lowercase();
        let mut consumed = offset + tag_match.get(0).unwrap().end();
        if !closing {
            while consumed < end {
                // Keep the preceding character for the attribute regex lookbehind.
                let m = ATTR.captures_from_pos(tail, consumed)?;
                let Some(m) = m.filter(|m| m.get(0).unwrap().start() == consumed) else {
                    break;
                };
                if let Some(value) = m.get(3) {
                    // HTMLParser decodes attributes even though this collector ignores them.
                    validation_text::unescape_checked(value.as_str())?;
                }
                consumed = m.get(0).unwrap().end();
            }
            let ending = tail[consumed..end].trim_matches(space);
            if ending != ">" && ending != "/>" {
                append(&tail[..end], false, skip, depth, &mut whole, &mut main)?;
                position = start + end;
                continue;
            }
        }
        let skipped = ["script", "style", "noscript", "template", "svg"].contains(&tag.as_str());
        if closing {
            if skipped {
                skip = skip.saturating_sub(1);
            } else if tag == "main" {
                depth = depth.saturating_sub(1);
            }
            raw = None;
            escapable = true;
        } else {
            if skipped {
                skip += 1;
            } else if tag == "main" {
                depth += 1;
            }
            if tail[consumed..end].trim_matches(space) == "/>" {
                if skipped {
                    skip = skip.saturating_sub(1);
                } else if tag == "main" {
                    depth = depth.saturating_sub(1);
                }
            } else if [
                "script",
                "style",
                "xmp",
                "iframe",
                "noembed",
                "noframes",
                "plaintext",
                "textarea",
                "title",
            ]
            .contains(&tag.as_str())
            {
                escapable = ["textarea", "title"].contains(&tag.as_str());
                raw = Some(tag);
            }
        }
        position = start + end;
    }
    let chosen = if main_seen.get() { main } else { whole };
    let collapsed = chosen
        .split(space)
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join(" ");
    Ok(collapsed.nfc().collect())
}
pub fn body_digest(body: &[u8], kind: &str, charset: Option<&str>) -> Result<(String, String)> {
    if ["text/html", "application/xhtml+xml"].contains(&kind) {
        let text = readable_text(body, charset)?;
        Ok((
            if text.is_empty() {
                String::new()
            } else {
                sha256(text.as_bytes())
            },
            "html".to_owned(),
        ))
    } else {
        Ok((
            if body.is_empty() {
                String::new()
            } else {
                sha256(body)
            },
            "bytes".to_owned(),
        ))
    }
}
