//! Frozen CPython 3.14.8 finite multibyte decoder transducers.
use crate::{Result, source_multibyte_rules as rules};

const DATA: &[u8; rules::LENGTH] = include_bytes!("source_multibyte.bin");
fn word(offset: usize) -> u32 {
    u32::from_le_bytes(DATA[offset..offset + 4].try_into().unwrap())
}
fn output(index: usize) -> &'static str {
    let start = word(rules::OUTPUT_OFFSETS + index * 4) as usize;
    let end = word(rules::OUTPUT_OFFSETS + (index + 1) * 4) as usize;
    std::str::from_utf8(&DATA[rules::OUTPUT_BYTES + start..rules::OUTPUT_BYTES + end])
        .expect("frozen decoder outputs are UTF-8")
}
pub fn decode(body: &[u8], name: &str, strict: bool) -> Option<Result<String>> {
    let (offset, _) = rules::table(name)?;
    Some((|| {
        let mut state = 0;
        let mut result = String::new();
        for byte in body.iter().map(|&b| b as usize).chain([256]) {
            let transition = word(offset + (state * 257 + byte) * 4);
            if strict && transition & 1 != 0 {
                return Err("invalid encoded parameter".into());
            }
            result.push_str(output((transition >> 10) as usize));
            state = ((transition >> 1) & 511) as usize;
        }
        Ok(result)
    })())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn frozen_edges_stay_in_their_state_and_string_tables() {
        assert_eq!(&DATA[..8], b"ASMC\x01\0\0\0");
        for name in [
            "big5",
            "big5hkscs",
            "cp932",
            "cp949",
            "cp950",
            "euc_jis_2004",
            "euc_jisx0213",
            "euc_jp",
            "gb2312",
            "gbk",
            "hz",
            "johab",
            "shift_jis",
            "shift_jis_2004",
            "shift_jisx0213",
        ] {
            let (offset, states) = rules::table(name).unwrap();
            assert!(offset + states * 257 * 4 <= rules::OUTPUT_OFFSETS);
            for index in 0..states * 257 {
                let transition = word(offset + index * 4);
                assert!(((transition >> 1) & 511) < states as u32);
                let index = (transition >> 10) as usize;
                assert!(rules::OUTPUT_OFFSETS + (index + 2) * 4 <= rules::OUTPUT_BYTES);
                output(index);
            }
        }
    }
    #[test]
    fn strict_decoding_distinguishes_invalid_bytes_from_replacement() {
        for name in ["big5", "shift_jis", "hz"] {
            let body: &[u8] = if name == "hz" { b"~" } else { &[0x81] };
            assert_eq!(decode(body, name, false).unwrap().unwrap(), "\u{fffd}");
            assert!(decode(body, name, true).unwrap().is_err());
        }
        assert_eq!(decode(b"~~", "hz", true).unwrap().unwrap(), "~");
        assert_eq!(
            decode(&[0x88, 0x62], "big5hkscs", true).unwrap().unwrap(),
            "\u{ca}\u{304}"
        );
        assert_eq!(
            crate::source_content::decode(&[0x81], Some("cp1252")).unwrap(),
            "\u{fffd}"
        );
        assert!(crate::source_content::decode_strict(&[0x81], "cp1252").is_err());
        assert_eq!(
            crate::source_content::decode_strict(&[0x80], "cp1252").unwrap(),
            "\u{20ac}"
        );
        assert!(decode(b"a", "gb18030", false).is_none());
    }
}
