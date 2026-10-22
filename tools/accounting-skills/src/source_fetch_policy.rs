//! Reviewed retrieval policy from scripts/source_fetch_policy.py.
//! HTTP redirect orchestration and transport remain the caller's responsibility.
use crate::Result;
use std::{
    io::Read,
    net::{IpAddr, Ipv6Addr, ToSocketAddrs},
};
use unicode_normalization::UnicodeNormalization;

pub const MAX_RESPONSE_BYTES: usize = 8 * 1024 * 1024;
pub const READ_CHUNK_BYTES: usize = 64 * 1024;
pub const MAX_REDIRECTS: usize = 3;
/// A transport must disable its automatic redirects before applying this policy.
pub const AUTOMATIC_REDIRECTS: bool = false;
pub const APPROVED_REDIRECT_EDGES: &[(&str, &str)] = &[];
// Independently reviewed list, not derived from the source index.
pub const APPROVED_HOSTS: &[&str] = &[
    "www.austrac.gov.au",
    "www.legislation.gov.au",
    "www.ato.gov.au",
    "www.asic.gov.au",
    "apesb.org.au",
    "www.tpb.gov.au",
    "standards.aasb.gov.au",
    "www.revenue.nsw.gov.au",
    "community.ato.gov.au",
    "www.fairwork.gov.au",
    "www.sro.vic.gov.au",
    "qro.qld.gov.au",
    "www.wa.gov.au",
    "revenuesa.sa.gov.au",
    "www.sro.tas.gov.au",
    "www.revenue.act.gov.au",
    "treasury.nt.gov.au",
    "business.gov.au",
    "www.hcourt.gov.au",
    "softwaredevelopers.ato.gov.au",
    "coallsl.com.au",
    "assets.ctfassets.net",
    "www.cyber.gov.au",
    "legislation.nsw.gov.au",
    "www.caselaw.nsw.gov.au",
    "www.legislation.qld.gov.au",
    "github.com",
    "www.fedcourt.gov.au",
    "www.art.gov.au",
];
const MALFORMED: &str = "Malformed URL or port.";
const UNSUPPORTED: &str = "Unsupported destination; an exact reviewed HTTPS host is required.";
const NON_PUBLIC: &str = "Source hostname resolves to a non-public address.";

struct Parts<'a> {
    scheme: &'a str,
    authority: &'a str,
    rest: &'a str,
    host: String,
    port: Option<u16>,
}

// Parse only the components used by the policy, without URL canonicalisation.
// Match urllib.parse's bracket, NFKC and port checks before host approval.
fn parts(url: &str) -> Result<Parts<'_>> {
    let colon = url.find(':');
    let (scheme, remainder) = match colon {
        Some(i)
            if url[..i].starts_with(|c: char| c.is_ascii_alphabetic())
                && url[..i]
                    .chars()
                    .all(|c| c.is_ascii_alphanumeric() || "+-.".contains(c)) =>
        {
            (&url[..i], &url[i + 1..])
        }
        _ => ("", url),
    };
    let (authority, rest) = if let Some(after) = remainder.strip_prefix("//") {
        let end = after.find(['/', '?', '#']).unwrap_or(after.len());
        (&after[..end], &after[end..])
    } else {
        ("", remainder)
    };
    if !authority.is_ascii() {
        let n = authority.replace(['@', ':', '#', '?'], "");
        let normal: String = n.nfkc().collect();
        if n != normal && normal.contains(['/', '?', '#', '@', ':']) {
            return Err(MALFORMED.into());
        }
    }
    let hostinfo = authority.rsplit('@').next().unwrap();
    let (host, port) = if authority.contains(['[', ']']) {
        let bracket = hostinfo.strip_prefix('[').ok_or(MALFORMED)?;
        let (host, tail) = bracket.split_once(']').ok_or(MALFORMED)?;
        if !tail.is_empty() && !tail.starts_with(':') {
            return Err(MALFORMED.into());
        }
        if host.starts_with(['v', 'V']) {
            let (version, address) = host[1..].split_once('.').ok_or(MALFORMED)?;
            if version.is_empty()
                || !version.bytes().all(|c| c.is_ascii_hexdigit())
                || address.is_empty()
            {
                return Err(MALFORMED.into());
            }
        } else {
            let mut scoped = host.split('%');
            let address = scoped.next().unwrap();
            if let Some(scope) = scoped.next()
                && (scope.is_empty() || scoped.next().is_some())
            {
                return Err(MALFORMED.into());
            }
            address.parse::<Ipv6Addr>().map_err(|_| MALFORMED)?;
        }
        (host, tail.strip_prefix(':').unwrap_or(""))
    } else {
        hostinfo.split_once(':').unwrap_or((hostinfo, ""))
    };
    let port = if port.is_empty() {
        None
    } else {
        if port.len() > 4300 || !port.bytes().all(|c| c.is_ascii_digit()) {
            return Err(MALFORMED.into());
        }
        let digits = port.trim_start_matches('0');
        Some(if digits.is_empty() {
            0
        } else {
            digits.parse::<u16>().map_err(|_| MALFORMED)?
        })
    };
    Ok(Parts {
        scheme,
        authority,
        rest,
        host: host.to_lowercase(),
        port,
    })
}

pub fn checked_url(url: &str) -> Result<String> {
    if url.chars().any(|c| c <= ' ' || c == '\u{7f}' || c == '\\') {
        return Err("URL contains whitespace, controls or a backslash.".into());
    }
    let p = parts(url)?;
    if !p.scheme.eq_ignore_ascii_case("https")
        || !p.host.is_ascii()
        || !APPROVED_HOSTS.contains(&p.host.as_str())
        || p.authority.contains('@')
        || p.port.is_some_and(|port| port != 443)
    {
        return Err(UNSUPPORTED.into());
    }
    if !url.contains('#') {
        return Ok(url.to_owned());
    }
    // Python 3.14 urldefrag reconstructs only fragment-bearing URLs and retains an empty query.
    let rest = p.rest.split('#').next().unwrap();
    Ok(format!("https://{}{rest}", p.authority))
}

// Python 3.14 ipaddress tables, derived under the PSF licence in PYTHON-LICENSE.txt.
// Keep this baseline with the original helper rather than changing with Rust's tables.
const V4_PRIVATE: &[(u32, u32)] = &[
    (0x00000000, 8),
    (0x0a000000, 8),
    (0x7f000000, 8),
    (0xa9fe0000, 16),
    (0xac100000, 12),
    (0xc0000000, 24),
    (0xc00000aa, 31),
    (0xc0000200, 24),
    (0xc0a80000, 16),
    (0xc6120000, 15),
    (0xc6336400, 24),
    (0xcb007100, 24),
    (0xf0000000, 4),
    (0xffffffff, 32),
];
const V6_PRIVATE: &[(u128, u32)] = &[
    (1, 128),
    (0, 128),
    (0xffff00000000, 96),
    (0x0064ff9b000100000000000000000000, 48),
    (0x01000000000000000000000000000000, 64),
    (0x20010000000000000000000000000000, 23),
    (0x20010db8000000000000000000000000, 32),
    (0x20020000000000000000000000000000, 16),
    (0x3fff0000000000000000000000000000, 20),
    (0xfc000000000000000000000000000000, 7),
    (0xfe800000000000000000000000000000, 10),
];
const V6_EXCEPTIONS: &[(u128, u32)] = &[
    (0x20010001000000000000000000000001, 128),
    (0x20010001000000000000000000000002, 128),
    (0x20010003000000000000000000000000, 32),
    (0x20010004011200000000000000000000, 48),
    (0x20010020000000000000000000000000, 28),
    (0x20010030000000000000000000000000, 28),
];
fn v4_public(address: std::net::Ipv4Addr) -> bool {
    let n = u32::from(address);
    let private = V4_PRIVATE
        .iter()
        .any(|&(base, bits)| n >> (32 - bits) == base >> (32 - bits))
        && ![0xc0000009, 0xc000000a].contains(&n);
    !private && n >> 22 != 0x64400000 >> 22 && n >> 28 != 0xe
}
pub fn is_public_address(address: IpAddr) -> bool {
    match address {
        IpAddr::V4(a) => v4_public(a),
        IpAddr::V6(a) => {
            if let Some(mapped) = a.to_ipv4_mapped() {
                return v4_public(mapped);
            }
            let n = u128::from(a);
            let private = V6_PRIVATE
                .iter()
                .any(|&(base, bits)| n >> (128 - bits) == base >> (128 - bits))
                && !V6_EXCEPTIONS
                    .iter()
                    .any(|&(base, bits)| n >> (128 - bits) == base >> (128 - bits));
            !private && n >> 120 != 0xff
        }
    }
}
pub fn check_addresses(addresses: impl IntoIterator<Item = IpAddr>) -> Result<()> {
    let mut any = false;
    for address in addresses {
        any = true;
        if !is_public_address(address) {
            return Err(NON_PUBLIC.into());
        }
    }
    if !any {
        return Err(std::io::Error::other("Source hostname returned no addresses.").into());
    }
    Ok(())
}
/// Reject every non-public DNS answer. This does not pin a later HTTP connection.
/// The caller must call checked_url before resolving or opening a destination.
pub fn check_public_resolution(url: &str) -> Result<()> {
    let p = parts(url)?;
    check_addresses((p.host.as_str(), 443).to_socket_addrs()?.map(|a| a.ip()))
}

fn python_space(c: char) -> bool {
    c.is_whitespace() || matches!(c, '\u{1c}'..='\u{1f}')
}
pub fn bounded_body(
    response: &mut impl Read,
    encoding: Option<&str>,
    length: Option<&str>,
) -> Result<Vec<u8>> {
    let encoding = encoding.unwrap_or("identity").trim_matches(python_space);
    if !encoding.is_empty() && !encoding.eq_ignore_ascii_case("identity") {
        return Err("Encoded response is unsupported.".into());
    }
    if let Some(length) = length {
        if length.is_empty() || !length.bytes().all(|c| c.is_ascii_digit()) {
            return Err("Malformed Content-Length.".into());
        }
        let normal = length.trim_start_matches('0');
        if normal.len() > 7 || normal.parse::<usize>().unwrap_or(0) > MAX_RESPONSE_BYTES {
            return Err("Response exceeds the 8 MiB ceiling.".into());
        }
    }
    let mut body = Vec::new();
    let mut buffer = [0; READ_CHUNK_BYTES];
    while body.len() <= MAX_RESPONSE_BYTES {
        let amount = READ_CHUNK_BYTES.min(MAX_RESPONSE_BYTES + 1 - body.len());
        let count = response.read(&mut buffer[..amount])?;
        if count == 0 {
            return Ok(body);
        }
        body.extend_from_slice(&buffer[..count]);
    }
    Err("Response exceeds the 8 MiB ceiling; no prefix is digested.".into())
}
