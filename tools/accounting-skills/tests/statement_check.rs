// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! The `statement-check` command as the statement-to-csv skill runs it: its exit codes and output.
//! Every figure is fabricated.
use serde_json::{Value, json};
use std::{fs, process::Command};
use tempfile::tempdir;

struct Run {
    code: Option<i32>,
    stdout: Vec<String>,
    stderr: String,
}

fn run_bytes(bytes: &[u8]) -> Run {
    let directory = tempdir().unwrap();
    let path = directory.path().join("lines.json");
    fs::write(&path, bytes).unwrap();
    command(&[path.to_str().unwrap()])
}

fn run(input: &Value) -> Run {
    run_bytes(input.to_string().as_bytes())
}

fn command(args: &[&str]) -> Run {
    let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .arg("statement-check")
        .args(args)
        .output()
        .unwrap();
    Run {
        code: output.status.code(),
        stdout: String::from_utf8(output.stdout)
            .unwrap()
            .lines()
            .map(str::to_owned)
            .collect(),
        stderr: String::from_utf8(output.stderr).unwrap(),
    }
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

/// One January bank statement, one page, 3 lines with balances on 2 of them.
fn january(id: &str) -> Value {
    json!({"id": id, "period_start": "2026-01-01", "period_end": "2026-01-31",
        "opening": "1000.00", "closing": "1250.00",
        "printed_credits": ["300.00"], "printed_debits": ["50.00"],
        "pages": [{"page": "1", "lines": [
            line("1", "2026-01-03", None, Some("200.00"), Some("1200.00")),
            line("2", "2026-01-20", Some("50.00"), None, None),
            line("3", "2026-01-28", None, Some("100.00"), Some("1250.00"))]}]})
}

fn deposit(statements: Vec<Value>) -> Value {
    json!({"direction": "deposit", "statements": statements})
}

fn assert_refused(run: &Run, message: &str) {
    assert_eq!(run.code, Some(1), "{}", run.stderr);
    assert!(run.stdout.is_empty());
    assert!(run.stderr.starts_with("FAIL "), "{}", run.stderr);
    assert!(run.stderr.contains(message), "{}", run.stderr);
}

#[test]
fn a_tie_exits_0_and_names_the_checks_that_ran() {
    let run = run(&deposit(vec![january("S1")]));
    assert_eq!(run.code, Some(0));
    assert_eq!(
        run.stdout,
        [
            "PASS 1 statements, 3 lines; compared 3 printed balances, 2 printed totals, 0 statement links"
        ]
    );
    assert!(run.stderr.is_empty());
}

#[test]
fn a_pass_without_printed_figures_says_nothing_was_compared() {
    let mut statement = january("S1");
    statement["printed_credits"] = Value::Null;
    statement["printed_debits"] = Value::Null;
    for line in statement["pages"][0]["lines"].as_array_mut().unwrap() {
        line["balance"] = Value::Null;
    }
    let run = run(&deposit(vec![statement]));
    assert_eq!(run.code, Some(0));
    assert_eq!(
        run.stdout,
        [
            "PASS 1 statements, 3 lines; compared 1 printed balances, 0 printed totals, 0 statement links"
        ]
    );
}

#[test]
fn a_break_exits_2_with_one_line_per_difference() {
    let mut statement = january("S1");
    statement["pages"][0]["lines"][1]["debit"] = json!("40.00");
    let run = run(&deposit(vec![statement]));
    assert_eq!(run.code, Some(2));
    assert_eq!(
        run.stdout,
        [
            "BREAK S1 page 1 line 3: printed balance 1250.00, computed 1260.00",
            "BREAK S1: printed debits 50.00, extracted 40.00",
            "FAIL 2 breaks",
        ]
    );
}

#[test]
fn printed_totals_may_be_listed_in_parts() {
    let mut statement = january("S1");
    statement["printed_credits"] = json!(["200.00", "100.00"]);
    assert_eq!(run(&deposit(vec![statement.clone()])).code, Some(0));
    statement["printed_credits"] = json!(["200.00", "90.00"]);
    let broken = run(&deposit(vec![statement.clone()]));
    assert_eq!(
        broken.stdout[0],
        "BREAK S1: printed credits 290.00, extracted 300.00"
    );
    statement["printed_credits"] = json!([]);
    assert_refused(
        &run(&deposit(vec![statement])),
        "list at least one printed figure",
    );
}

#[test]
fn malformed_input_exits_1() {
    assert_refused(&run_bytes(b"{\"direction\": \"deposit\","), "lines.json");
    let mut amount = january("S1");
    amount["pages"][0]["lines"][0]["credit"] = json!("1,200.00");
    assert_refused(&run(&deposit(vec![amount])), "is not a plain amount");
    let mut zero = january("S1");
    zero["pages"][0]["lines"][1]["debit"] = json!("-0.00");
    assert_refused(&run(&deposit(vec![zero])), "unsigned");
}

#[test]
fn no_argument_or_a_missing_file_exits_1() {
    assert_refused(
        &command(&[]),
        "usage: accounting-skills statement-check FILE",
    );
    let directory = tempdir().unwrap();
    let missing = directory.path().join("absent.json");
    assert_refused(&command(&[missing.to_str().unwrap()]), "absent.json");
}

#[test]
fn a_byte_order_mark_is_ignored() {
    let mut bytes = "\u{feff}".as_bytes().to_vec();
    bytes.extend(deposit(vec![january("S1")]).to_string().as_bytes());
    assert_eq!(run_bytes(&bytes).code, Some(0));
}

#[test]
fn an_empty_input_is_refused() {
    assert_refused(&run(&deposit(vec![])), "no statements");
}

#[test]
fn a_repeated_statement_is_refused_or_broken() {
    assert_refused(
        &run(&deposit(vec![january("S1"), january("S1")])),
        "statement S1 appears more than once",
    );
    let run = run(&deposit(vec![january("S1"), january("S2")]));
    assert_eq!(run.code, Some(2));
    assert_eq!(
        run.stdout,
        [
            "BREAK S1 and S2: one period lies wholly within the other",
            "OVERLAP S1 and S2: 2026-01-01 to 2026-01-31",
            "FAIL 1 breaks",
        ]
    );
}

#[test]
fn a_contained_statement_breaks_and_a_partial_overlap_is_reported() {
    let mut contained = january("S2");
    contained["period_start"] = json!("2026-01-10");
    contained["period_end"] = json!("2026-01-20");
    contained["opening"] = json!("1200.00");
    contained["closing"] = json!("1200.00");
    contained["printed_credits"] = Value::Null;
    contained["printed_debits"] = Value::Null;
    contained["pages"] = json!([]);
    let run_contained = run(&deposit(vec![january("S1"), contained.clone()]));
    assert_eq!(run_contained.code, Some(2));
    assert!(
        run_contained
            .stdout
            .contains(&"BREAK S1 and S2: one period lies wholly within the other".to_owned())
    );
    assert!(
        run_contained
            .stdout
            .contains(&"OVERLAP S1 and S2: 2026-01-10 to 2026-01-20".to_owned())
    );
    let mut partial = contained;
    partial["period_start"] = json!("2026-01-25");
    partial["period_end"] = json!("2026-02-24");
    partial["opening"] = json!("1150.00");
    partial["closing"] = json!("1150.00");
    let run_partial = run(&deposit(vec![january("S1"), partial]));
    assert_eq!(run_partial.code, Some(0), "{:?}", run_partial.stdout);
    assert_eq!(
        run_partial.stdout,
        [
            "OVERLAP S1 and S2: 2026-01-25 to 2026-01-31",
            "PASS 2 statements, 3 lines; compared 4 printed balances, 2 printed totals, 1 statement links",
        ]
    );
}

#[test]
fn an_overlap_needs_the_earlier_lines_in_date_order() {
    // Lines printed 3 Jan, 28 Jan, 20 Jan: the balance before 25 January is 1150.00, but the
    // last line in printed order dated before then leaves 1250.00.
    let mut statement = january("S1");
    let lines = statement["pages"][0]["lines"].as_array_mut().unwrap();
    lines.swap(1, 2);
    lines[1]["balance"] = json!("1300.00");
    lines[2]["balance"] = json!("1250.00");
    let next = json!({"id": "S2", "period_start": "2026-01-25", "period_end": "2026-02-24",
        "opening": "1250.00", "closing": "1250.00", "pages": []});
    let run = run(&deposit(vec![statement, next]));
    assert_eq!(run.code, Some(2));
    assert_eq!(
        run.stdout[0],
        "BREAK S1 to S2: overlap cannot be placed, S1 lines are not in date order"
    );
}

#[test]
fn lines_dated_outside_the_period_break() {
    let mut late = january("S1");
    late["pages"][0]["lines"][2]["date"] = json!("2027-01-28");
    let run_late = run(&deposit(vec![late]));
    assert_eq!(run_late.code, Some(2));
    assert_eq!(
        run_late.stdout[0],
        "BREAK S1 page 1 line 3: dated 2027-01-28, after the period ends 2026-01-31"
    );
    let mut early = january("S1");
    early["pages"][0]["lines"][0]["date"] = json!("2025-12-02");
    assert_eq!(run(&deposit(vec![early.clone()])).code, Some(0));
    early["pages"][0]["lines"][0]["date"] = json!("2025-11-30");
    assert_eq!(
        run(&deposit(vec![early])).stdout[0],
        "BREAK S1 page 1 line 1: dated 2025-11-30, more than 31 days before the period starts 2026-01-01"
    );
}

#[test]
fn references_must_be_present_and_unique() {
    let mut repeated = january("S1");
    repeated["pages"][0]["lines"][1]["line"] = json!("1");
    assert_refused(
        &run(&deposit(vec![repeated])),
        "line 1 appears more than once",
    );
    let mut empty = january("S1");
    empty["pages"][0]["lines"][0]["line"] = json!(" ");
    assert_refused(&run(&deposit(vec![empty])), "line reference is empty");
    let mut pages = january("S1");
    let page = pages["pages"][0].clone();
    pages["pages"].as_array_mut().unwrap().push(page);
    assert_refused(&run(&deposit(vec![pages])), "page 1 appears more than once");
    assert_refused(
        &run(&deposit(vec![january("")])),
        "statement reference is empty",
    );
}
