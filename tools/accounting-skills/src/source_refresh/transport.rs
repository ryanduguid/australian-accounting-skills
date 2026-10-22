use super::{Fetched, iso_day};
use crate::{Result, source_content as content, source_fetch_policy as policy};
use fancy_regex::Regex;
use std::{collections::BTreeSet, io::Read, sync::LazyLock, time::Duration};

pub struct Response {
    pub status: u16,
    pub reason: String,
    pub final_url: String,
    pub headers: Vec<(String, String)>,
    pub body: Box<dyn Read>,
}
impl Response {
    pub fn header(&self, name: &str) -> Option<&str> {
        self.headers
            .iter()
            .find(|(key, _)| key.eq_ignore_ascii_case(name))
            .map(|(_, v)| v.as_str())
    }
}
pub trait Transport {
    fn resolve(&mut self, url: &str) -> Result<()>;
    fn open(&mut self, url: &str) -> Result<Response>;
}
pub struct HttpTransport {
    agent: ureq::Agent,
}
impl Default for HttpTransport {
    fn default() -> Self {
        let config = ureq::Agent::config_builder()
            .proxy(None)
            .max_redirects(0)
            .http_status_as_error(false)
            .timeout_global(Some(Duration::from_secs(30)))
            .tls_config(
                ureq::tls::TlsConfig::builder()
                    .root_certs(ureq::tls::RootCerts::PlatformVerifier)
                    .build(),
            )
            .build();
        Self {
            agent: config.into(),
        }
    }
}
impl Transport for HttpTransport {
    fn resolve(&mut self, url: &str) -> Result<()> {
        policy::check_public_resolution(url)
    }
    fn open(&mut self, url: &str) -> Result<Response> {
        let (_, tail) = url.split_once("://").ok_or("URL has no authority")?;
        let end = tail.find(['/', '?']).unwrap_or(tail.len());
        let wire = format!("https://{}{}", tail[..end].to_lowercase(), &tail[end..]);
        let response=self.agent.get(&wire).header("User-Agent","australian-accounting-skills source-refresh (+https://github.com/ryanduguid/australian-accounting-skills)")
   .header("Accept","text/html,application/xhtml+xml,*/*").header("Accept-Encoding","identity").call()?;
        let (parts, body) = response.into_parts();
        let headers = parts
            .headers
            .iter()
            .filter(|(name, _)| {
                matches!(
                    name.as_str(),
                    "location"
                        | "content-type"
                        | "content-encoding"
                        | "content-length"
                        | "last-modified"
                        | "date"
                )
            })
            // Python's HTTP header parser maps each wire octet through Latin-1.
            .map(|(name, value)| {
                (
                    name.to_string(),
                    value.as_bytes().iter().map(|&b| char::from(b)).collect(),
                )
            })
            .collect();
        Ok(Response {
            status: parts.status.as_u16(),
            reason: parts.status.canonical_reason().unwrap_or("").into(),
            final_url: url.into(),
            headers,
            body: Box::new(body.into_reader()),
        })
    }
}
fn host(url: &str) -> String {
    url.split_once("://")
        .map(|(_, tail)| {
            tail.split(['/', '?', '#', ':'])
                .next()
                .unwrap()
                .to_lowercase()
        })
        .unwrap_or_default()
}
pub fn join(base: &str, reference: &str) -> String {
    crate::source_urls::join(base, reference)
}

pub fn upstream_last_modified(
    body: &[u8],
    last: Option<&str>,
    served: Option<&str>,
) -> Result<String> {
    static JSON: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(r#"(?i)"dateModified"[\t\n\r\x0b\x0c ]*:[\t\n\r\x0b\x0c ]*"([^"]{4,40})""#)
            .unwrap()
    });
    static META: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(r#"(?i)<meta[^>]*?(?:name|property)[\t\n\r\x0b\x0c ]*=[\t\n\r\x0b\x0c ]*["'](?:DCTERMS\.modified|article:modified_time|og:updated_time)["'][^>]*?content[\t\n\r\x0b\x0c ]*=[\t\n\r\x0b\x0c ]*["']([^"']{4,40})["']"#).unwrap()
    });
    static REVERSE: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(r#"(?i)<meta[^>]*?content[\t\n\r\x0b\x0c ]*=[\t\n\r\x0b\x0c ]*["']([^"']{4,40})["'][^>]*?(?:name|property)[\t\n\r\x0b\x0c ]*=[\t\n\r\x0b\x0c ]*["'](?:DCTERMS\.modified|article:modified_time|og:updated_time)["']"#).unwrap()
    });
    // Python searches bytes: one projected scalar per byte preserves its 4..40
    // capture limit, including non-ASCII and malformed UTF-8. Pattern literals
    // are ASCII; no non-ASCII Latin-1 scalar case-folds to an ASCII letter.
    let text: String = body.iter().map(|&byte| char::from(byte)).collect();
    for pattern in [&*JSON, &*META, &*REVERSE] {
        if let Some(found) = pattern.captures(text.as_ref())? {
            let captured: Vec<u8> = found[1].chars().map(|c| c as u8).collect();
            let day = iso_day(&String::from_utf8_lossy(&captured));
            if !day.is_empty() {
                return Ok(day);
            }
        }
    }
    let last = iso_day(last.unwrap_or(""));
    let served = iso_day(served.unwrap_or(""));
    Ok(
        if !last.is_empty() && (served.is_empty() || last < served) {
            last
        } else {
            String::new()
        },
    )
}
pub fn content_type(value: Option<&str>) -> (String, Option<String>) {
    let value = value.unwrap_or("text/plain");
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
    // email.message._parseparam treats double-quoted semicolons as value data.
    let mut parts = Vec::new();
    let mut start = 0;
    let mut quotes = 0;
    let mut previous = '\0';
    for (i, c) in value.char_indices() {
        if c == '"' && previous != '\\' {
            quotes += 1;
        }
        if c == ';' && quotes % 2 == 0 {
            parts.push(&value[start..i]);
            start = i + 1;
        }
        previous = c;
    }
    parts.push(&value[start..]);
    let mut charset = None;
    for part in parts.into_iter().skip(1) {
        let (key, raw) = part.split_once('=').unwrap_or((part, ""));
        let key = key.trim_matches(content::space).to_lowercase();
        if key.starts_with("charset*") {
            if charset.is_none() {
                charset = Some("unqualified-rfc2231-charset-parameter".into());
            }
            continue;
        }
        if key != "charset" || charset.is_some() {
            continue;
        }
        let raw = raw.trim_matches(content::space);
        let value = if raw.len() > 1 && raw.starts_with('"') && raw.ends_with('"') {
            raw[1..raw.len() - 1]
                .replace("\\\\", "\\")
                .replace("\\\"", "\"")
        } else if raw.len() > 1 && raw.starts_with('<') && raw.ends_with('>') {
            raw[1..raw.len() - 1].into()
        } else {
            raw.into()
        };
        if value.is_ascii() {
            charset = Some(value.to_ascii_lowercase());
        } else {
            break;
        }
    }
    (kind, charset)
}
enum Failure {
    Policy(String),
    Transport(String),
}
fn policy_error(error: Box<dyn std::error::Error>) -> Failure {
    if error.is::<std::io::Error>() {
        Failure::Transport(error.to_string())
    } else {
        Failure::Policy(error.to_string())
    }
}
fn interpretation_error(error: Box<dyn std::error::Error>) -> Failure {
    let message = error.to_string();
    if message.starts_with("Unqualified source charset ") {
        Failure::Policy(message)
    } else {
        Failure::Transport(message)
    }
}
fn attempt(
    transport: &mut impl Transport,
    url: &str,
    include_text: bool,
) -> std::result::Result<Fetched, Failure> {
    let mut target = policy::checked_url(url).map_err(|e| Failure::Policy(e.to_string()))?;
    let mut seen = BTreeSet::from([target.clone()]);
    for hop in 0..=policy::MAX_REDIRECTS {
        transport.resolve(&target).map_err(policy_error)?;
        let mut response = transport
            .open(&target)
            .map_err(|e| Failure::Transport(e.to_string()))?;
        if [301, 302, 303, 307, 308].contains(&response.status) {
            let location = response.header("Location").filter(|v| !v.is_empty());
            if location.is_none() || hop == policy::MAX_REDIRECTS {
                return Err(Failure::Policy(
                    "Missing redirect location or redirect ceiling exceeded.".into(),
                ));
            }
            let following = policy::checked_url(&join(&target, location.unwrap()))
                .map_err(|e| Failure::Policy(e.to_string()))?;
            let edge = (host(&target), host(&following));
            if edge.0 != edge.1
                && !policy::APPROVED_REDIRECT_EDGES.contains(&(edge.0.as_str(), edge.1.as_str()))
            {
                return Err(Failure::Policy(
                    "Cross-host redirect has not been reviewed.".into(),
                ));
            }
            if !seen.insert(following.clone()) {
                return Err(Failure::Policy("Redirect loop.".into()));
            }
            target = following;
            continue;
        }
        if !(200..300).contains(&response.status) {
            return Ok(Fetched {
                status: Some(response.status),
                final_url: response.final_url.clone(),
                error: format!("HTTP {} {}", response.status, response.reason),
                ..Fetched::default()
            });
        }
        let final_url =
            policy::checked_url(&response.final_url).map_err(|e| Failure::Policy(e.to_string()))?;
        if final_url != target {
            return Err(Failure::Policy("Unexpected response destination.".into()));
        }
        let encoding = response.header("Content-Encoding").map(str::to_owned);
        let length = response.header("Content-Length").map(str::to_owned);
        let body = policy::bounded_body(&mut response.body, encoding.as_deref(), length.as_deref())
            .map_err(policy_error)?;
        let (kind, charset) = content_type(response.header("Content-Type"));
        let (digest, reading) =
            content::body_digest(&body, &kind, charset.as_deref()).map_err(interpretation_error)?;
        let text =
            if include_text && ["text/html", "application/xhtml+xml"].contains(&kind.as_str()) {
                content::readable_text(&body, charset.as_deref())
            } else if include_text && kind == "text/plain" {
                content::decode(&body, charset.as_deref())
            } else {
                Ok(String::new())
            }
            .map_err(interpretation_error)?;
        let last_modified = upstream_last_modified(
            &body,
            response.header("Last-Modified"),
            response.header("Date"),
        )
        .map_err(|e| Failure::Transport(e.to_string()))?;
        return Ok(Fetched {
            status: Some(response.status),
            final_url,
            digest,
            kind: reading,
            content_type: kind,
            last_modified,
            error: String::new(),
            text_truncated: text.chars().count() > 32768,
            text: text.chars().take(32768).collect(),
        });
    }
    unreachable!()
}
pub fn fetch_with(
    transport: &mut impl Transport,
    url: &str,
    tries: usize,
    delay: f64,
    include_text: bool,
    mut sleep: impl FnMut(f64) -> Result<()>,
) -> Fetched {
    let mut last = String::new();
    for n in 0..tries {
        match attempt(transport, url, include_text) {
            Ok(value) => return value,
            Err(Failure::Policy(message)) => {
                return Fetched {
                    status: Some(0),
                    final_url: url.into(),
                    error: format!("Source policy: {message}"),
                    ..Fetched::default()
                };
            }
            Err(Failure::Transport(message)) => {
                last = message;
                if n + 1 < tries
                    && let Err(e) = sleep(delay)
                {
                    last = e.to_string();
                    break;
                }
            }
        }
    }
    Fetched {
        status: Some(0),
        final_url: url.into(),
        error: last,
        ..Fetched::default()
    }
}
pub fn fetch(url: &str, include_text: bool) -> Fetched {
    fetch_with(
        &mut HttpTransport::default(),
        url,
        3,
        6.0,
        include_text,
        super::sleep,
    )
}

#[cfg(test)]
mod http_tests {
    use super::*;
    use std::{
        collections::VecDeque,
        io::Cursor,
        sync::{Arc, Mutex},
    };
    use ureq::unversioned::{
        resolver::{ResolvedSocketAddrs, Resolver},
        transport::{
            Buffers, ConnectionDetails, Connector, LazyBuffers, NextTimeout,
            Transport as WireTransport,
        },
    };

    #[derive(Debug, Default)]
    struct State {
        responses: VecDeque<Vec<u8>>,
        requests: Vec<Vec<u8>>,
        closed: usize,
    }
    #[derive(Debug)]
    struct MemoryConnector(Arc<Mutex<State>>);
    #[derive(Debug)]
    struct MemoryTransport {
        state: Arc<Mutex<State>>,
        index: usize,
        input: Cursor<Vec<u8>>,
        buffers: LazyBuffers,
    }
    impl Connector for MemoryConnector {
        type Out = MemoryTransport;
        fn connect(
            &self,
            details: &ConnectionDetails,
            _: Option<()>,
        ) -> std::result::Result<Option<Self::Out>, ureq::Error> {
            assert!(details.config.proxy().is_none());
            assert_eq!(details.uri.host(), Some("www.ato.gov.au"));
            let mut state = self.0.lock().unwrap();
            let response = state
                .responses
                .pop_front()
                .expect("unexpected HTTP connection");
            let index = state.requests.len();
            state.requests.push(Vec::new());
            Ok(Some(MemoryTransport {
                state: self.0.clone(),
                index,
                input: Cursor::new(response),
                buffers: LazyBuffers::new(4096, 4096),
            }))
        }
    }
    impl WireTransport for MemoryTransport {
        fn buffers(&mut self) -> &mut dyn Buffers {
            &mut self.buffers
        }
        fn transmit_output(
            &mut self,
            amount: usize,
            _: NextTimeout,
        ) -> std::result::Result<(), ureq::Error> {
            self.state.lock().unwrap().requests[self.index]
                .extend_from_slice(&self.buffers.output()[..amount]);
            Ok(())
        }
        fn await_input(&mut self, _: NextTimeout) -> std::result::Result<bool, ureq::Error> {
            let n = self.input.read(self.buffers.input_append_buf())?;
            self.buffers.input_appended(n);
            Ok(n > 0)
        }
        fn is_open(&mut self) -> bool {
            self.input.position() < self.input.get_ref().len() as u64
        }
        // This test substitutes the byte channel only. It does not test TLS or certificates.
        fn is_tls(&self) -> bool {
            true
        }
    }
    impl Drop for MemoryTransport {
        fn drop(&mut self) {
            self.state.lock().unwrap().closed += 1;
        }
    }
    #[derive(Debug)]
    struct MemoryResolver;
    impl Resolver for MemoryResolver {
        fn resolve(
            &self,
            uri: &ureq::http::Uri,
            _: &ureq::config::Config,
            _: NextTimeout,
        ) -> std::result::Result<ResolvedSocketAddrs, ureq::Error> {
            assert_eq!(uri.host(), Some("www.ato.gov.au"));
            let mut addresses = self.empty();
            addresses.push("8.8.8.8:443".parse().unwrap());
            Ok(addresses)
        }
    }
    fn client(response: &[u8]) -> (HttpTransport, Arc<Mutex<State>>) {
        let production = HttpTransport::default();
        let config = production.agent.config().clone();
        assert!(config.proxy().is_none());
        assert_eq!(config.max_redirects(), 0);
        assert!(!config.http_status_as_error());
        assert_eq!(config.timeouts().global, Some(Duration::from_secs(30)));
        let state = Arc::new(Mutex::new(State {
            responses: VecDeque::from([response.to_vec()]),
            ..State::default()
        }));
        (
            HttpTransport {
                agent: ureq::Agent::with_parts(
                    config,
                    MemoryConnector(state.clone()),
                    MemoryResolver,
                ),
            },
            state,
        )
    }
    #[test]
    fn actual_http_stack_preserves_redirects_refusals_and_request_headers() {
        for status in ["302 Found", "403 Forbidden"] {
            let bytes = format!(
                "HTTP/1.1 {status}\r\nLocation: https://www.ato.gov.au/next\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
            );
            let (mut client, state) = client(bytes.as_bytes());
            let response = client.open("https://WWW.ATO.GOV.AU/a?b=c").unwrap();
            assert_eq!(
                response.status,
                if status.starts_with("302") { 302 } else { 403 }
            );
            assert_eq!(response.final_url, "https://WWW.ATO.GOV.AU/a?b=c");
            drop(response);
            drop(client);
            let state = state.lock().unwrap();
            assert_eq!(state.requests.len(), 1);
            assert_eq!(state.closed, 1);
            let request = String::from_utf8(state.requests[0].clone())
                .unwrap()
                .to_ascii_lowercase();
            assert!(request.starts_with("get /a?b=c http/1.1\r\n"));
            assert!(request.contains("\r\nhost: www.ato.gov.au\r\n"));
            assert!(request.contains("\r\naccept-encoding: identity\r\n"));
            assert!(
                request.contains("\r\nuser-agent: australian-accounting-skills source-refresh (")
            );
        }
    }
    #[test]
    fn actual_http_stack_dechunks_but_does_not_decompress_response_content() {
        let wire=b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Encoding: gzip\r\nConnection: close\r\n\r\n3\r\nraw\r\n0\r\n\r\n";
        let (mut client, state) = client(wire);
        let mut response = client.open("https://www.ato.gov.au/a").unwrap();
        let mut body = Vec::new();
        response.body.read_to_end(&mut body).unwrap();
        assert_eq!(body, b"raw");
        assert_eq!(response.header("Content-Encoding"), Some("gzip"));
        drop(response);
        drop(client);
        assert_eq!(state.lock().unwrap().closed, 1);
    }
    #[test]
    fn wire_header_octets_do_not_invalidate_unrelated_content() {
        for (header, allowed) in [
            (&b"X-Unrelated: \x80"[..], true),
            (&b"Content-Encoding: \x80"[..], false),
        ] {
            let mut wire=b"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 4\r\nConnection: close\r\n".to_vec();
            wire.extend_from_slice(header);
            wire.extend_from_slice(b"\r\n\r\npage");
            let (mut client, _) = client(&wire);
            let mut response = client.open("https://www.ato.gov.au/a").unwrap();
            assert!(response.header("X-Unrelated").is_none());
            let encoding = response.header("Content-Encoding").map(str::to_owned);
            let length = response.header("Content-Length").map(str::to_owned);
            let body =
                policy::bounded_body(&mut response.body, encoding.as_deref(), length.as_deref());
            if allowed {
                let body = body.unwrap();
                assert_eq!(body, b"page");
                assert_eq!(
                    content::body_digest(&body, "text/plain", Some("utf-8"))
                        .unwrap()
                        .0,
                    super::super::content_digest("page")
                );
            } else {
                assert!(body.is_err());
            }
        }
    }
}
