use accounting_skills::source_fetch_policy as p;
use std::io::{self, Read};

#[test]
fn urls_preserve_reviewed_spelling_and_refuse_authority_changes() {
    assert_eq!(
        p::checked_url("https://www.fairwor\u{212a}.gov.au/path#x").unwrap(),
        "https://www.fairwor\u{212a}.gov.au/path"
    );
    assert_eq!(
        p::checked_url("HTTPS://WWW.ATO.GOV.AU:00443/a?#x").unwrap(),
        "https://WWW.ATO.GOV.AU:00443/a?"
    );
    assert_eq!(
        p::checked_url("HTTPS://www.ato.gov.au/a?").unwrap(),
        "HTTPS://www.ato.gov.au/a?"
    );
    for url in [
        "https://www.ato.gov.au.evil.test/",
        "https://www.ato.gov.au@evil.test/",
        "https://www.ato.gov.au:80/",
        "https://www.ato.gov.au./",
        "https://www.ato.gov.au\\x",
        "https://[::1]/",
        "https://www.ato.gov.au：443/",
    ] {
        assert!(p::checked_url(url).is_err(), "{url}");
    }
}
#[test]
fn all_dns_answers_must_be_public_including_mapped_ipv6() {
    for address in [
        "8.8.8.8",
        "192.0.0.9",
        "192.0.0.10",
        "2001:1::1",
        "2001:3::1",
        "fec0::1",
    ] {
        assert!(p::is_public_address(address.parse().unwrap()), "{address}");
    }
    for address in [
        "100.64.0.1",
        "192.0.0.8",
        "::ffff:127.0.0.1",
        "::ffff:224.0.0.1",
        "2001:db8::1",
        "3fff::1",
        "ff02::1",
    ] {
        assert!(!p::is_public_address(address.parse().unwrap()), "{address}");
    }
    assert!(
        p::check_addresses(["8.8.8.8".parse().unwrap(), "127.0.0.1".parse().unwrap()]).is_err()
    );
    assert_eq!(
        p::check_addresses([]).unwrap_err().to_string(),
        "Source hostname returned no addresses."
    );
}
struct Reader {
    remaining: usize,
    calls: Vec<usize>,
    fail: bool,
}
impl Read for Reader {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        self.calls.push(buf.len());
        if self.fail {
            return Err(io::Error::other("read failed"));
        }
        let n = buf.len().min(self.remaining);
        buf[..n].fill(42);
        self.remaining -= n;
        Ok(n)
    }
}
#[test]
fn body_ceiling_checks_eof_without_returning_an_overflow_prefix() {
    let mut r = Reader {
        remaining: p::MAX_RESPONSE_BYTES,
        calls: vec![],
        fail: false,
    };
    assert_eq!(
        p::bounded_body(&mut r, None, Some("0008388608"))
            .unwrap()
            .len(),
        p::MAX_RESPONSE_BYTES
    );
    assert_eq!(r.calls.last(), Some(&1));
    assert!(r.calls.iter().all(|&n| n <= p::READ_CHUNK_BYTES));
    r.remaining = p::MAX_RESPONSE_BYTES + 1;
    assert_eq!(
        p::bounded_body(&mut r, None, Some("1"))
            .unwrap_err()
            .to_string(),
        "Response exceeds the 8 MiB ceiling; no prefix is digested."
    );
}
#[test]
fn headers_are_checked_before_any_read_and_io_errors_propagate() {
    for (encoding, length) in [
        (Some("gzip"), None),
        (None, Some("+1")),
        (None, Some("8388609")),
        (None, Some("")),
    ] {
        let mut r = Reader {
            remaining: 1,
            calls: vec![],
            fail: false,
        };
        assert!(p::bounded_body(&mut r, encoding, length).is_err());
        assert!(r.calls.is_empty());
    }
    let mut r = Reader {
        remaining: 1,
        calls: vec![],
        fail: true,
    };
    let error = p::bounded_body(&mut r, None, None).unwrap_err();
    assert!(error.is::<io::Error>());
    assert_eq!(error.to_string(), "read failed");
}
