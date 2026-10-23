use accounting_skills::{Result, source_fetch_policy as policy, source_refresh as s};
use s::transport::{Response, Transport};
use serde_json::json;
use std::{
    cell::RefCell,
    collections::VecDeque,
    io::{self, Read},
    rc::Rc,
};

const URL: &str = "https://www.ato.gov.au/a";
#[test]
fn published_dates_preserve_python_numeric_and_mail_rules() {
    for value in [
        "١ Jan ٢٠٢٦ ١٢:٣٠ GMT",
        "1\u{1c}Jan\u{1c}2026\u{1c}12:30\u{1c}GMT",
        "1 Jan 2026 12:30 +23_00",
    ] {
        assert_eq!(s::iso_day(value), "2026-01-01");
    }
    for value in [
        "1 Jan 2026 12:30 +999999999999999999999999999",
        "1 Jan 2026,, 12:30 GMT",
        "1 Jan 2026 12:30,, GMT",
        "2026-01-01T12:30:60",
    ] {
        assert_eq!(s::iso_day(value), "");
    }
    let date: String = "1 Jan 2026 12:30 GMT"
        .chars()
        .map(|c| {
            c.to_digit(10)
                .map_or(c, |n| char::from_u32(0x1d7ce + n).unwrap())
        })
        .collect();
    assert_eq!(s::iso_day(&date), "2026-01-01");
    for markup in [
        format!(r#""dateModified":"{date}""#),
        format!(r#"<meta name="DCTERMS.modified" content="{date}">"#),
        format!(r#"<meta content="{date}" name="DCTERMS.modified">"#),
    ] {
        assert_eq!(
            s::transport::upstream_last_modified(markup.as_bytes(), None, None).unwrap(),
            ""
        );
        assert_eq!(
            s::transport::upstream_last_modified(markup.as_bytes(), Some("2026-01-02"), None)
                .unwrap(),
            "2026-01-02"
        );
    }
    let large = format!("{}1", "0".repeat(4300));
    assert_eq!(s::iso_day(&format!("{large} Jan 2026 12:30 GMT")), "");
    assert_eq!(s::iso_day(&format!("1 Jan {large} 12:30 GMT")), "");
    assert_eq!(
        s::iso_day(&format!("1 Jan 2026 12:30 +{large}")),
        "2026-01-01"
    );
}
#[test]
fn human_dates_refuse_year_zero_even_with_matching_acceptance() {
    let mut record = json!({"checked_at":"0000-01-01","fact":"fixture","content_hash":"a","content_hash_covers":"html","content_url":URL,"source_last_modified":""});
    assert_eq!(s::review_date(&json!({"next_review":"0000-01-01"})), "");
    assert!(!s::human_readiness(&record, "2026-10-23").1.is_empty());
    record["checked_at"] = json!("2026-10-01");
    record["review_required_since"] = json!("0000-01-01");
    record["reviewed_content"] = json!({"checked_at":"2026-10-01","content_hash":"a","content_hash_covers":"html","content_url":URL,"source_last_modified":""});
    assert!(!s::human_readiness(&record, "2026-10-23").1.is_empty());
    for value in ["0001-01-01", "9999-12-31"] {
        assert_eq!(s::review_date(&json!({"next_review":value})), value);
    }
}
#[test]
fn malformed_inventory_and_dangling_links_cannot_complete_a_sweep_or_write() {
    let temp = tempfile::tempdir().unwrap();
    let skills = temp.path().join(".claude/skills");
    std::fs::create_dir_all(skills.join("a-valid")).unwrap();
    std::fs::create_dir_all(skills.join("z-invalid")).unwrap();
    let valid = skills.join("a-valid/sources.json");
    let original =
        format!(r#"{{"sources":[{{"url":"{URL}","checked_at":"2026-10-01","fact":"fixture"}}]}}"#);
    std::fs::write(&valid, &original).unwrap();
    let invalid = skills.join("z-invalid/sources.json");
    std::fs::write(&invalid, "[]").unwrap();
    assert_eq!(s::load_index(&invalid, &skills).unwrap(), json!([]));
    let options = s::Options {
        write: true,
        spacing: 0.0,
        today: "2026-10-23".into(),
        ..s::Options::default()
    };
    assert!(
        s::refresh_with(
            &skills,
            &options,
            |_| s::Fetched {
                status: Some(200),
                final_url: URL.into(),
                digest: "new".into(),
                kind: "html".into(),
                ..s::Fetched::default()
            },
            |_| Ok(())
        )
        .is_err()
    );
    assert_eq!(std::fs::read_to_string(&valid).unwrap(), original);
    std::fs::remove_file(&invalid).unwrap();
    #[cfg(windows)]
    std::os::windows::fs::symlink_file(temp.path().join("missing.json"), &invalid).unwrap();
    #[cfg(unix)]
    std::os::unix::fs::symlink(temp.path().join("missing.json"), &invalid).unwrap();
    assert!(s::index_files(&skills).is_err());
    assert_eq!(std::fs::read_to_string(&valid).unwrap(), original);
}
#[test]
fn confusable_published_keys_cannot_hide_a_later_http_date_or_make_preflight_ready() {
    for key in ["dateModifİed", "dateModıfied"] {
        let mut spec = Spec::html(&format!(
            r#"<main>Unchanged content</main><script>{{"{key}":"2020-01-01"}}</script>"#
        ));
        spec.headers.extend([
            (
                "Last-Modified".into(),
                "Tue, 20 Oct 2026 12:00:00 GMT".into(),
            ),
            ("Date".into(), "Fri, 23 Oct 2026 12:00:00 GMT".into()),
        ]);
        let mut fake = Fake::new(vec![spec]);
        let (fetched, _) = fetch(&mut fake);
        assert_eq!(fetched.last_modified, "2026-10-20");
        let record = json!({"url":URL,"checked_at":"2026-10-01","fact":"fixture","content_hash":fetched.digest,"content_hash_covers":"html","content_url":URL});
        assert_eq!(s::classify(&record, &fetched).0, s::CHANGED);
        let temp = tempfile::tempdir().unwrap();
        let skills = temp.path().join(".claude/skills");
        std::fs::create_dir_all(skills.join("example")).unwrap();
        std::fs::write(skills.join("example/SKILL.md"), "fixture").unwrap();
        std::fs::write(
            skills.join("example/sources.json"),
            serde_json::to_vec(&json!({"skill":"example","sources":[record]})).unwrap(),
        )
        .unwrap();
        let (report, code) = s::preflight_with(
            "example",
            &skills,
            "2026-10-23",
            0.0,
            |_| fetched.clone(),
            |_| Ok(()),
        );
        assert_eq!(code, 2);
        assert!(!report.contains("READY:"));
    }
}
#[derive(Clone)]
struct Spec {
    status: u16,
    destination: String,
    headers: Vec<(String, String)>,
    bytes: Vec<u8>,
    fail: bool,
}
impl Spec {
    fn html(text: &str) -> Self {
        Self {
            status: 200,
            destination: URL.into(),
            headers: vec![("Content-Type".into(), "text/html; charset=utf-8".into())],
            bytes: text.as_bytes().to_vec(),
            fail: false,
        }
    }
    fn redirect(location: &str) -> Self {
        let mut value = Self::html("");
        value.status = 302;
        value.headers = vec![("Location".into(), location.into())];
        value
    }
}
struct Body {
    inner: io::Cursor<Vec<u8>>,
    fail: bool,
    events: Rc<RefCell<Vec<String>>>,
}
impl Read for Body {
    fn read(&mut self, out: &mut [u8]) -> io::Result<usize> {
        self.events.borrow_mut().push("read".into());
        if self.fail {
            Err(io::Error::other("fabricated read failure"))
        } else {
            self.inner.read(out)
        }
    }
}
impl Drop for Body {
    fn drop(&mut self) {
        self.events.borrow_mut().push("close".into());
    }
}
struct Fake {
    responses: VecDeque<Spec>,
    events: Rc<RefCell<Vec<String>>>,
    private: bool,
    dns_failures: usize,
    open_failures: usize,
}
impl Fake {
    fn new(specs: Vec<Spec>) -> Self {
        Self {
            responses: specs.into(),
            events: Rc::default(),
            private: false,
            dns_failures: 0,
            open_failures: 0,
        }
    }
}
impl Transport for Fake {
    fn resolve(&mut self, url: &str) -> Result<()> {
        self.events.borrow_mut().push(format!("resolve {url}"));
        if self.dns_failures > 0 {
            self.dns_failures -= 1;
            return Err(io::Error::other("fabricated DNS failure").into());
        }
        policy::check_addresses(vec![
            if self.private { "127.0.0.1" } else { "8.8.8.8" }.parse()?,
        ])
    }
    fn open(&mut self, url: &str) -> Result<Response> {
        self.events.borrow_mut().push(format!("open {url}"));
        if self.open_failures > 0 {
            self.open_failures -= 1;
            return Err(io::Error::other("fabricated open failure").into());
        }
        let spec = self.responses.pop_front().expect("unexpected request");
        Ok(Response {
            status: spec.status,
            reason: if spec.status == 403 {
                "Forbidden"
            } else {
                "OK"
            }
            .into(),
            final_url: spec.destination,
            headers: spec.headers,
            body: Box::new(Body {
                inner: io::Cursor::new(spec.bytes),
                fail: spec.fail,
                events: self.events.clone(),
            }),
        })
    }
}
fn fetch(fake: &mut Fake) -> (s::Fetched, Vec<f64>) {
    let mut sleeps = Vec::new();
    let result = s::fetch_with(fake, URL, 3, 6.0, true, |delay| {
        sleeps.push(delay);
        Ok(())
    });
    (result, sleeps)
}

#[test]
fn redirect_policy_runs_before_every_open_and_closes_each_response() {
    let mut final_response = Spec::html("<main>Current &amp; complete</main>");
    final_response.destination = "https://www.ato.gov.au/b".into();
    let mut fake = Fake::new(vec![Spec::redirect("/b#section"), final_response]);
    let (value, sleeps) = fetch(&mut fake);
    assert!(value.readable());
    assert_eq!(value.text, "Current & complete");
    assert_eq!(value.final_url, "https://www.ato.gov.au/b");
    assert!(sleeps.is_empty());
    assert_eq!(
        &*fake.events.borrow(),
        &[
            format!("resolve {URL}"),
            format!("open {URL}"),
            "close".into(),
            "resolve https://www.ato.gov.au/b".into(),
            "open https://www.ato.gov.au/b".into(),
            "read".into(),
            "read".into(),
            "close".into()
        ]
    );
    for location in [
        "https://www.asic.gov.au/x",
        "https://127.0.0.1/x",
        "http://www.ato.gov.au/x",
        URL,
        "",
    ] {
        let mut fake = Fake::new(vec![Spec::redirect(location)]);
        let (value, sleeps) = fetch(&mut fake);
        assert!(
            value.error.starts_with("Source policy:"),
            "{location}: {value:?}"
        );
        assert!(sleeps.is_empty());
        assert_eq!(
            fake.events
                .borrow()
                .iter()
                .filter(|v| v.starts_with("open "))
                .count(),
            1
        );
        assert_eq!(fake.events.borrow().last().unwrap(), "close");
    }
}
#[test]
fn private_dns_and_unsafe_initial_urls_never_open() {
    let mut fake = Fake::new(vec![]);
    fake.private = true;
    let (value, sleeps) = fetch(&mut fake);
    assert!(value.error.contains("non-public"));
    assert!(sleeps.is_empty());
    assert_eq!(fake.events.borrow().len(), 1);
    let value = s::fetch_with(&mut fake, "https://example.test/x", 3, 0.0, false, |_| {
        panic!("must not retry")
    });
    assert!(value.error.starts_with("Source policy:"));
    assert_eq!(fake.events.borrow().len(), 1);
}
#[test]
fn transport_faults_retry_but_settled_http_and_policy_failures_do_not() {
    for stage in ["dns", "open", "read"] {
        let mut bad = Spec::html("bad");
        bad.fail = true;
        let mut fake = Fake::new(if stage == "read" {
            vec![bad, Spec::html("good")]
        } else {
            vec![Spec::html("good")]
        });
        if stage == "dns" {
            fake.dns_failures = 1;
        }
        if stage == "open" {
            fake.open_failures = 1;
        }
        let (value, sleeps) = fetch(&mut fake);
        assert!(value.readable(), "{stage}");
        assert_eq!(sleeps, vec![6.0]);
        assert_eq!(
            fake.events
                .borrow()
                .iter()
                .filter(|v| *v == "close")
                .count(),
            if stage == "read" { 2 } else { 1 }
        );
    }
    let mut spec = Spec::html("do not read");
    spec.status = 403;
    spec.destination = "https://www.ato.gov.au/blocked".into();
    let mut fake = Fake::new(vec![spec]);
    let (value, sleeps) = fetch(&mut fake);
    assert_eq!(value.error, "HTTP 403 Forbidden");
    assert_eq!(value.final_url, "https://www.ato.gov.au/blocked");
    assert!(sleeps.is_empty());
    assert!(!fake.events.borrow().iter().any(|v| v == "read"));
    assert_eq!(fake.events.borrow().last().unwrap(), "close");
    for header in [
        ("Content-Encoding", "gzip"),
        ("Content-Length", "8388609"),
        ("Content-Length", "+2"),
    ] {
        let mut spec = Spec::html("bad");
        spec.headers.push((header.0.into(), header.1.into()));
        let mut fake = Fake::new(vec![spec]);
        let (value, sleeps) = fetch(&mut fake);
        assert!(value.error.starts_with("Source policy:"));
        assert!(sleeps.is_empty());
        assert!(!fake.events.borrow().iter().any(|v| v == "read"));
        assert_eq!(fake.events.borrow().last().unwrap(), "close");
    }
}
#[test]
fn response_destination_redirect_ceiling_and_charset_fail_closed() {
    let mut spec = Spec::html("bad");
    spec.destination = "https://www.ato.gov.au/other".into();
    let mut fake = Fake::new(vec![spec]);
    let (value, _) = fetch(&mut fake);
    assert!(value.error.contains("Unexpected response destination"));
    assert!(!fake.events.borrow().iter().any(|v| v == "read"));
    let mut fake = Fake::new(
        (0..4)
            .map(|i| Spec::redirect(&format!("/hop{i}")))
            .collect(),
    );
    let (value, sleeps) = fetch(&mut fake);
    assert!(value.error.contains("redirect ceiling"));
    assert!(sleeps.is_empty());
    assert_eq!(
        fake.events
            .borrow()
            .iter()
            .filter(|v| *v == "close")
            .count(),
        4
    );
    let mut spec = Spec::html("bad");
    spec.headers = vec![("Content-Type".into(), "text/html; charset=shift_jis".into())];
    let mut fake = Fake::new(vec![spec]);
    let (value, sleeps) = fetch(&mut fake);
    assert!(
        value
            .error
            .starts_with("Source policy: Unqualified source charset")
    );
    assert!(sleeps.is_empty());
    assert_eq!(s::classify(&json!({}), &value).0, s::UNREADABLE);
}
#[test]
fn text_limit_counts_characters_and_digest_covers_the_whole_body() {
    let text = "𝄞".repeat(32769);
    let mut spec = Spec::html(&text);
    spec.headers = vec![("Content-Type".into(), "text/plain; charset=utf-8".into())];
    let mut fake = Fake::new(vec![spec]);
    let (value, _) = fetch(&mut fake);
    assert_eq!(value.text.chars().count(), 32768);
    assert!(value.text_truncated);
    assert_eq!(value.digest, s::content_digest(&text));
    assert_eq!(value.kind, "bytes");
}

#[test]
fn extended_parameters_preserve_plain_precedence_and_numeric_order() {
    for character in ['\u{1c89}', '\u{11db0}', '\u{1e6c0}', '\u{16ea0}'] {
        let header = format!(
            "text/plain;x{character}*{}=unused;charset=utf-8",
            "0".repeat(4301)
        );
        assert_eq!(
            s::transport::content_type(Some(&header)).unwrap(),
            ("text/plain".into(), Some("utf-8".into()))
        );
    }
    for (header, expected) in [
        ("text/html; charset*=utf-8''ascii; charset=UTF-8", "utf-8"),
        ("text/html; charset*1=8; charset*0=utf-", "utf-8"),
        ("text/html; charset*=ascii; charset*0=utf-8", "utf-8"),
        ("text/html; charset*=made-up''utf%2D8", "utf-8"),
        ("text/html; charset*=utf-16''abc", "abc"),
        ("text/html; charset*=rot13''utf-8", "utf-8"),
        ("text/html; charset*=cpé037''UTF-8", "utf-8"),
        ("charset=utf-8", "utf-8"),
    ] {
        let (_, charset) = s::transport::content_type(Some(header)).unwrap();
        assert_eq!(charset.as_deref(), Some(expected), "{header}");
    }
    let large = "9".repeat(4300);
    let header = format!("text/html; charset*{large}=8; charset*0=utf-");
    assert_eq!(
        s::transport::content_type(Some(&header))
            .unwrap()
            .1
            .as_deref(),
        Some("utf-8")
    );
}

#[test]
fn parameter_conversion_errors_and_non_ascii_fallback_are_preserved() {
    for header in [
        format!("text/html; x*{}=unused; charset=utf-8", "0".repeat(4301)),
        "text/html; charset*=utf-8%00''ascii".into(),
    ] {
        assert!(s::transport::content_type(Some(&header)).is_err());
    }
    assert_eq!(
        s::transport::content_type(Some("text/html; charset*=utf-8''%FF"))
            .unwrap()
            .1,
        None
    );
    assert!(
        s::transport::content_type(Some("text/html; charset*=utf-7''+AFU-+AFQ-+AEY--8"))
            .unwrap_err()
            .to_string()
            .starts_with("Unqualified source charset ")
    );
}

#[test]
fn extended_charset_and_legacy_body_feed_the_full_html_digest() {
    let mut spec = Spec::html("");
    spec.headers = vec![(
        "Content-Type".into(),
        "text/html; charset*1*=r; charset*0*=us-ascii''koi8-".into(),
    )];
    spec.bytes = [
        b"<main>".as_slice(),
        &[0xf0, 0xd2, 0xc9, 0xd7, 0xc5, 0xd4],
        b"</main>",
    ]
    .concat();
    let mut fake = Fake::new(vec![spec]);
    let (value, sleeps) = fetch(&mut fake);
    assert!(value.error.is_empty());
    assert!(sleeps.is_empty());
    assert_eq!(value.text, "Привет");
    assert_eq!(value.digest, s::content_digest("Привет"));
    assert_eq!(value.kind, "html");
    assert_eq!(
        fake.events
            .borrow()
            .iter()
            .filter(|event| *event == "close")
            .count(),
        1
    );
}
#[test]
fn index_write_preserves_human_fields_and_detects_replacement_links() {
    let temp = tempfile::tempdir().unwrap();
    let skills = temp.path().join("skills");
    let directory = skills.join("example");
    std::fs::create_dir_all(&directory).unwrap();
    let index = directory.join("sources.json");
    let record = json!({"url":URL,"checked_at":"2026-10-01","fact":"fixture","reverify_by":"2026-11-01","content_hash":"old","content_hash_covers":"html","content_url":URL});
    std::fs::write(
        &index,
        serde_json::to_string(&json!({"skill":"example","sources":[record]})).unwrap(),
    )
    .unwrap();
    let options = s::Options {
        write: true,
        today: "2026-10-23".into(),
        spacing: 0.0,
        ..s::Options::default()
    };
    let report = s::refresh_with(
        &skills,
        &options,
        |_| s::Fetched {
            status: Some(200),
            final_url: URL.into(),
            digest: "new".into(),
            kind: "html".into(),
            ..s::Fetched::default()
        },
        |_| Ok(()),
    )
    .unwrap();
    assert_eq!(report.written, vec![index.clone()]);
    let stored = s::load_index(&index, &skills).unwrap();
    let stored = &stored["sources"][0];
    for key in [
        "checked_at",
        "fact",
        "reverify_by",
        "content_hash",
        "content_hash_covers",
        "content_url",
    ] {
        assert_eq!(stored[key], record[key], "{key}");
    }
    assert_eq!(stored["pending_review"]["content_hash"], "new");
    let outside = temp.path().join("outside.json");
    std::fs::write(&outside, "untouched").unwrap();
    let result = s::refresh_with(
        &skills,
        &options,
        |_| {
            std::fs::remove_file(&index).unwrap();
            #[cfg(windows)]
            std::os::windows::fs::symlink_file(&outside, &index).unwrap();
            #[cfg(unix)]
            std::os::unix::fs::symlink(&outside, &index).unwrap();
            s::Fetched {
                status: Some(200),
                final_url: URL.into(),
                digest: "new".into(),
                kind: "html".into(),
                ..s::Fetched::default()
            }
        },
        |_| Ok(()),
    );
    assert!(
        result
            .unwrap_err()
            .to_string()
            .contains("Linked source index")
    );
    assert_eq!(std::fs::read_to_string(&outside).unwrap(), "untouched");
}
