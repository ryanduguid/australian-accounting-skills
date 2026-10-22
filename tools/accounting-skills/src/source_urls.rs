//! urllib.parse-compatible joining for checked HTTPS redirect targets (PSF-2.0).
#[derive(Default)]
struct Parts {
    scheme: String,
    netloc: String,
    path: String,
    query: Option<String>,
    fragment: Option<String>,
}
fn split(value: &str) -> Parts {
    let clean = value
        .trim_start_matches(|c: char| c <= ' ')
        .replace(['\t', '\r', '\n'], "");
    let mut tail = clean.as_str();
    let mut p = Parts::default();
    if let Some(i) = tail.find(':')
        && tail[..i].starts_with(|c: char| c.is_ascii_alphabetic())
        && tail[..i]
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || "+-.".contains(c))
    {
        p.scheme = tail[..i].to_ascii_lowercase();
        tail = &tail[i + 1..];
    }
    if let Some(authority) = tail.strip_prefix("//") {
        let end = authority.find(['/', '?', '#']).unwrap_or(authority.len());
        p.netloc = authority[..end].into();
        tail = &authority[end..];
    }
    if let Some((head, frag)) = tail.split_once('#') {
        p.fragment = Some(frag.into());
        tail = head;
    }
    if let Some((head, query)) = tail.split_once('?') {
        p.query = Some(query.into());
        tail = head;
    }
    p.path = tail.into();
    p
}
fn unsplit(p: Parts) -> String {
    let mut out = String::new();
    if !p.scheme.is_empty() {
        out.push_str(&p.scheme);
        out.push(':');
    }
    if !p.netloc.is_empty() || p.scheme == "https" || p.scheme == "http" {
        out.push_str("//");
        out.push_str(&p.netloc);
        if !p.path.is_empty() && !p.path.starts_with('/') {
            out.push('/');
        }
    }
    out.push_str(&p.path);
    if let Some(q) = p.query {
        out.push('?');
        out.push_str(&q);
    }
    if let Some(f) = p.fragment {
        out.push('#');
        out.push_str(&f);
    }
    out
}
pub fn defrag(value: &str) -> String {
    if !value.contains('#') {
        return value.into();
    }
    let mut p = split(value);
    p.fragment = None;
    unsplit(p)
}
pub fn join(base: &str, reference: &str) -> String {
    if base.is_empty() {
        return reference.into();
    }
    if reference.is_empty() {
        return base.into();
    }
    let b = split(base);
    let mut p = split(reference);
    if p.scheme.is_empty() {
        p.scheme = b.scheme.clone();
    }
    if p.scheme != b.scheme || !["https", "http", ""].contains(&p.scheme.as_str()) {
        return reference.into();
    }
    if !p.netloc.is_empty() {
        return unsplit(p);
    }
    p.netloc = b.netloc;
    if p.path.is_empty() {
        p.path = b.path;
        if p.query.is_none() {
            p.query = b.query;
            if p.fragment.is_none() {
                p.fragment = b.fragment;
            }
        }
        return unsplit(p);
    }
    let mut segments: Vec<&str> = if p.path.starts_with('/') {
        p.path.split('/').collect()
    } else {
        let mut parts: Vec<_> = b.path.split('/').collect();
        if parts.last() != Some(&"") {
            parts.pop();
        }
        parts.extend(p.path.split('/'));
        let len = parts.len();
        parts
            .into_iter()
            .enumerate()
            .filter(|(i, s)| *i == 0 || *i + 1 == len || !s.is_empty())
            .map(|(_, s)| s)
            .collect()
    };
    let ending = segments.last().copied().unwrap_or("");
    let mut resolved = Vec::new();
    for part in segments.drain(..) {
        match part {
            ".." => {
                resolved.pop();
            }
            "." => {}
            _ => resolved.push(part),
        }
    }
    if [".", ".."].contains(&ending) {
        resolved.push("");
    }
    let path = resolved.join("/");
    p.path = if path.is_empty() { "/".into() } else { path };
    unsplit(p)
}
