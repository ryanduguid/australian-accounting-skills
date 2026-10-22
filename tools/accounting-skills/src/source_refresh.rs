//! Primary-source retrieval, pending candidates and independent human readiness.
pub use crate::source_content::{body_digest, readable_text};
use crate::{Result, source_content as content};
use chrono::{NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    time::Duration,
};
pub mod transport;
pub use transport::{fetch, fetch_with};

pub const DIGEST_FIELD: &str = "content_hash";
pub const DIGEST_KIND_FIELD: &str = "content_hash_covers";
pub const CONTENT_URL_FIELD: &str = "content_url";
pub const UPSTREAM_FIELD: &str = "source_last_modified";
pub const PENDING_FIELD: &str = "pending_review";
pub const REVIEW_REQUIRED_FIELD: &str = "review_required_since";
pub const REVIEWED_FIELD: &str = "reviewed_content";
pub const REVERIFY_FIELD: &str = "reverify_by";
pub const SCHEDULE_FIELD: &str = "manual_review";
pub const UNCHANGED: &str = "unchanged";
pub const CHANGED: &str = "changed";
pub const RECORDED: &str = "recorded";
pub const BASELINE_REQUIRED: &str = "baseline-required";
pub const MISSING: &str = "missing";
pub const BLOCKED: &str = "blocked";
pub const UNREACHABLE: &str = "unreachable";
pub const UNREADABLE: &str = "unreadable";
pub const SCHEDULED: &str = "scheduled";
pub const REVIEW_DUE: &str = "review-due";
pub const OUTCOMES: &[&str] = &[
    CHANGED,
    MISSING,
    BLOCKED,
    UNREACHABLE,
    UNREADABLE,
    REVIEW_DUE,
    BASELINE_REQUIRED,
    SCHEDULED,
    RECORDED,
    UNCHANGED,
];
pub const ACTIONABLE: &[&str] = &[CHANGED, MISSING, UNREADABLE, REVIEW_DUE, BASELINE_REQUIRED];
const BOUNDARY: &str = "\nReadiness concerns recorded source evidence. Verify the exact fact and its effective period at use time; this is not legal, tax or professional approval.\n";

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(default)]
pub struct Fetched {
    pub status: Option<u16>,
    pub final_url: String,
    pub digest: String,
    pub kind: String,
    pub content_type: String,
    pub last_modified: String,
    pub error: String,
    pub text: String,
    pub text_truncated: bool,
}
impl Fetched {
    pub fn reachable(&self) -> bool {
        self.status == Some(200) && self.error.is_empty()
    }
    pub fn readable(&self) -> bool {
        self.reachable() && !self.digest.is_empty()
    }
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Outcome {
    pub skill: String,
    pub title: String,
    pub url: String,
    pub outcome: String,
    pub detail: String,
    pub checked_at: String,
    pub fetched: Fetched,
    #[serde(default)]
    pub next_review: String,
}
impl Outcome {
    pub fn actionable(&self) -> bool {
        ACTIONABLE.contains(&self.outcome.as_str())
    }
    pub fn needs_attention(&self) -> bool {
        self.actionable() || [BLOCKED, UNREACHABLE].contains(&self.outcome.as_str())
    }
}
#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(default)]
pub struct Report {
    pub outcomes: Vec<Outcome>,
    pub written: Vec<PathBuf>,
}
impl Report {
    pub fn by_outcome(&self, name: &str) -> Vec<&Outcome> {
        self.outcomes.iter().filter(|o| o.outcome == name).collect()
    }
    pub fn actionable(&self) -> Vec<&Outcome> {
        self.outcomes.iter().filter(|o| o.actionable()).collect()
    }
    pub fn needs_attention(&self) -> Vec<&Outcome> {
        self.outcomes
            .iter()
            .filter(|o| o.needs_attention())
            .collect()
    }
}
pub fn truth(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::Number(v) => v.as_f64() != Some(0.0),
        Value::String(v) => !v.is_empty(),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
    }
}
pub fn string(value: &Value) -> String {
    match value {
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        Value::String(s) => s.clone(),
        _ => value.to_string(),
    }
}
fn field(record: &Value, key: &str) -> String {
    record.get(key).map(string).unwrap_or_default()
}
pub fn content_digest(text: &str) -> String {
    content::sha256(text.as_bytes())
}

pub fn defrag(url: &str) -> String {
    crate::source_urls::defrag(url)
}

pub fn review_date(schedule: &Value) -> String {
    let due = field(schedule, "next_review");
    if due.len() == 10
        && due.is_ascii()
        && !due.starts_with("0000-")
        && NaiveDate::parse_from_str(&due, "%Y-%m-%d")
            .is_ok_and(|d| d.format("%Y-%m-%d").to_string() == due)
    {
        due
    } else {
        String::new()
    }
}
pub fn iso_day(value: &str) -> String {
    crate::source_dates::iso_day(value)
}
pub fn reverify_passed(record: &Value, today: &str) -> String {
    if !record
        .as_object()
        .is_some_and(|r| r.contains_key(REVERIFY_FIELD))
    {
        return String::new();
    }
    let value = field(record, REVERIFY_FIELD);
    let usable = review_date(&json!({"next_review":value}));
    if !usable.is_empty() && usable.as_str() >= today {
        String::new()
    } else if !usable.is_empty() {
        usable
    } else {
        format!("{}, not a real date", python_repr(&value))
    }
}
fn python_repr(value: &str) -> String {
    let quote = if value.contains('\'') && !value.contains('"') {
        '"'
    } else {
        '\''
    };
    let mut out = String::from(quote);
    for c in value.chars() {
        match c {
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c == quote => {
                out.push('\\');
                out.push(c);
            }
            c if c.is_control() => out.push_str(&format!("\\x{:02x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push(quote);
    out
}
pub fn reverify_note(passed: &str) -> String {
    format!(
        "The recorded fact passed its reverify_by date ({passed}). Read the source, then update checked_at, the fact and reverify_by by hand."
    )
}
pub fn latest_upstream_date(record: &Value, fetched: &Fetched) -> String {
    iso_day(&fetched.last_modified).max(iso_day(&field(record, UPSTREAM_FIELD)))
}
pub fn classify(record: &Value, fetched: &Fetched) -> (String, String) {
    let pair = |name: &str, message: String| (name.to_owned(), message);
    if fetched.error.starts_with("Source policy:") {
        return pair(
            UNREADABLE,
            format!("{} Open the source for manual review.", fetched.error),
        );
    }
    if fetched.reachable() && !fetched.readable() {
        return pair(
            UNREADABLE,
            format!(
                "Retrieved {} but extracted no content to digest. This is a fault in scripts/source_refresh.py, not a finding about the source.",
                if fetched.content_type.is_empty() {
                    "the response"
                } else {
                    &fetched.content_type
                }
            ),
        );
    }
    if !fetched.reachable() {
        let reason = if fetched.error.is_empty() {
            format!(
                "HTTP {}",
                fetched
                    .status
                    .map(|s| s.to_string())
                    .unwrap_or("None".into())
            )
        } else {
            fetched.error.clone()
        };
        return match fetched.status {
            Some(404 | 410) => pair(
                MISSING,
                format!("{reason}. The indexed URL no longer resolves: repoint the record."),
            ),
            Some(401 | 403 | 429 | 451) => pair(
                BLOCKED,
                format!("{reason}. This host refuses automated retrieval: review by hand."),
            ),
            _ => pair(
                UNREACHABLE,
                format!("{reason}. Open the source by hand before relying on the workflow."),
            ),
        };
    }
    let modified = latest_upstream_date(record, fetched);
    let checked = review_date(&json!({"next_review":field(record,"checked_at")}));
    if !modified.is_empty() && !checked.is_empty() && modified > checked {
        return pair(
            CHANGED,
            format!(
                "Published source modification {modified} is later than human review {checked}."
            ),
        );
    }
    let previous = defrag(&field(record, CONTENT_URL_FIELD));
    let current = defrag(&fetched.final_url);
    if !previous.is_empty() && !current.is_empty() && previous != current {
        return pair(
            CHANGED,
            format!("Source destination changed from {previous} to {current}."),
        );
    }
    let stored = field(record, DIGEST_FIELD);
    let same = field(record, DIGEST_KIND_FIELD) == fetched.kind;
    if !stored.is_empty() && same && stored != fetched.digest {
        return pair(
            CHANGED,
            "Readable text changed since the last readable sweep.".into(),
        );
    }
    if stored.is_empty() || previous.is_empty() {
        return pair(BASELINE_REQUIRED,"A readable content or destination baseline is missing. A person must review the pending candidate and explicitly accept its reviewed baseline by hand.".into());
    }
    if !same {
        return pair(
            RECORDED,
            format!(
                "The digest covers a different reading of {}. Human acceptance must bind the new reading to its reviewed baseline.",
                if fetched.content_type.is_empty() {
                    "this content type"
                } else {
                    &fetched.content_type
                }
            ),
        );
    }
    pair(
        UNCHANGED,
        "Readable text and destination are unchanged since the last readable sweep.".into(),
    )
}
pub fn apply_fetch(record: &mut Value, fetched: &Fetched, today: &str) -> Result<()> {
    let outcome = classify(record, fetched).0;
    let modified = latest_upstream_date(record, fetched);
    let record = record
        .as_object_mut()
        .ok_or("source record must be an object")?;
    record.insert("final_url".into(), json!(fetched.final_url));
    record.insert("http_status".into(), json!(fetched.status));
    record.insert("fetched_at".into(), json!(today));
    if fetched.readable() {
        record.insert(UPSTREAM_FIELD.into(), json!(modified));
        if outcome != UNCHANGED || record.contains_key(PENDING_FIELD) {
            if !record.contains_key(PENDING_FIELD) {
                record.insert(REVIEW_REQUIRED_FIELD.into(), json!(today));
            }
            record.insert(PENDING_FIELD.into(),json!({DIGEST_FIELD:fetched.digest,DIGEST_KIND_FIELD:fetched.kind,CONTENT_URL_FIELD:fetched.final_url,"observed_at":today,UPSTREAM_FIELD:modified}));
        }
    }
    for key in [
        DIGEST_FIELD,
        DIGEST_KIND_FIELD,
        CONTENT_URL_FIELD,
        UPSTREAM_FIELD,
    ] {
        record.entry(key).or_insert(json!(""));
    }
    Ok(())
}
pub fn checked_index(path: &Path, skills: &Path) -> Result<()> {
    let linked = |p: &Path| {
        fs::symlink_metadata(p)
            .map(|m| m.file_type().is_symlink())
            .unwrap_or(false)
    };
    if linked(path) || path.parent().is_some_and(linked) {
        return Err("Linked source index or skill directory is unsupported".into());
    }
    if !path.canonicalize()?.starts_with(skills.canonicalize()?) {
        return Err("Source index resolves outside the skills tree".into());
    }
    Ok(())
}
pub fn index_files(skills: &Path) -> Result<Vec<PathBuf>> {
    let mut paths = Vec::new();
    if !skills.is_dir() {
        return Ok(paths);
    }
    for entry in fs::read_dir(skills)? {
        let path = entry?.path().join("sources.json");
        match fs::symlink_metadata(&path) {
            Ok(_) => {
                checked_index(&path, skills)?;
                paths.push(path);
            }
            Err(e)
                if matches!(
                    e.kind(),
                    std::io::ErrorKind::NotFound | std::io::ErrorKind::NotADirectory
                ) => {}
            Err(e) => return Err(e.into()),
        }
    }
    paths.sort_by_key(|p| {
        if cfg!(windows) {
            p.to_string_lossy().to_lowercase()
        } else {
            p.to_string_lossy().into_owned()
        }
    });
    Ok(paths)
}
pub fn load_index(path: &Path, skills: &Path) -> Result<Value> {
    checked_index(path, skills)?;
    Ok(serde_json::from_str(&crate::read_text(path)?)?)
}
pub fn dump_index(path: &Path, payload: &Value, skills: &Path) -> Result<()> {
    checked_index(path, skills)?;
    fs::write(
        path,
        crate::platform_text(&(serde_json::to_string_pretty(payload)? + "\n")),
    )?;
    Ok(())
}

#[derive(Clone)]
pub struct Options {
    pub only_skill: String,
    pub only_url: String,
    pub write: bool,
    pub spacing: f64,
    pub today: String,
}
impl Default for Options {
    fn default() -> Self {
        Self {
            only_skill: String::new(),
            only_url: String::new(),
            write: false,
            spacing: 1.0,
            today: String::new(),
        }
    }
}
fn today(value: &str) -> String {
    if value.is_empty() {
        chrono::Local::now()
            .date_naive()
            .format("%Y-%m-%d")
            .to_string()
    } else {
        value.into()
    }
}
pub fn refresh_with(
    skills: &Path,
    options: &Options,
    mut fetch: impl FnMut(&str) -> Fetched,
    mut sleep: impl FnMut(f64) -> Result<()>,
) -> Result<Report> {
    let stamp = today(&options.today);
    let mut report = Report::default();
    let mut seen = BTreeMap::new();
    let mut touched = Vec::new();
    for path in index_files(skills)? {
        let mut payload = load_index(&path, skills)?;
        if !payload.is_object() {
            return Err(format!(
                "Source index must contain a JSON object: {}",
                path.display()
            )
            .into());
        }
        let skill = payload.get("skill").map(string).unwrap_or_else(|| {
            path.parent()
                .and_then(Path::file_name)
                .unwrap()
                .to_string_lossy()
                .into_owned()
        });
        let Some(records) = payload.get_mut("sources").and_then(Value::as_array_mut) else {
            continue;
        };
        let mut changed = false;
        for record in records.iter_mut().filter(|r| r.is_object()) {
            let url = field(record, "url");
            if (!options.only_skill.is_empty() && skill != options.only_skill)
                || (!options.only_url.is_empty() && url != options.only_url)
                || url.is_empty()
            {
                continue;
            }
            let passed = reverify_passed(record, &stamp);
            let pending = record.get(PENDING_FIELD).is_some();
            let (outcome, detail, fetched, next_review) = if let Some(schedule) =
                record.get(SCHEDULE_FIELD).filter(|s| s.is_object())
            {
                let due = review_date(schedule);
                let late = due.is_empty() || due < stamp;
                let mut detail = if late {
                    format!(
                        "Manual review was due {}. Read the source, then update checked_at and manual_review.next_review by hand.",
                        if due.is_empty() {
                            "with no valid date set"
                        } else {
                            &due
                        }
                    )
                } else if !passed.is_empty() {
                    reverify_note(&passed)
                } else {
                    format!(
                        "Reviewed by hand {}, next review {due}.",
                        field(schedule, "cadence")
                    )
                };
                if late && !passed.is_empty() {
                    detail.push(' ');
                    detail.push_str(&reverify_note(&passed));
                }
                if pending {
                    detail.push_str(
                        " Pending human review: explicitly accept the candidate baseline by hand.",
                    );
                }
                (
                    (if late || !passed.is_empty() || pending {
                        REVIEW_DUE
                    } else {
                        SCHEDULED
                    })
                    .into(),
                    detail,
                    Fetched {
                        status: Some(0),
                        error: "not fetched: reviewed by hand".into(),
                        ..Fetched::default()
                    },
                    due,
                )
            } else {
                let target = defrag(&url);
                if !seen.contains_key(&target) {
                    if !seen.is_empty() && options.spacing != 0.0 {
                        sleep(options.spacing)?;
                    }
                    seen.insert(target.clone(), fetch(&target));
                }
                let fetched = seen[&target].clone();
                let (mut outcome, mut detail) = classify(record, &fetched);
                if options.write {
                    apply_fetch(record, &fetched, &stamp)?;
                    changed = true;
                }
                if record.get(PENDING_FIELD).is_some() {
                    if ![CHANGED, MISSING, UNREADABLE, BASELINE_REQUIRED]
                        .contains(&outcome.as_str())
                    {
                        outcome = REVIEW_DUE.into();
                    }
                    detail.push_str(" Pending human review: a sweep cannot accept a changed or missing baseline.");
                }
                if !passed.is_empty() {
                    if [CHANGED, MISSING, UNREADABLE, BASELINE_REQUIRED].contains(&outcome.as_str())
                    {
                        detail = format!("{detail} {}", reverify_note(&passed));
                    } else if [BLOCKED, UNREACHABLE].contains(&outcome.as_str()) {
                        outcome = REVIEW_DUE.into();
                        detail = format!("{} Retrieval: {detail}", reverify_note(&passed));
                    } else {
                        outcome = REVIEW_DUE.into();
                        detail = reverify_note(&passed);
                    }
                }
                (outcome, detail, fetched, String::new())
            };
            report.outcomes.push(Outcome {
                skill: skill.clone(),
                title: field(record, "title"),
                url,
                outcome,
                detail,
                checked_at: field(record, "checked_at"),
                fetched,
                next_review,
            });
        }
        if changed {
            touched.push((path, payload));
        }
    }
    for (path, payload) in touched {
        dump_index(&path, &payload, skills)?;
        report.written.push(path);
    }
    Ok(report)
}
pub fn sleep(seconds: f64) -> Result<()> {
    std::thread::sleep(Duration::try_from_secs_f64(seconds)?);
    Ok(())
}
pub fn refresh(skills: &Path, options: &Options) -> Result<Report> {
    refresh_with(skills, options, |url| fetch(url, false), sleep)
}

pub fn human_readiness(record: &Value, today: &str) -> (String, String) {
    let fail = |checked: String, message: &str| (checked, message.to_owned());
    if record.get(PENDING_FIELD).is_some() {
        return fail(
            String::new(),
            "Pending human review: explicitly accept the candidate baseline by hand.",
        );
    }
    let checked = review_date(&json!({"next_review":field(record,"checked_at")}));
    if checked.is_empty() || checked.as_str() > today {
        return fail(checked, "Missing, malformed or future human check date.");
    }
    if !record.get("fact").is_some_and(|v| {
        v.as_str()
            .is_some_and(|s| !s.trim_matches(content::space).is_empty())
    }) {
        return fail(checked, "The human review does not record a fact.");
    }
    if let Some(since) = record.get(REVIEW_REQUIRED_FIELD) {
        let since = review_date(&json!({"next_review":since}));
        let binding = record.get(REVIEWED_FIELD);
        if since.is_empty()
            || checked < since
            || !binding.is_some_and(Value::is_object)
            || [
                DIGEST_FIELD,
                DIGEST_KIND_FIELD,
                CONTENT_URL_FIELD,
                "checked_at",
            ]
            .iter()
            .any(|k| binding.and_then(|b| b.get(k)) != record.get(k))
            || binding.and_then(|b| b.get(UPSTREAM_FIELD))
                != Some(
                    record
                        .get(UPSTREAM_FIELD)
                        .unwrap_or(&Value::String(String::new())),
                )
        {
            return fail(
                checked,
                "Human acceptance must bind the digest, reading, destination, published date and current review date.",
            );
        }
    }
    let volatile = record.get("volatile").is_some_and(truth);
    if !reverify_passed(record, today).is_empty()
        || (volatile && record.get(REVERIFY_FIELD).is_none())
    {
        return fail(checked, "The fact needs a current reverify_by date.");
    }
    if volatile {
        let due = review_date(&json!({"next_review":field(record,REVERIFY_FIELD)}));
        if let (Ok(d), Ok(c)) = (
            NaiveDate::parse_from_str(&due, "%Y-%m-%d"),
            NaiveDate::parse_from_str(&checked, "%Y-%m-%d"),
        ) && d.signed_duration_since(c).num_days() > 400
        {
            return fail(
                checked,
                "The volatile fact exceeds the existing 400-day review bound.",
            );
        }
    }
    if field(record, "verification_status") == "indexed-source-discovery-only" {
        return fail(
            checked,
            "The record is discovery-only; a schedule does not establish human review.",
        );
    }
    (checked, String::new())
}
pub fn source_readiness(record: &Value, outcome: &Outcome, today: &str) -> (bool, String) {
    let (checked, problem) = human_readiness(record, today);
    if !problem.is_empty() {
        return (false, problem);
    }
    let modified = latest_upstream_date(record, &outcome.fetched);
    if !modified.is_empty() && modified > checked {
        return (
            false,
            "The source changed after the recorded human review.".into(),
        );
    }
    let schedule = record.get(SCHEDULE_FIELD).filter(|s| !s.is_null());
    if let Some(schedule) = schedule.filter(|s| s.is_object())
        && outcome.outcome == REVIEW_DUE
    {
        let due = review_date(schedule);
        return (
            false,
            format!(
                "Manual review was due {}; complete the human review and update its schedule by hand.",
                if due.is_empty() {
                    "with no valid date set"
                } else {
                    &due
                }
            ),
        );
    }
    if [
        CHANGED,
        MISSING,
        UNREADABLE,
        BASELINE_REQUIRED,
        RECORDED,
        REVIEW_DUE,
    ]
    .contains(&outcome.outcome.as_str())
    {
        return (
            false,
            format!("Retrieval requires review: {}.", outcome.outcome),
        );
    }
    if let Some(schedule) = schedule {
        if !schedule.is_object() {
            return (false, "Malformed manual review schedule.".into());
        }
        let due = review_date(schedule);
        if due.is_empty()
            || due.as_str() < today
            || !schedule.get("cadence").is_some_and(|v| {
                v.as_str()
                    .is_some_and(|s| !s.trim_matches(content::space).is_empty())
            })
        {
            return (
                false,
                "Manual review is overdue or its schedule is malformed.".into(),
            );
        }
        let warning = if [BLOCKED, UNREACHABLE].contains(&outcome.outcome.as_str()) {
            " Retrieval remains unavailable."
        } else {
            ""
        };
        return (
            true,
            format!("READY_MANUAL: human review {checked}, next review {due}.{warning}"),
        );
    }
    if field(record, "verification_status").starts_with("unavailable") {
        return (false, "The record is explicitly unverified.".into());
    }
    if outcome.outcome != UNCHANGED {
        return (
            false,
            format!("Retrieval requires review: {}.", outcome.outcome),
        );
    }
    (
        true,
        format!("READY: human review {checked}; retrieval and destination unchanged."),
    )
}
pub fn render_at(report: &Report, write: bool, swept: &str) -> String {
    let counts = OUTCOMES
        .iter()
        .map(|&n| (n, report.by_outcome(n).len()))
        .collect::<BTreeMap<_, _>>();
    let upcoming = report
        .by_outcome(SCHEDULED)
        .iter()
        .map(|o| o.next_review.clone())
        .min()
        .unwrap_or("none scheduled".into());
    let pages = report
        .outcomes
        .iter()
        .map(|o| defrag(&o.url))
        .collect::<BTreeSet<_>>()
        .len();
    let mut lines = vec![
        "# Primary source sweep".to_owned(),
        String::new(),
        format!(
            "Swept {} records over {pages} distinct pages at {swept}.",
            report.outcomes.len()
        ),
        String::new(),
        format!("- changed: {}", counts[CHANGED]),
        format!(
            "- missing (dead link, repoint the record): {}",
            counts[MISSING]
        ),
        format!(
            "- unreadable (a fault in this script): {}",
            counts[UNREADABLE]
        ),
        format!(
            "- blocked (host refuses automation, review by hand): {}",
            counts[BLOCKED]
        ),
        format!(
            "- unreachable (transport fault, may clear): {}",
            counts[UNREACHABLE]
        ),
        format!(
            "- review-due (manual review overdue or reverify_by passed): {}",
            counts[REVIEW_DUE]
        ),
        format!(
            "- baseline-required (review and record a readable baseline): {}",
            counts[BASELINE_REQUIRED]
        ),
        format!(
            "- scheduled (reviewed by hand, next review {upcoming}): {}",
            counts[SCHEDULED]
        ),
        format!(
            "- baseline recorded or reading changed: {}",
            counts[RECORDED]
        ),
        format!("- unchanged: {}", counts[UNCHANGED]),
        String::new(),
    ];
    let mut attention = report.needs_attention();
    if attention.is_empty() {
        lines.extend([
            "No actionable or network findings were reported.".into(),
            String::new(),
        ]);
    } else {
        lines.extend(
            [
                "A blocked or unreachable source is a fact about the network, not a",
                "finding about this repository, so it is listed but does not fail a",
                "--check run. Everything else asks for an edit here.",
                "",
                "A digest change means the page's readable text moved. It does not",
                "mean a rule changed, and it never changes `checked_at`: read the",
                "source and update the review date by hand if the workflow relies",
                "on material that moved.",
                "",
                "| Outcome | Skill | Source | Reviewed | Upstream | Detail |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
            .map(str::to_owned),
        );
        attention.sort_by(|a, b| (&a.outcome, &a.skill).cmp(&(&b.outcome, &b.skill)));
        for o in attention {
            lines.push(format!(
                "| {} | `{}` | [{}]({}) | {} | {} | {} |",
                o.outcome,
                o.skill,
                o.title,
                o.url,
                o.checked_at,
                if o.fetched.last_modified.is_empty() {
                    "not published"
                } else {
                    &o.fetched.last_modified
                },
                o.detail
            ));
        }
        lines.push(String::new());
    }
    if write && !report.written.is_empty() {
        lines.extend([
            format!("Updated {} index files.", report.written.len()),
            String::new(),
        ]);
    }
    lines.join("\n")
}
pub fn render(report: &Report, write: bool) -> String {
    render_at(
        report,
        write,
        &Utc::now().format("%Y-%m-%d %H:%M UTC").to_string(),
    )
}
pub fn preflight_with(
    skill: &str,
    skills: &Path,
    stamp: &str,
    spacing: f64,
    fetch: impl FnMut(&str) -> Fetched,
    sleep: impl FnMut(f64) -> Result<()>,
) -> (String, u8) {
    let stamp = today(stamp);
    let heading = format!("# Skill source preflight: {skill}\n\nEvaluated: {stamp}\n");
    let fail = |message: &str, code| (format!("{heading}\n{message}\n{BOUNDARY}"), code);
    if skill.is_empty()
        || !skill.as_bytes()[0].is_ascii_lowercase() && !skill.as_bytes()[0].is_ascii_digit()
        || !skill
            .bytes()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == b'-')
    {
        return fail("Invalid exact skill name.", 1);
    }
    let directory = skills.join(skill);
    if !directory
        .canonicalize()
        .ok()
        .zip(skills.canonicalize().ok())
        .is_some_and(|(p, r)| p.starts_with(r))
        || !directory.join("SKILL.md").is_file()
    {
        return fail("No matching skill.", 1);
    }
    let index = directory.join("sources.json");
    if !index.is_file() {
        return fail(
            if directory.join("sources.exempt.json").is_file() {
                "UNAVAILABLE: source exemption requires live manual verification."
            } else {
                "No source index."
            },
            if directory.join("sources.exempt.json").is_file() {
                2
            } else {
                1
            },
        );
    }
    if fs::symlink_metadata(&index).is_ok_and(|m| m.file_type().is_symlink()) {
        return fail("Linked source index is unsupported.", 1);
    }
    let payload = match load_index(&index, skills) {
        Ok(v) => v,
        Err(e) => return fail(&format!("Invalid source index: {e}."), 1),
    };
    let Some(entries) = payload
        .get("sources")
        .and_then(Value::as_array)
        .filter(|v| !v.is_empty())
    else {
        return fail("Incomplete or mismatched source index.", 1);
    };
    if payload.get("skill").and_then(Value::as_str) != Some(skill)
        || entries.iter().any(|r| {
            !r.is_object()
                || !r.get("url").is_some_and(|v| {
                    v.as_str()
                        .is_some_and(|s| !s.trim_matches(content::space).is_empty())
                })
        })
    {
        return fail("Incomplete or mismatched source index.", 1);
    }
    let options = Options {
        only_skill: skill.into(),
        spacing,
        today: stamp.clone(),
        ..Options::default()
    };
    let report = match refresh_with(skills, &options, fetch, sleep) {
        Ok(r) => r,
        Err(e) => return fail(&format!("Invalid source index: {e}."), 1),
    };
    if report.outcomes.len() != entries.len() {
        return fail("Source inventory changed or was incomplete.", 1);
    }
    let (mut lines, mut ready) = (vec![heading], true);
    for (record, outcome) in entries.iter().zip(report.outcomes) {
        let (usable, detail) = source_readiness(record, &outcome, &stamp);
        ready &= usable;
        lines.push(format!("\n- {}: {detail}", outcome.url));
        let manual = record.get(SCHEDULE_FIELD).is_some_and(Value::is_object);
        lines.push(format!(
            "  Human check: {}; retrieval: {}; reverify by: {}.",
            record
                .get("checked_at")
                .map(string)
                .unwrap_or("unknown".into()),
            if manual {
                "not attempted: explicit manual review"
            } else {
                &outcome.outcome
            },
            record
                .get(REVERIFY_FIELD)
                .map(string)
                .unwrap_or("not applicable".into())
        ));
        if manual && field(record, "verification_status").starts_with("unavailable") {
            lines.push("  Recorded automatic retrieval remains unavailable; it was not retried by this preflight.".into());
        }
    }
    (lines.join("\n") + BOUNDARY, if ready { 0 } else { 2 })
}
pub fn preflight(skill: &str, skills: &Path, today: &str, spacing: f64) -> (String, u8) {
    preflight_with(
        skill,
        skills,
        today,
        spacing,
        |url| fetch(url, false),
        sleep,
    )
}

pub fn cli(mut args: impl Iterator<Item = std::ffi::OsString>) -> Result<u8> {
    use std::io::{self, Write};
    let mut root = std::env::current_dir()?;
    let mut options = Options::default();
    let (mut preflight_mode, mut check, mut report_path) = (false, false, None);
    let error = |message: &str| -> Result<u8> {
        io::stderr().write_all(
            crate::platform_text(&format!(
                "accounting-skills source-refresh: error: {message}\n"
            ))
            .as_bytes(),
        )?;
        Ok(2)
    };
    while let Some(arg) = args.next() {
        let name = arg.to_str().ok_or("argument is not Unicode")?;
        match name {
            "--write" => options.write = true,
            "--check" => check = true,
            "--preflight" => preflight_mode = true,
            "--help" | "-h" => {
                io::stdout().write_all(crate::platform_text("usage: accounting-skills source-refresh [--root PATH] [--skill NAME] [--url URL] [--preflight] [--write] [--check] [--report PATH] [--spacing SECONDS]\nRe-fetch indexed primary sources, preserving human acceptance and review dates.\n").as_bytes())?;
                return Ok(0);
            }
            "--root" | "--skill" | "--url" | "--report" | "--spacing" => {
                let Some(value) = args.next() else {
                    return error(&format!("{name} requires a value"));
                };
                match name {
                    "--root" => root = PathBuf::from(value),
                    "--report" => report_path = Some(PathBuf::from(value)),
                    _ => {
                        let value = value.to_str().ok_or("argument is not Unicode")?;
                        match name {
                            "--skill" => options.only_skill = value.into(),
                            "--url" => options.only_url = value.into(),
                            _ => match value.parse() {
                                Ok(seconds) => options.spacing = seconds,
                                Err(_) => return error("--spacing requires a number"),
                            },
                        }
                    }
                }
            }
            _ => return error(&format!("unrecognised argument: {name}")),
        }
    }
    let skills = root.join(".claude/skills");
    let (rendered, code) = if preflight_mode {
        if options.only_skill.is_empty() || options.write || check || !options.only_url.is_empty() {
            return error("--preflight requires --skill and cannot use --write, --check or --url");
        }
        preflight(&options.only_skill, &skills, "", options.spacing)
    } else {
        let report = match refresh(&skills, &options) {
            Ok(report) => report,
            Err(e) => {
                io::stderr().write_all(
                    crate::platform_text(&format!("Invalid source index: {e}.\n")).as_bytes(),
                )?;
                return Ok(1);
            }
        };
        if report.outcomes.is_empty() {
            io::stderr()
                .write_all(crate::platform_text("No source records matched.\n").as_bytes())?;
            return Ok(1);
        }
        (
            render(&report, options.write),
            if check && !report.actionable().is_empty() {
                2
            } else {
                0
            },
        )
    };
    io::stdout().write_all(crate::platform_text(&(rendered.clone() + "\n")).as_bytes())?;
    if let Some(path) = report_path {
        fs::write(path, crate::platform_text(&rendered))?;
    }
    Ok(code)
}
