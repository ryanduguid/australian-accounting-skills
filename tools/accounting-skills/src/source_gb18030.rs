//! Frozen CPython 3.14.8 GB18030 scalars, with its one-shot error consumption.
use crate::{Result, source_gb18030_rules::RANGES};

const PAIRS: &[u8; 126 * 256 * 4] = include_bytes!("source_gb18030.bin");

pub fn decode(mut body: &[u8], strict: bool) -> Result<String> {
    let mut output = String::new();
    while !body.is_empty() {
        if body[0] < 128 {
            output.push(body[0] as char);
            body = &body[1..];
            continue;
        }
        // CPython requests the complete sequence before inspecting its later
        // bytes. An incomplete digit-led tail becomes one replacement, even
        // when the first or third byte would be illegal in a complete input.
        let width = if body.get(1).is_some_and(u8::is_ascii_digit) {
            4
        } else {
            2
        };
        if body.len() < width {
            if strict {
                return Err("invalid encoded parameter".into());
            }
            output.push('\u{fffd}');
            break;
        }
        let mut scalar = None;
        if (0x81..=0xfe).contains(&body[0]) {
            if width == 2 {
                let offset = ((body[0] as usize - 0x81) * 256 + body[1] as usize) * 4;
                scalar = char::from_u32(u32::from_le_bytes(
                    PAIRS[offset..offset + 4].try_into().unwrap(),
                ));
            } else if (0x81..=0xfe).contains(&body[2]) && body[3].is_ascii_digit() {
                let index = (((body[0] as u32 - 0x81) * 10 + body[1] as u32 - 0x30) * 126
                    + body[2] as u32
                    - 0x81)
                    * 10
                    + body[3] as u32
                    - 0x30;
                let next = RANGES.partition_point(|&(start, _, _)| start <= index);
                if next != 0 {
                    let (start, end, base) = RANGES[next - 1];
                    if index <= end {
                        scalar = char::from_u32(base + index - start);
                    }
                }
            }
        }
        if let Some(value) = scalar {
            output.push(value);
            body = &body[width..];
        } else {
            if strict {
                return Err("invalid encoded parameter".into());
            }
            output.push('\u{fffd}');
            // Illegal complete sequences consume one byte and resume; their
            // remaining bytes can start valid ASCII or multibyte sequences.
            body = &body[1..];
        }
    }
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn ranges_are_ordered_and_contain_only_unicode_scalars() {
        for pair in RANGES.windows(2) {
            assert!(pair[0].1 < pair[1].0);
        }
        for &(start, end, base) in RANGES {
            assert!(start <= end);
            for scalar in base..=base + end - start {
                assert!(char::from_u32(scalar).is_some());
            }
        }
        for word in PAIRS.as_chunks::<4>().0 {
            let value = u32::from_le_bytes(*word);
            assert!(value == u32::MAX || char::from_u32(value).is_some());
        }
    }
    #[test]
    fn malformed_tails_and_valid_extensions_preserve_consumption() {
        for bytes in [&[0x80, b'0', b'A'][..], &[0x81, b'0'], &[0x81]] {
            assert_eq!(decode(bytes, false).unwrap(), "\u{fffd}");
            assert!(decode(bytes, true).is_err());
        }
        assert_eq!(
            decode(&[0x80, b'0', b'A', b'0'], false).unwrap(),
            "\u{fffd}0A0"
        );
        assert_eq!(decode(&[0x81, 0x30, 0x81, 0x30], true).unwrap(), "\u{80}");
        assert_eq!(
            decode(&[0x90, 0x30, 0x81, 0x30], true).unwrap(),
            "\u{10000}"
        );
        assert_eq!(decode(&[0xa2, 0xe3], true).unwrap(), "\u{20ac}");
        assert_eq!(decode(&[0xc4, 0xe3, 0xba, 0xc3], true).unwrap(), "你好");
    }
}
