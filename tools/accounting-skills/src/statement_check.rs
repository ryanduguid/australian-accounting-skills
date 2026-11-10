// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! Ties out bank and card statement lines in exact cents, so no model does the arithmetic.
//!
//! The input carries amounts, balances and line references only, never descriptions,
//! so nothing this command prints can quote statement text.
use crate::{Result, platform_text, read_text};
use chrono::{Days, NaiveDate};
use serde::Deserialize;
use std::{
    collections::BTreeSet,
    ffi::OsString,
    io::{self, Write},
    path::Path,
};

const USAGE: &str = "usage: accounting-skills statement-check FILE";
/// How many days before its period a line may be dated. A card prints the transaction date
/// of a purchase it posts within the period; anything earlier breaks.
const EARLY_DAYS: u64 = 31;

#[derive(Deserialize, Clone, Copy)]
#[serde(rename_all = "lowercase")]
enum Direction {
    /// A bank account: credits raise the printed balance.
    Deposit,
    /// A card or loan printed as an amount owed: debits raise the printed balance.
    Owed,
}

#[derive(Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
enum SignFrom {
    Column,
    Balance,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Input {
    direction: Direction,
    statements: Vec<Statement>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Statement {
    id: String,
    period_start: String,
    period_end: String,
    opening: String,
    closing: String,
    printed_credits: Option<Vec<String>>,
    printed_debits: Option<Vec<String>>,
    pages: Vec<Page>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Page {
    page: String,
    brought_forward: Option<String>,
    carried_forward: Option<String>,
    printed_credits: Option<Vec<String>>,
    printed_debits: Option<Vec<String>>,
    lines: Vec<Line>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Line {
    line: String,
    date: String,
    debit: Option<String>,
    credit: Option<String>,
    balance: Option<String>,
    sign_from: SignFrom,
}

/// A plain decimal with at most 15 whole digits and 0 or 2 decimal places, in cents.
/// Thousands separators, signs other than a leading minus, and brackets are refused.
fn cents(text: &str, at: &str) -> Result<i128> {
    let (negative, digits) = text
        .strip_prefix('-')
        .map_or((false, text), |rest| (true, rest));
    let (whole, fraction) = digits.split_once('.').unwrap_or((digits, "00"));
    if whole.is_empty()
        || whole.len() > 15
        || fraction.len() != 2
        || !whole
            .bytes()
            .chain(fraction.bytes())
            .all(|b| b.is_ascii_digit())
    {
        return Err(format!("{at}: {text:?} is not a plain amount such as -1234.56").into());
    }
    let value = format!("{whole}{fraction}").parse::<i128>()?;
    Ok(if negative { -value } else { value })
}

/// A debit or credit: the column gives the sign, so a minus sign is refused, even on zero.
fn unsigned(text: &str, at: &str) -> Result<i128> {
    if text.starts_with('-') {
        return Err(
            format!("{at}: debit and credit are unsigned; the column gives the sign").into(),
        );
    }
    cents(text, at)
}

fn optional(text: Option<&str>, at: &str) -> Result<Option<i128>> {
    text.map(|text| cents(text, at)).transpose()
}

/// The sum of the printed figures for one side, such as purchases, cash advances and fees.
fn printed_total(parts: Option<&[String]>, at: &str) -> Result<Option<i128>> {
    let Some(parts) = parts else {
        return Ok(None);
    };
    if parts.is_empty() {
        return Err(
            format!("{at}: list at least one printed figure, or leave the field out").into(),
        );
    }
    let mut total = 0;
    for part in parts {
        total += unsigned(part, at)?;
    }
    Ok(Some(total))
}

fn date(text: &str, at: &str) -> Result<NaiveDate> {
    NaiveDate::parse_from_str(text, "%Y-%m-%d")
        .ok()
        .filter(|parsed| parsed.format("%Y-%m-%d").to_string() == text)
        .ok_or_else(|| format!("{at}: {text:?} is not a date in the form 2026-01-31").into())
}

/// A statement, page or line reference: a break must name something a person can find.
fn reference<'a>(text: &'a str, what: &str, seen: &mut BTreeSet<&'a str>, at: &str) -> Result<()> {
    if text.trim().is_empty() {
        return Err(format!("{at}: {what} reference is empty").into());
    }
    if !seen.insert(text) {
        return Err(format!("{at}: {what} {text} appears more than once").into());
    }
    Ok(())
}

fn money(value: i128) -> String {
    let sign = if value < 0 { "-" } else { "" };
    let value = value.abs();
    format!("{sign}{}.{:02}", value / 100, value % 100)
}

/// One statement after its own checks: the figures continuity needs.
struct Checked {
    start: NaiveDate,
    end: NaiveDate,
    opening: i128,
    closing: i128,
    /// The running balance after each line, with the line's date, in statement order.
    after: Vec<(NaiveDate, i128)>,
}

#[derive(Default)]
struct Report {
    breaks: Vec<String>,
    overlaps: Vec<String>,
    lines: usize,
    balances: usize,
    totals: usize,
    links: usize,
}

impl Report {
    fn differs(&mut self, at: &str, what: &str, printed: i128, label: &str, other: i128) {
        if printed != other {
            self.breaks.push(format!(
                "BREAK {at}: {what} {}, {label} {}",
                money(printed),
                money(other)
            ));
        }
    }

    /// Compares a printed balance with the one computed from the lines.
    fn balance(&mut self, at: &str, what: &str, printed: i128, computed: i128) {
        self.balances += 1;
        self.differs(at, what, printed, "computed", computed);
    }

    /// Compares a printed gross total, where one is printed, with the extracted lines.
    fn total(&mut self, at: &str, side: &str, printed: Option<i128>, extracted: i128) {
        if let Some(printed) = printed {
            self.totals += 1;
            self.differs(
                at,
                &format!("printed {side}"),
                printed,
                "extracted",
                extracted,
            );
        }
    }
}

/// The running state through one statement.
struct Running {
    balance: i128,
    /// Whether the balance was just set from a printed figure, which a sign taken from the
    /// balance needs on the line before.
    printed_before: bool,
    after: Vec<(NaiveDate, i128)>,
}

/// The statement a page belongs to, as its lines need it.
struct Period<'a> {
    id: &'a str,
    start: NaiveDate,
    end: NaiveDate,
    direction: Direction,
}

/// Checks one page and returns its extracted gross credits and debits.
fn check_page(
    page: &Page,
    period: &Period,
    running: &mut Running,
    report: &mut Report,
) -> Result<(i128, i128)> {
    let at = format!("{} page {}", period.id, page.page);
    if let Some(forward) = optional(
        page.brought_forward.as_deref(),
        &format!("{at} brought_forward"),
    )? {
        report.balance(&at, "brought forward", forward, running.balance);
        running.balance = forward;
        running.printed_before = true;
    }
    let earliest = period.start.checked_sub_days(Days::new(EARLY_DAYS));
    let (mut credits, mut debits) = (0_i128, 0_i128);
    let mut seen = BTreeSet::new();
    for line in &page.lines {
        reference(&line.line, "line", &mut seen, &at)?;
        let at = format!("{at} line {}", line.line);
        let when = date(&line.date, &format!("{at} date"))?;
        if when > period.end {
            report.breaks.push(format!(
                "BREAK {at}: dated {when}, after the period ends {}",
                period.end
            ));
        } else if earliest.is_some_and(|earliest| when < earliest) {
            report.breaks.push(format!(
                "BREAK {at}: dated {when}, more than {EARLY_DAYS} days before the period starts {}",
                period.start
            ));
        }
        let (debit, credit) = match (line.debit.as_deref(), line.credit.as_deref()) {
            (Some(debit), None) => (unsigned(debit, &format!("{at} debit"))?, 0),
            (None, Some(credit)) => (0, unsigned(credit, &format!("{at} credit"))?),
            _ => return Err(format!("{at}: give exactly one of debit and credit").into()),
        };
        debits += debit;
        credits += credit;
        running.balance += match period.direction {
            Direction::Deposit => credit - debit,
            Direction::Owed => debit - credit,
        };
        let balance = optional(line.balance.as_deref(), &format!("{at} balance"))?;
        if line.sign_from == SignFrom::Balance && !(running.printed_before && balance.is_some()) {
            report.breaks.push(format!(
                "BREAK {at}: sign taken from the balance without printed balances on this line and the one before"
            ));
        }
        if let Some(balance) = balance {
            report.balance(&at, "printed balance", balance, running.balance);
            running.balance = balance;
        }
        running.printed_before = balance.is_some();
        running.after.push((when, running.balance));
        report.lines += 1;
    }
    if let Some(forward) = optional(
        page.carried_forward.as_deref(),
        &format!("{at} carried_forward"),
    )? {
        report.balance(&at, "carried forward", forward, running.balance);
        running.balance = forward;
        running.printed_before = true;
    }
    let printed = printed_total(
        page.printed_credits.as_deref(),
        &format!("{at} printed_credits"),
    )?;
    report.total(&at, "credits", printed, credits);
    let printed = printed_total(
        page.printed_debits.as_deref(),
        &format!("{at} printed_debits"),
    )?;
    report.total(&at, "debits", printed, debits);
    Ok((credits, debits))
}

fn check_statement(
    statement: &Statement,
    direction: Direction,
    report: &mut Report,
) -> Result<Checked> {
    let id = statement.id.as_str();
    let start = date(&statement.period_start, &format!("{id} period_start"))?;
    let end = date(&statement.period_end, &format!("{id} period_end"))?;
    if end < start {
        return Err(format!("{id}: period_end is before period_start").into());
    }
    let opening = cents(&statement.opening, &format!("{id} opening"))?;
    let closing = cents(&statement.closing, &format!("{id} closing"))?;
    let period = Period {
        id,
        start,
        end,
        direction,
    };
    let mut running = Running {
        balance: opening,
        printed_before: true,
        after: Vec::new(),
    };
    let (mut credits, mut debits) = (0_i128, 0_i128);
    let mut seen = BTreeSet::new();
    for page in &statement.pages {
        reference(&page.page, "page", &mut seen, id)?;
        let (page_credits, page_debits) = check_page(page, &period, &mut running, report)?;
        credits += page_credits;
        debits += page_debits;
    }
    report.balance(id, "closing", closing, running.balance);
    let printed = printed_total(
        statement.printed_credits.as_deref(),
        &format!("{id} printed_credits"),
    )?;
    report.total(id, "credits", printed, credits);
    let printed = printed_total(
        statement.printed_debits.as_deref(),
        &format!("{id} printed_debits"),
    )?;
    report.total(id, "debits", printed, debits);
    Ok(Checked {
        start,
        end,
        opening,
        closing,
        after: running.after,
    })
}

/// Each statement's opening must follow from the one before: its closing where the
/// periods abut, or its running balance before the overlap where they overlap.
fn check_continuity(ids: (&str, &str), before: &Checked, next: &Checked, report: &mut Report) {
    let at = format!("{} to {}", ids.0, ids.1);
    let following = before.end.checked_add_days(Days::new(1));
    if Some(next.start) > following {
        report.breaks.push(format!(
            "BREAK {at}: gap, {} ends {} and {} starts {}",
            ids.0, before.end, ids.1, next.start
        ));
        return;
    }
    let expected = if Some(next.start) == following {
        before.closing
    } else {
        // The balance before the overlap is only known when the lines run in date order.
        if !before.after.windows(2).all(|pair| pair[0].0 <= pair[1].0) {
            report.breaks.push(format!(
                "BREAK {at}: overlap cannot be placed, {} lines are not in date order",
                ids.0
            ));
            return;
        }
        before
            .after
            .iter()
            .rev()
            .find(|(when, _)| *when < next.start)
            .map_or(before.opening, |(_, running)| *running)
    };
    report.links += 1;
    report.differs(&at, "opening", next.opening, "computed", expected);
}

fn check(input: &Input) -> Result<Report> {
    if input.statements.is_empty() {
        return Err("no statements: the input must hold at least one".into());
    }
    let mut report = Report::default();
    let mut ids = BTreeSet::new();
    let mut checked: Vec<Checked> = Vec::new();
    for statement in &input.statements {
        reference(&statement.id, "statement", &mut ids, "statements")?;
        let current = check_statement(statement, input.direction, &mut report)?;
        if checked
            .last()
            .is_some_and(|before| current.start < before.start)
        {
            return Err(format!("{}: statements must be in period order", statement.id).into());
        }
        checked.push(current);
    }
    for (index, next) in checked.iter().enumerate().skip(1) {
        let next_id = &input.statements[index].id;
        for (earlier, before) in checked[..index].iter().enumerate() {
            if before.end < next.start {
                continue;
            }
            let before_id = &input.statements[earlier].id;
            report.overlaps.push(format!(
                "OVERLAP {before_id} and {next_id}: {} to {}",
                next.start,
                before.end.min(next.end)
            ));
            if next.start == before.start || next.end <= before.end {
                report.breaks.push(format!(
                    "BREAK {before_id} and {next_id}: one period lies wholly within the other"
                ));
            }
        }
        let before_id = &input.statements[index - 1].id;
        check_continuity((before_id, next_id), &checked[index - 1], next, &mut report);
    }
    Ok(report)
}

/// Runs the `statement-check` command: exit 0 when everything ties, 2 on any break.
pub fn cli(args: impl Iterator<Item = OsString>) -> Result<u8> {
    let args: Vec<_> = args.collect();
    let [path] = args.as_slice() else {
        return Err(USAGE.into());
    };
    let path = Path::new(path);
    let text = read_text(path).map_err(|error| format!("{}: {error}", path.display()))?;
    // Windows PowerShell 5 writes a byte-order mark; it carries no figures.
    let text = text.strip_prefix('\u{feff}').unwrap_or(&text);
    let input: Input =
        serde_json::from_str(text).map_err(|error| format!("{}: {error}", path.display()))?;
    let report = check(&input)?;
    let mut out = String::new();
    for line in report.breaks.iter().chain(&report.overlaps) {
        out.push_str(line);
        out.push('\n');
    }
    let code = if report.breaks.is_empty() {
        out.push_str(&format!(
            "PASS {} statements, {} lines; compared {} printed balances, {} printed totals, {} statement links\n",
            input.statements.len(),
            report.lines,
            report.balances,
            report.totals,
            report.links
        ));
        0
    } else {
        out.push_str(&format!("FAIL {} breaks\n", report.breaks.len()));
        2
    };
    io::stdout().write_all(platform_text(&out).as_bytes())?;
    Ok(code)
}

#[cfg(test)]
mod tests {
    use super::{Input, cents, check};
    use serde_json::{Value, json};

    fn breaks(input: &Value) -> Vec<String> {
        let input: Input = serde_json::from_value(input.clone()).unwrap();
        check(&input).unwrap().breaks
    }

    fn line(
        line: &str,
        date: &str,
        debit: Option<&str>,
        credit: Option<&str>,
        balance: Option<&str>,
    ) -> Value {
        json!({"line": line, "date": date, "debit": debit, "credit": credit, "balance": balance, "sign_from": "column"})
    }

    /// A fabricated 2 page bank statement that ties on every check.
    fn bank() -> Value {
        json!({"direction": "deposit", "statements": [{
        "id": "S1", "period_start": "2026-01-01", "period_end": "2026-01-31",
        "opening": "1000.00", "closing": "1150.00",
        "printed_credits": ["300.00"], "printed_debits": ["150.00"],
        "pages": [
            {"page": "1", "brought_forward": "1000.00", "carried_forward": "1100.00",
             "printed_credits": ["200.00"], "printed_debits": ["100.00"], "lines": [
                line("1", "2026-01-03", None, Some("200.00"), Some("1200.00")),
                line("2", "2026-01-09", Some("100.00"), None, Some("1100.00"))]},
            {"page": "2", "brought_forward": "1100.00", "carried_forward": "1150.00", "lines": [
                line("1", "2026-01-20", Some("50.00"), None, None),
                line("2", "2026-01-28", None, Some("100.00"), Some("1150.00"))]}
        ]}]})
    }

    #[test]
    fn a_statement_that_ties_has_no_breaks() {
        assert_eq!(breaks(&bank()), Vec::<String>::new());
    }

    #[test]
    fn the_first_broken_running_balance_is_named_once() {
        let mut input = bank();
        input["statements"][0]["pages"][0]["lines"][1]["debit"] = json!("90.00");
        assert_eq!(
            breaks(&input),
            [
                "BREAK S1 page 1 line 2: printed balance 1100.00, computed 1110.00",
                "BREAK S1 page 1: printed debits 100.00, extracted 90.00",
                "BREAK S1: printed debits 150.00, extracted 140.00",
            ]
        );
    }

    #[test]
    fn omissions_that_cancel_fail_the_gross_totals() {
        // A card printed with no running balances: the missed 40.00 purchase and
        // 40.00 refund leave the net movement, and so the closing balance, unchanged.
        let input = json!({"direction": "owed", "statements": [{
            "id": "C1", "period_start": "2026-03-01", "period_end": "2026-03-31",
            "opening": "500.00", "closing": "620.00",
            "printed_credits": ["240.00"], "printed_debits": ["360.00"],
            "pages": [{"page": "1", "lines": [
                line("1", "2026-03-04", Some("320.00"), None, None),
                line("2", "2026-03-15", None, Some("200.00"), None)]}]}]});
        assert_eq!(
            breaks(&input),
            [
                "BREAK C1: printed credits 240.00, extracted 200.00",
                "BREAK C1: printed debits 360.00, extracted 320.00",
            ]
        );
    }

    #[test]
    fn printed_movement_with_no_extracted_lines_fails() {
        let input = json!({"direction": "deposit", "statements": [{
            "id": "S1", "period_start": "2026-01-01", "period_end": "2026-01-31",
            "opening": "100.00", "closing": "100.00",
            "printed_credits": ["25.00"], "printed_debits": ["25.00"], "pages": []}]});
        assert_eq!(breaks(&input).len(), 2);
    }

    #[test]
    fn a_card_in_credit_crosses_zero_in_the_owed_direction() {
        let input = json!({"direction": "owed", "statements": [{
            "id": "C1", "period_start": "2026-12-15", "period_end": "2027-01-14",
            "opening": "-35.00", "closing": "84.50",
            "pages": [{"page": "1", "lines": [
                line("1", "2026-12-13", Some("20.00"), None, Some("-15.00")),
                line("2", "2026-12-30", Some("99.50"), None, Some("84.50"))]}]}]});
        assert_eq!(breaks(&input), Vec::<String>::new());
        let mut wrong_way = input.clone();
        wrong_way["direction"] = json!("deposit");
        assert_eq!(
            breaks(&wrong_way)[0],
            "BREAK C1 page 1 line 1: printed balance -15.00, computed -55.00"
        );
    }

    #[test]
    fn a_sign_from_the_balance_needs_both_printed_balances() {
        let mut input = bank();
        input["statements"][0]["pages"][0]["lines"][1]["sign_from"] = json!("balance");
        assert_eq!(breaks(&input), Vec::<String>::new());
        input["statements"][0]["pages"][1]["lines"][1]["sign_from"] = json!("balance");
        assert_eq!(
            breaks(&input),
            [
                "BREAK S1 page 2 line 2: sign taken from the balance without printed balances on this line and the one before"
            ]
        );
    }

    #[test]
    fn overlapping_statements_continue_from_the_balance_before_the_overlap() {
        let mut input = bank();
        let next = json!({"id": "S2", "period_start": "2026-01-25", "period_end": "2026-02-24",
            "opening": "1050.00", "closing": "1050.00", "pages": []});
        input["statements"].as_array_mut().unwrap().push(next);
        // The last S1 line dated before 25 January is the 20 January debit, leaving 1050.00.
        assert_eq!(breaks(&input), Vec::<String>::new());
        input["statements"][1]["opening"] = json!("1150.00");
        input["statements"][1]["closing"] = json!("1150.00");
        assert_eq!(
            breaks(&input),
            ["BREAK S1 to S2: opening 1150.00, computed 1050.00"]
        );
        input["statements"][1]["period_start"] = json!("2026-02-02");
        assert_eq!(
            breaks(&input),
            ["BREAK S1 to S2: gap, S1 ends 2026-01-31 and S2 starts 2026-02-02"]
        );
    }

    #[test]
    fn abutting_statements_continue_from_the_closing_balance() {
        let mut input = bank();
        let next = json!({"id": "S2", "period_start": "2026-02-01", "period_end": "2026-02-28",
            "opening": "1150.00", "closing": "1150.00", "pages": []});
        input["statements"].as_array_mut().unwrap().push(next);
        assert_eq!(breaks(&input), Vec::<String>::new());
    }

    #[test]
    fn amounts_are_plain_exact_decimals() {
        assert_eq!(cents("-1234.56", "x").unwrap(), -123_456);
        assert_eq!(cents("7", "x").unwrap(), 700);
        for refused in [
            "1,234.56",
            "(30.00)",
            "+5.00",
            "1.5",
            "",
            "-",
            "1e3",
            "12.345",
            "1234567890123456",
        ] {
            assert!(cents(refused, "x").is_err(), "{refused}");
        }
    }

    #[test]
    fn malformed_input_is_refused_not_skipped() {
        let mut input = bank();
        input["statements"][0]["pages"][0]["lines"][0]["description"] = json!("text");
        assert!(serde_json::from_value::<Input>(input).is_err());
        let mut both = bank();
        both["statements"][0]["pages"][0]["lines"][0]["debit"] = json!("1.00");
        let both: Input = serde_json::from_value(both).unwrap();
        assert!(check(&both).is_err());
        let mut date = bank();
        date["statements"][0]["pages"][0]["lines"][0]["date"] = json!("03/01/2026");
        let date: Input = serde_json::from_value(date).unwrap();
        assert!(check(&date).is_err());
    }
}
