// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Pure-Rust deterministic stored-mode ZIP writer and reader with CRC-32
//! verification, used for OOXML `.xlsx` and `.docx` packages with zero
//! external compression dependencies.

use std::collections::BTreeMap;

const DOS_TIME: u16 = 0;
const DOS_DATE: u16 = (1 << 5) | 1;
const VERSION: u16 = 20;
const UTF8: u16 = 1 << 11;
const LOCAL_SIG: u32 = 0x0403_4b50;
const CENTRAL_SIG: u32 = 0x0201_4b50;
const EOCD_SIG: u32 = 0x0605_4b50;

pub fn crc32(bytes: &[u8]) -> u32 {
    let mut crc = u32::MAX;
    for byte in bytes {
        crc ^= u32::from(*byte);
        for _ in 0..8 {
            crc = if crc & 1 == 1 {
                (crc >> 1) ^ 0xEDB8_8320
            } else {
                crc >> 1
            };
        }
    }
    !crc
}

fn narrow_u32(value: usize) -> Result<u32, String> {
    u32::try_from(value).map_err(|_| "ZIP archive exceeds 4 GiB limit".to_owned())
}

fn append_entry(
    archive: &mut Vec<u8>,
    directory: &mut Vec<u8>,
    name: &str,
    bytes: &[u8],
) -> Result<(), String> {
    if name.contains('\\') || name.split('/').any(|p| matches!(p, "" | "." | "..")) {
        return Err(format!("invalid ZIP entry path: {name}"));
    }
    let offset = narrow_u32(archive.len())?;
    let size = narrow_u32(bytes.len())?;
    let name_len = u16::try_from(name.len()).map_err(|_| "ZIP entry name exceeds 65,535 bytes")?;
    let crc = crc32(bytes);

    let mut common = Vec::with_capacity(24);
    for field in [VERSION, UTF8, 0u16, DOS_TIME, DOS_DATE] {
        common.extend(field.to_le_bytes());
    }
    for field in [crc, size, size] {
        common.extend(field.to_le_bytes());
    }
    common.extend(name_len.to_le_bytes());
    common.extend(0u16.to_le_bytes());

    archive.extend(LOCAL_SIG.to_le_bytes());
    archive.extend(&common);
    archive.extend(name.as_bytes());
    archive.extend(bytes);

    directory.extend(CENTRAL_SIG.to_le_bytes());
    directory.extend(VERSION.to_le_bytes());
    directory.extend(&common);
    for field in [0u16, 0, 0] {
        directory.extend(field.to_le_bytes());
    }
    directory.extend(0u32.to_le_bytes());
    directory.extend(offset.to_le_bytes());
    directory.extend(name.as_bytes());
    Ok(())
}

pub fn write_zip(entries: &BTreeMap<String, Vec<u8>>) -> Result<Vec<u8>, String> {
    let mut archive = Vec::new();
    let mut directory = Vec::new();
    for (name, bytes) in entries {
        append_entry(&mut archive, &mut directory, name, bytes)?;
    }
    let count =
        u16::try_from(entries.len()).map_err(|_| "ZIP exceeds 65,535 entries".to_owned())?;
    let cd_offset = narrow_u32(archive.len())?;
    let cd_size = narrow_u32(directory.len())?;
    archive.extend(directory);
    archive.extend(EOCD_SIG.to_le_bytes());
    for field in [0u16, 0, count, count] {
        archive.extend(field.to_le_bytes());
    }
    archive.extend(cd_size.to_le_bytes());
    archive.extend(cd_offset.to_le_bytes());
    archive.extend(0u16.to_le_bytes());
    Ok(archive)
}

fn read_u16(bytes: &[u8], offset: usize) -> Result<u16, String> {
    let slice = bytes
        .get(offset..offset + 2)
        .ok_or_else(|| "unexpected end of ZIP archive".to_owned())?;
    Ok(u16::from_le_bytes([slice[0], slice[1]]))
}

fn read_u32(bytes: &[u8], offset: usize) -> Result<u32, String> {
    let slice = bytes
        .get(offset..offset + 4)
        .ok_or_else(|| "unexpected end of ZIP archive".to_owned())?;
    Ok(u32::from_le_bytes([slice[0], slice[1], slice[2], slice[3]]))
}

fn read_local_payload(
    bytes: &[u8],
    name: &str,
    local_offset: usize,
    comp_size: usize,
    expected_crc: u32,
) -> Result<Vec<u8>, String> {
    if read_u32(bytes, local_offset)? != LOCAL_SIG {
        return Err(format!("invalid local header for ZIP entry {name}"));
    }
    let local_name_len = usize::from(read_u16(bytes, local_offset + 26)?);
    let local_extra_len = usize::from(read_u16(bytes, local_offset + 28)?);
    let data_start = local_offset
        .checked_add(30)
        .and_then(|v| v.checked_add(local_name_len))
        .and_then(|v| v.checked_add(local_extra_len))
        .ok_or_else(|| "ZIP local header offset overflow".to_owned())?;
    let data_end = data_start
        .checked_add(comp_size)
        .ok_or_else(|| "ZIP entry size overflow".to_owned())?;
    let payload = bytes
        .get(data_start..data_end)
        .ok_or_else(|| format!("truncated payload for ZIP entry {name}"))?
        .to_vec();
    if crc32(&payload) != expected_crc {
        return Err(format!("CRC-32 mismatch for ZIP entry {name}"));
    }
    Ok(payload)
}

fn parse_central_entry(bytes: &[u8], cursor: usize) -> Result<(String, Vec<u8>, usize), String> {
    if read_u32(bytes, cursor)? != CENTRAL_SIG {
        return Err("invalid ZIP central directory signature".to_owned());
    }
    let method = read_u16(bytes, cursor + 10)?;
    if method != 0 {
        return Err(format!(
            "unsupported ZIP compression method {method} (only stored entries are supported)"
        ));
    }
    let expected_crc = read_u32(bytes, cursor + 16)?;
    let comp_size = usize::try_from(read_u32(bytes, cursor + 20)?).unwrap_or(usize::MAX);
    let uncomp_size = usize::try_from(read_u32(bytes, cursor + 24)?).unwrap_or(usize::MAX);
    if comp_size != uncomp_size {
        return Err("stored ZIP entry has mismatched sizes".to_owned());
    }
    let name_len = usize::from(read_u16(bytes, cursor + 28)?);
    let extra_len = usize::from(read_u16(bytes, cursor + 30)?);
    let comment_len = usize::from(read_u16(bytes, cursor + 32)?);
    let local_offset = usize::try_from(read_u32(bytes, cursor + 42)?).unwrap_or(usize::MAX);

    let name_start = cursor + 46;
    let name_bytes = bytes
        .get(name_start..name_start + name_len)
        .ok_or_else(|| "truncated ZIP entry name".to_owned())?;
    let name = std::str::from_utf8(name_bytes)
        .map_err(|_| "ZIP entry name is not valid UTF-8".to_owned())?
        .to_owned();
    if name.contains('\\') || name.split('/').any(|p| matches!(p, "." | "..")) {
        return Err(format!("unsafe ZIP entry path: {name}"));
    }
    let payload = read_local_payload(bytes, &name, local_offset, comp_size, expected_crc)?;
    Ok((
        name,
        payload,
        name_start + name_len + extra_len + comment_len,
    ))
}

/// Read stored entries from a ZIP archive and validate every CRC-32 checksum.
pub fn read_zip(bytes: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, String> {
    if bytes.len() < 22 {
        return Err("ZIP archive is too short".to_owned());
    }
    let search_start = bytes.len().saturating_sub(65_557);
    let eocd_pos = (search_start..=bytes.len() - 22)
        .rev()
        .find(|&pos| read_u32(bytes, pos).ok() == Some(EOCD_SIG))
        .ok_or_else(|| "missing ZIP end-of-central-directory record".to_owned())?;

    let entry_count = usize::from(read_u16(bytes, eocd_pos + 10)?);
    let cd_size = usize::try_from(read_u32(bytes, eocd_pos + 12)?).unwrap_or(usize::MAX);
    let cd_offset = usize::try_from(read_u32(bytes, eocd_pos + 16)?).unwrap_or(usize::MAX);
    let cd_end = cd_offset
        .checked_add(cd_size)
        .ok_or_else(|| "ZIP central directory offset overflow".to_owned())?;
    if cd_end > eocd_pos {
        return Err("ZIP central directory extends past EOCD".to_owned());
    }

    let mut entries = BTreeMap::new();
    let mut cursor = cd_offset;
    for _ in 0..entry_count {
        let (name, payload, next_cursor) = parse_central_entry(bytes, cursor)?;
        if entries.insert(name.clone(), payload).is_some() {
            return Err(format!("duplicate ZIP entry: {name}"));
        }
        cursor = next_cursor;
    }
    Ok(entries)
}
