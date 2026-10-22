//! Interpret a source-sweep report without upgrading unchecked sources to checked.
use crate::{Result, read_text};
use fancy_regex::Regex;
use serde::Serialize;
use std::{
    collections::BTreeMap,
    fs,
    path::{Component, Path, PathBuf},
    sync::LazyLock,
};

const CATEGORIES: [&str; 7] = [
    "changed",
    "missing",
    "unreadable",
    "review-due",
    "baseline-required",
    "blocked",
    "unreachable",
];
static SWEPT: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?m)^Swept (\d+) records over (\d+) distinct pages at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC\.$").unwrap()
});
static COUNT: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?m)^- (changed|missing|unreadable|review-due|baseline-required|blocked|unreachable)[^:]*: (\d+)$").unwrap()
});
static DIGIT: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"^\d$").unwrap());

// Nonnegative report counts need addition and zero checks only. Decimal strings
// preserve Python's large-count semantics without a numeric runtime dependency.
fn decimal(text: &str) -> Result<String> {
    if text.chars().count() > 4300 {
        return Err("report integer exceeds Python's 4300-digit limit".into());
    }
    let mut ascii = String::new();
    for c in text.chars() {
        if c.is_ascii_digit() {
            ascii.push(c);
            continue;
        }
        if !DIGIT.is_match(&c.to_string())? {
            return Err("invalid decimal digit".into());
        }
        let mut start = c as u32;
        while start > 0
            && char::from_u32(start - 1)
                .is_some_and(|prior| DIGIT.is_match(&prior.to_string()).unwrap_or(false))
        {
            start -= 1;
        }
        ascii.push(char::from(b'0' + ((c as u32 - start) % 10) as u8));
    }
    let normal = ascii.trim_start_matches('0');
    Ok(if normal.is_empty() {
        "0".to_owned()
    } else {
        normal.to_owned()
    })
}

fn add(left: &str, right: &str) -> String {
    let mut left = left.bytes().rev();
    let mut right = right.bytes().rev();
    let mut carry = 0;
    let mut out = Vec::new();
    loop {
        let a = left.next();
        let b = right.next();
        if a.is_none() && b.is_none() && carry == 0 {
            break;
        }
        let total = a.map_or(0, |v| v - b'0') + b.map_or(0, |v| v - b'0') + carry;
        out.push(b'0' + total % 10);
        carry = total / 10;
    }
    out.reverse();
    String::from_utf8(out).unwrap()
}

fn timestamp(text: &str, cli: bool) -> Result<[u16; 6]> {
    let pattern = if cli {
        r"^(\d{4})-([0-9]{1,2})-([0-9]{1,2})T([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})Z$"
    } else {
        r"^(\d{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2})$"
    };
    let regex = Regex::new(pattern)?;
    let captures = regex.captures(text)?.ok_or("invalid sweep timestamp")?;
    let mut parts = [0_u16; 6];
    for (index, part) in parts.iter_mut().enumerate().take(if cli { 6 } else { 5 }) {
        *part = decimal(captures.get(index + 1).unwrap().as_str())?.parse()?;
    }
    let [year, month, day, hour, minute, second] = parts;
    let leap = year.is_multiple_of(4) && (!year.is_multiple_of(100) || year.is_multiple_of(400));
    let days = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if leap => 29,
        2 => 28,
        _ => 0,
    };
    if year == 0 || day == 0 || day > days || hour > 23 || minute > 59 || second > 59 {
        return Err("invalid sweep timestamp".into());
    }
    Ok(parts)
}

#[derive(Debug, Serialize)]
pub struct Outcome {
    pub name: &'static str,
    pub comment: String,
}
impl Outcome {
    pub fn lines(&self) -> String {
        format!("outcome={}\ncomment={}\n", self.name, self.comment)
    }
}

pub fn parse_report(text: &str, started: &str) -> Result<BTreeMap<String, String>> {
    if !text.starts_with("# Primary source sweep\n") {
        return Err("the report does not start with the sweep header".into());
    }
    let swept = SWEPT
        .captures(text)?
        .ok_or("the report has no 'Swept N records' line")?;
    let stamp = swept.get(3).unwrap().as_str();
    let mut start = timestamp(started, true)?;
    start[5] = 0;
    if timestamp(stamp, false)? < start {
        return Err(
            format!("the report was written at {stamp} UTC, before this run started").into(),
        );
    }
    let mut counts = BTreeMap::new();
    for capture in COUNT.captures_iter(text) {
        let capture = capture?;
        let name = capture.get(1).unwrap().as_str();
        if counts.contains_key(name) {
            return Err(format!("duplicate count for {name}").into());
        }
        counts.insert(name.to_owned(), decimal(capture.get(2).unwrap().as_str())?);
    }
    let missing: Vec<_> = CATEGORIES
        .iter()
        .filter(|name| !counts.contains_key(**name))
        .copied()
        .collect();
    if !missing.is_empty() {
        return Err(format!("the report has no count for {}", missing.join(", ")).into());
    }
    let records = decimal(swept.get(1).unwrap().as_str())?;
    if records == "0" {
        return Err("the report covers no records".into());
    }
    counts.insert("records".to_owned(), records);
    Ok(counts)
}

pub fn decide(status: i64, counts: &BTreeMap<String, String>) -> Result<Outcome> {
    let mut actionable = "0".to_owned();
    for category in &CATEGORIES[..5] {
        actionable = add(&actionable, counts.get(*category).ok_or("missing count")?);
    }
    if actionable.len() > 4300 {
        return Err("report integer exceeds Python's 4300-digit limit".into());
    }
    if status == 2 {
        if actionable == "0" {
            return Err("exit 2 with a report that lists nothing actionable".into());
        }
        return Ok(Outcome {
            name: "findings",
            comment: format!("{actionable} sources need an edit here."),
        });
    }
    if status != 0 {
        return Err(format!("source_refresh.py exited {status}").into());
    }
    if actionable != "0" {
        return Err(
            format!("exit 0 with a report that lists {actionable} actionable sources").into(),
        );
    }
    let unchecked: Vec<_> = CATEGORIES[5..]
        .iter()
        .filter_map(|category| {
            let count = counts.get(*category)?;
            (count != "0").then(|| format!("{count} {category}"))
        })
        .collect();
    let comment = if unchecked.is_empty() {
        "No actionable source findings were reported.".to_owned()
    } else {
        format!(
            "No indexed source needs an edit here. {} sources could not be checked and are listed in the report.",
            unchecked.join(" and ")
        )
    };
    Ok(Outcome {
        name: "clean",
        comment,
    })
}

fn resolve(path: &Path, links: usize) -> Result<PathBuf> {
    if links > 40 {
        return Err("too many report-path links".into());
    }
    let mut absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir()?.join(path)
    };
    if !absolute.is_absolute() {
        absolute = std::path::absolute(absolute)?;
    }
    let mut resolved = PathBuf::new();
    // Preserve parent components until links have been followed. Windows'
    // absolute-path conversion otherwise collapses link/.. too early.
    for component in absolute.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                resolved.pop();
            }
            Component::Normal(name) => {
                resolved.push(name);
                if let Ok(target) = fs::read_link(&resolved) {
                    let target = if target.is_absolute() {
                        target
                    } else {
                        resolved.parent().unwrap().join(target)
                    };
                    resolved = resolve(&target, links + 1)?;
                } else if resolved.exists() {
                    resolved = fs::canonicalize(&resolved)?;
                }
            }
            other => resolved.push(other.as_os_str()),
        }
    }
    Ok(resolved)
}

fn display(path: &Path) -> String {
    let text = path.to_string_lossy();
    #[cfg(windows)]
    {
        text.strip_prefix(r"\\?\").unwrap_or(&text).to_owned()
    }
    #[cfg(not(windows))]
    {
        text.into_owned()
    }
}

pub fn outcome(status: i64, report: &Path, started: &str, within: &Path) -> Result<Outcome> {
    // The original CLI validates its start time before examining the status.
    timestamp(started, true)?;
    if ![0, 2].contains(&status) {
        return Err(format!("source_refresh.py exited {status}").into());
    }
    let root = resolve(within, 0)?;
    let resolved = resolve(report, 0)?;
    if !resolved.starts_with(root) {
        return Err(format!(
            "report path escapes the working directory: {}",
            display(report)
        )
        .into());
    }
    if !resolved.is_file() {
        return Err(format!(
            "source_refresh.py exited {status} but wrote no report at {}",
            display(&resolved)
        )
        .into());
    }
    decide(status, &parse_report(&read_text(&resolved)?, started)?)
}

pub fn cli(args: impl Iterator<Item = std::ffi::OsString>) -> Result<u8> {
    let mut args = args;
    let (mut status, mut report, mut started) = (None, None, None);
    while let Some(arg) = args.next() {
        let option = arg.to_str().ok_or("invalid sweep-outcome option")?;
        let (option, attached) = option
            .split_once('=')
            .map_or((option, None), |(option, value)| (option, Some(value)));
        let value = attached
            .map(std::ffi::OsString::from)
            .or_else(|| {
                args.next()
                    .filter(|value| !value.as_encoded_bytes().starts_with(b"--"))
            })
            .ok_or("option requires a value")?;
        match option {
            "--status" => status = Some(value.to_str().ok_or("invalid status")?.parse::<i64>()?),
            "--report" => report = Some(PathBuf::from(value)),
            "--started" => started = Some(value.into_string().map_err(|_| "invalid start time")?),
            _ => return Err("unknown sweep-outcome option".into()),
        }
    }
    let result = outcome(
        status.ok_or("--status is required")?,
        &report.ok_or("--report is required")?,
        &started.ok_or("--started is required")?,
        &std::env::current_dir()?,
    )?;
    use std::io::Write;
    std::io::stdout().write_all(crate::platform_text(&result.lines()).as_bytes())?;
    Ok(0)
}
