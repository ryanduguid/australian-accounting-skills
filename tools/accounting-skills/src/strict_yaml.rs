//! The validation card schema uses YAML syntax with no aliases, anchors or tags.
use crate::Result;
use serde_json::{Map, Value};
use yaml_rust2::{
    parser::{Event, Parser},
    scanner::{Scanner, TScalarStyle, TokenType},
};

fn node(parser: &mut Parser<impl Iterator<Item = char>>, depth: usize) -> Result<Value> {
    if depth > 128 {
        return Err("front matter is nested too deeply to read".into());
    }
    let event = parser.next_token()?.0;
    match event {
        Event::Scalar(text, style, _, _) => {
            if style == TScalarStyle::Plain {
                match text.as_str() {
                    "true" | "True" | "TRUE" | "yes" | "Yes" | "YES" | "on" | "On" | "ON" => {
                        return Ok(Value::Bool(true));
                    }
                    "false" | "False" | "FALSE" | "no" | "No" | "NO" | "off" | "Off" | "OFF" => {
                        return Ok(Value::Bool(false));
                    }
                    "" | "~" | "null" | "Null" | "NULL" => return Ok(Value::Null),
                    _ => {}
                }
                // Non-string scalars cannot satisfy any string field in this schema.
                for pattern in crate::validation_data::YAML_NONSTRING {
                    if fancy_regex::Regex::new(pattern)?.is_match(&text)? {
                        return Ok(Value::Number(0.into()));
                    }
                }
            }
            Ok(Value::String(text))
        }
        Event::SequenceStart(_, _) => {
            let mut values = Vec::new();
            while !matches!(parser.peek()?.0, Event::SequenceEnd) {
                values.push(node(parser, depth + 1)?);
            }
            parser.next_token()?;
            Ok(Value::Array(values))
        }
        Event::MappingStart(_, _) => {
            let mut values = Map::new();
            while !matches!(parser.peek()?.0, Event::MappingEnd) {
                let key = node(parser, depth + 1)?;
                if key.is_array() || key.is_object() {
                    return Err("YAML mapping keys must be scalar".into());
                }
                let key = key
                    .as_str()
                    .map(str::to_owned)
                    .unwrap_or_else(|| key.to_string());
                if values.contains_key(&key) {
                    return Err(
                        format!("duplicate YAML field: {}", super::validation::repr(&key)).into(),
                    );
                }
                values.insert(key, node(parser, depth + 1)?);
            }
            parser.next_token()?;
            Ok(Value::Object(values))
        }
        _ => Err("front matter must be valid YAML: unexpected document event".into()),
    }
}

pub fn card_mapping(raw: &str) -> Result<Value> {
    let mut scanner = Scanner::new(raw.chars());
    for token in scanner.by_ref() {
        if matches!(
            token.1,
            TokenType::Alias(_) | TokenType::Anchor(_) | TokenType::Tag(_, _)
        ) {
            return Err("YAML aliases, anchors and tags are not permitted".into());
        }
    }
    if let Some(error) = scanner.get_error() {
        return Err(format!("front matter must be valid YAML: {error}").into());
    }
    let mut parser = Parser::new_from_str(raw);
    if !matches!(parser.next_token()?.0, Event::StreamStart) {
        return Err("front matter must be valid YAML".into());
    }
    if matches!(parser.peek()?.0, Event::StreamEnd) {
        return Ok(Value::Null);
    }
    parser.next_token()?; // DocumentStart
    let value = node(&mut parser, 0)?;
    if !matches!(parser.next_token()?.0, Event::DocumentEnd)
        || !matches!(parser.next_token()?.0, Event::StreamEnd)
    {
        return Err("front matter must be valid YAML: expected one document".into());
    }
    Ok(value)
}
