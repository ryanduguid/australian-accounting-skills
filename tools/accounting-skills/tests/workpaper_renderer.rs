// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

use serde_json::{Value, json};
use std::{fs, process::Command};

fn bin() -> &'static str {
    env!("CARGO_BIN_EXE_workpaper-renderer")
}

#[test]
fn cli_help_schema_and_bad_args() {
    let help = Command::new(bin()).arg("--help").output().unwrap();
    assert_eq!(help.status.code(), Some(0));
    assert!(
        String::from_utf8(help.stdout)
            .unwrap()
            .contains("workpaper-renderer render")
    );

    let schema = Command::new(bin()).arg("schema").output().unwrap();
    assert_eq!(schema.status.code(), Some(0));
    let parsed: Value = serde_json::from_slice(&schema.stdout).unwrap();
    assert_eq!(parsed["title"], "Australian Accounting Workpaper");

    let bad = Command::new(bin()).arg("unknown-subcmd").output().unwrap();
    assert_eq!(bad.status.code(), Some(2));

    let missing_out = Command::new(bin())
        .args(["render", "--input", "nonexistent.json"])
        .output()
        .unwrap();
    assert_eq!(missing_out.status.code(), Some(1));
    assert!(
        String::from_utf8(missing_out.stderr)
            .unwrap()
            .contains("at least one of --xlsx, --docx or --pdf")
    );
}

#[test]
fn renders_json_workpaper_to_xlsx_docx_pdf_and_verifies_formulas() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("bas.json");
    let xlsx_path = dir.path().join("bas.xlsx");
    let docx_path = dir.path().join("bas.docx");
    let pdf_path = dir.path().join("bas.pdf");
    let report_path = dir.path().join("report.json");

    let workpaper = json!({
        "title": "Q3 BAS Workpaper (Fabricated Fixture)",
        "entity_code": "ENT-001",
        "period": "2026-01-01 to 2026-03-31",
        "prepared_on": "2026-04-10",
        "reviewer": "Manager",
        "status": "DRAFT_FOR_REVIEW",
        "summary": "Quarterly GST and PAYG reconciliation prepared for human review. Contains 1 UNVERIFIED item.",
        "sections": [
            {
                "heading": "GST Control Tie-Out",
                "paragraphs": ["Collected GST less input tax credits agrees to the GST clearing movement within $0.00."],
                "bullets": ["Cash basis confirmed against prior BAS.", "Missing tax invoice flagged as UNVERIFIED."],
                "table": {
                    "headers": ["Label", "Description", "Amount"],
                    "rows": [
                        ["1A", "GST on sales", "$12,500.00"],
                        ["1B", "GST on purchases", "$4,200.00"],
                        ["Net", "1A less 1B", "$8,300.00"]
                    ]
                }
            }
        ],
        "sheets": [
            {
                "name": "BAS Schedule",
                "headers": ["Code", "Category", "Amount", "Taxable"],
                "rows": [
                    ["1A", "Sales GST", 12500.0, true],
                    ["1B", "Purchase GST", 4200.0, true],
                    ["ADJ", "Prior adjustment", -300.0, false],
                    ["NET", "Net GST", {"formula": "=C2-C3+C4", "format": "currency"}, false],
                    ["SUM", "Gross absolute", {"formula": "=SUM(C2:C3)+ABS(C4)", "format": "number"}, false],
                    ["AVG", "Mean 1A/1B", {"formula": "=ROUND(AVERAGE(C2:C3), 2)", "format": "number"}, false],
                    ["MINMAX", "Spread", {"formula": "=MAX(C2:C3)-MIN(C2:C3)", "format": "number"}, false],
                    ["CNT", "Numeric count", {"formula": "=COUNT(C2:C4)", "format": "number"}, false],
                    ["COND", "Payable flag", {"formula": "=IF(C5>0, 1, 0)", "format": "number"}, false],
                    ["SAFE", "Div guard", {"formula": "=IFERROR(C2/0, 99)", "format": "number"}, false],
                    ["SIF", "Sales only", {"formula": "=SUMIF(A2:A4, \"1A\", C2:C4)", "format": "currency"}, false],
                    ["INJ", "=SUM(C2:C4)", 0.0, false]
                ]
            },
            {
                "name": "Cross Check",
                "headers": ["Check", "Result"],
                "rows": [
                    ["Tie to BAS Schedule", {"formula": "='BAS Schedule'!C5", "format": "currency"}],
                    ["Variance", {"formula": "=B2-8000", "format": "currency"}]
                ]
            }
        ],
        "exceptions": [
            {
                "id": "EXC-1",
                "item": "Missing tax invoice for $440 supply (UNVERIFIED)",
                "status": "UNVERIFIED",
                "evidence_needed": "Supplier tax invoice showing ABN and GST",
                "owner": "Client"
            }
        ],
        "sources": [
            {
                "title": "A New Tax System (Goods and Services Tax) Act 1999",
                "reference": "s 11-5, s 29-10",
                "checked_at": "2026-04-10",
                "status": "CONFIRMED"
            }
        ]
    });
    fs::write(&input, serde_json::to_vec_pretty(&workpaper).unwrap()).unwrap();

    let output = Command::new(bin())
        .args([
            "render",
            "--input",
            input.to_str().unwrap(),
            "--xlsx",
            xlsx_path.to_str().unwrap(),
            "--docx",
            docx_path.to_str().unwrap(),
            "--pdf",
            pdf_path.to_str().unwrap(),
            "--report",
            report_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert_eq!(
        output.status.code(),
        Some(0),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let report: Value = serde_json::from_slice(&fs::read(&report_path).unwrap()).unwrap();
    assert_eq!(report["ok"], true);
    assert_eq!(report["formula_count"], 10);
    assert_eq!(report["error_count"], 0);
    assert_eq!(report["open_exception_count"], 1);
    assert!(report["unverified_mentions"].as_u64().unwrap() >= 3);

    // Check key evaluated values
    let formulas = report["formulas"].as_array().unwrap();
    let find_val = |sheet: &str, cell: &str| {
        formulas
            .iter()
            .find(|f| f["sheet"] == sheet && f["cell"] == cell)
            .unwrap()["value"]
            .as_f64()
            .unwrap()
    };
    assert!((find_val("BAS Schedule", "C5") - 8000.0).abs() < 1e-6);
    assert!((find_val("BAS Schedule", "C6") - 17000.0).abs() < 1e-6);
    assert!((find_val("BAS Schedule", "C7") - 8350.0).abs() < 1e-6);
    assert!((find_val("BAS Schedule", "C8") - 8300.0).abs() < 1e-6);
    assert!((find_val("BAS Schedule", "C9") - 3.0).abs() < 1e-6);
    assert!((find_val("BAS Schedule", "C10") - 1.0).abs() < 1e-6);
    assert!((find_val("BAS Schedule", "C11") - 99.0).abs() < 1e-6);
    assert!((find_val("BAS Schedule", "C12") - 12500.0).abs() < 1e-6);
    assert!((find_val("Cross Check", "B2") - 8000.0).abs() < 1e-6);
    assert!((find_val("Cross Check", "B3") - 0.0).abs() < 1e-6);

    // Standalone verify-xlsx passes on the generated workbook.
    let verify = Command::new(bin())
        .args(["verify-xlsx", "--input", xlsx_path.to_str().unwrap()])
        .output()
        .unwrap();
    assert_eq!(
        verify.status.code(),
        Some(0),
        "stdout: {}\nstderr: {}",
        String::from_utf8_lossy(&verify.stdout),
        String::from_utf8_lossy(&verify.stderr)
    );
    let verify_report: Value = serde_json::from_slice(&verify.stdout).unwrap();
    assert_eq!(verify_report["ok"], true);
    assert_eq!(verify_report["formula_count"], 10);

    // Check formula-injection string stayed an inline string, not a formula.
    let xlsx_bytes = fs::read(&xlsx_path).unwrap();
    let xlsx_str = String::from_utf8_lossy(&xlsx_bytes);
    assert!(xlsx_str.contains("DRAFT FOR HUMAN REVIEW"));
    assert!(xlsx_str.contains(r#"t="inlineStr"><is><t>=SUM(C2:C4)</t></is>"#));

    // Check DOCX contains header, banner, headings and exceptions.
    let docx_bytes = fs::read(&docx_path).unwrap();
    let docx_str = String::from_utf8_lossy(&docx_bytes);
    assert!(docx_bytes.starts_with(b"PK\x03\x04"));
    assert!(docx_str.contains("word/document.xml"));
    assert!(docx_str.contains("DRAFT FOR HUMAN REVIEW"));
    assert!(docx_str.contains("OPEN REVIEW ITEMS PRESENT"));
    assert!(docx_str.contains("Reviewer exception register"));

    // Check PDF structure, header banner and xref trailer.
    let pdf_bytes = fs::read(&pdf_path).unwrap();
    let pdf_str = String::from_utf8_lossy(&pdf_bytes);
    assert!(pdf_bytes.starts_with(b"%PDF-1.4\n"));
    assert!(pdf_str.contains("DRAFT FOR HUMAN REVIEW"));
    assert!(pdf_str.contains("Page 1 of 1"));
    assert!(pdf_str.contains("%%EOF"));
}

#[test]
fn detects_div_zero_cycles_and_disallowed_formulas() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("bad.json");
    let xlsx_path = dir.path().join("bad.xlsx");
    let report_path = dir.path().join("bad-report.json");

    let workpaper = json!({
        "title": "Faulty Formula Fixture",
        "sheets": [
            {
                "name": "Faults",
                "headers": ["Case", "Formula"],
                "rows": [
                    ["DivZero", {"formula": "=10/0"}],
                    ["CycleA", {"formula": "=B4+1"}],
                    ["CycleB", {"formula": "=B3+1"}],
                    ["Webservice", {"formula": "=WEBSERVICE(\"https://example.invalid\")"}],
                    ["ExternalRef", {"formula": "=[other.xlsx]Sheet1!A1"}]
                ]
            }
        ]
    });
    fs::write(&input, serde_json::to_vec_pretty(&workpaper).unwrap()).unwrap();

    let output = Command::new(bin())
        .args([
            "render",
            "--input",
            input.to_str().unwrap(),
            "--xlsx",
            xlsx_path.to_str().unwrap(),
            "--report",
            report_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(1));
    let report: Value = serde_json::from_slice(&fs::read(&report_path).unwrap()).unwrap();
    assert_eq!(report["ok"], false);
    assert_eq!(report["error_count"], 5);

    // verify-xlsx must also reject the workbook carrying error cells.
    let verify = Command::new(bin())
        .args(["verify-xlsx", "--input", xlsx_path.to_str().unwrap()])
        .output()
        .unwrap();
    assert_eq!(verify.status.code(), Some(1));
}

#[test]
fn parses_markdown_workpaper_and_paginates_long_pdf() {
    let dir = tempfile::tempdir().unwrap();
    let md_path = dir.path().join("note.md");
    let xlsx_path = dir.path().join("note.xlsx");
    let docx_path = dir.path().join("note.docx");
    let pdf_path = dir.path().join("note.pdf");

    let mut md = String::from(
        "---\n\
         title: \"Division 7A Workpaper\"\n\
         entity_code: \"ENT-042\"\n\
         period: \"2025-26\"\n\
         prepared_on: \"2026-08-15\"\n\
         reviewer: \"Partner\"\n\
         status: \"DRAFT_FOR_REVIEW\"\n\
         ---\n\n\
         Overview summary for review.\n\n\
         ## Loan Schedule\n\n\
         | Loan | Opening | Repayments |\n\
         | --- | --- | --- |\n\
         | SH-1 | $50,000.00 | $10,000.00 |\n\
         | SH-2 | $12,000.00 | $0.00 |\n\n\
         ## Exceptions\n\n\
         - Signed complying agreement for SH-2 is UNVERIFIED.\n\n\
         ## Detailed Notes\n\n",
    );
    for i in 1..=70 {
        md.push_str(&format!(
            "- Review note {i}: verify repayment bank trace before lodgement day.\n"
        ));
    }
    fs::write(&md_path, md).unwrap();

    let output = Command::new(bin())
        .args([
            "render",
            "--input",
            md_path.to_str().unwrap(),
            "--xlsx",
            xlsx_path.to_str().unwrap(),
            "--docx",
            docx_path.to_str().unwrap(),
            "--pdf",
            pdf_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(0));
    let report: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(report["ok"], true);
    assert_eq!(report["open_exception_count"], 1);
    assert_eq!(report["unverified_mentions"], 3);

    let pdf_str = String::from_utf8_lossy(&fs::read(&pdf_path).unwrap()).into_owned();
    assert!(pdf_str.contains("Page 2 of "), "expected multi-page PDF");

    let verify = Command::new(bin())
        .args(["verify-xlsx", "--input", xlsx_path.to_str().unwrap()])
        .output()
        .unwrap();
    assert_eq!(verify.status.code(), Some(0));
}

#[test]
fn verify_xlsx_rejects_corrupted_archive() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("simple.json");
    let xlsx_path = dir.path().join("simple.xlsx");
    fs::write(&input, r#"{"title":"Simple"}"#).unwrap();
    let render = Command::new(bin())
        .args([
            "render",
            "--input",
            input.to_str().unwrap(),
            "--xlsx",
            xlsx_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert_eq!(render.status.code(), Some(0));

    let mut bytes = fs::read(&xlsx_path).unwrap();
    let mid = bytes.len() / 2;
    bytes[mid] ^= 0xFF;
    let corrupt_path = dir.path().join("corrupt.xlsx");
    fs::write(&corrupt_path, bytes).unwrap();

    let verify = Command::new(bin())
        .args(["verify-xlsx", "--input", corrupt_path.to_str().unwrap()])
        .output()
        .unwrap();
    assert_eq!(verify.status.code(), Some(1));
}
