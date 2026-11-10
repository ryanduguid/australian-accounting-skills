// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

use accounting_skills::citations::{Unmatched, check};
use std::{fs, path::Path, process::Command};

fn skill(root: &Path, name: &str, text: &str, sources: Option<&str>) {
    let folder = root.join(".claude/skills").join(name);
    fs::create_dir_all(&folder).unwrap();
    fs::write(folder.join("SKILL.md"), text).unwrap();
    if let Some(sources) = sources {
        fs::write(folder.join("sources.json"), sources).unwrap();
    }
}

const SOURCES: &str = r#"{"skill": "alpha", "sources": [
  {"title": "Fuel Tax Act 2006", "url": "https://www.legislation.gov.au/C2006A00072/latest/text"},
  {"title": "Fuel schemes ruling", "url": "https://www.ato.gov.au/law/view/document?DocID=TXR/TR20103/NAT/ATO/00001"}
]}"#;

fn run(root: &Path) -> (i32, String) {
    let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args(["check-citations", "--root"])
        .arg(root)
        .output()
        .unwrap();
    (
        output.status.code().unwrap(),
        String::from_utf8(output.stdout)
            .unwrap()
            .replace("\r\n", "\n"),
    )
}

fn missing(file: &str, line: usize, citation: &str, reason: &str) -> Unmatched {
    Unmatched {
        file: file.into(),
        line,
        citation: citation.into(),
        reason: reason.into(),
    }
}

#[test]
fn each_unrecorded_ruling_and_section_is_reported_by_file_and_line() {
    let root = tempfile::tempdir().unwrap();
    skill(
        root.path(),
        "alpha",
        "Apply s 41-5 of the *Fuel Tax Act 2006* and TR 2010/3.\n\
         Then s 43-10(4) removes the charge.\n\
         PCG 2016/8 sets the records.\n\
         Deduct under s 8-1 of the ITAA 1997.\n\
         APES 110 Section 310 covers conflicts.\n",
        Some(SOURCES),
    );
    skill(
        root.path(),
        "beta",
        "Where ss 109D and 109R apply, flag it.\n",
        None,
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.rulings, report.rulings_resolved), (2, 1));
    assert_eq!((report.sections, report.sections_resolved), (5, 1));
    let alpha = ".claude/skills/alpha/SKILL.md";
    let beta = ".claude/skills/beta/SKILL.md";
    assert_eq!(
        report.unmatched,
        [
            missing(alpha, 2, "s 43-10(4)", "names no Act"),
            missing(alpha, 3, "PCG 2016/8", "no record names it"),
            missing(
                alpha,
                4,
                "s 8-1",
                "no record names its Act (Income Tax Assessment Act 1997)"
            ),
            missing(beta, 1, "ss 109D", "names no Act"),
            missing(beta, 1, "ss 109R", "names no Act"),
        ]
    );

    let (code, output) = run(root.path());
    assert_eq!(code, 2);
    assert!(output.starts_with(".claude/skills/alpha/SKILL.md:2: s 43-10(4): names no Act\n"));
    assert!(output.ends_with(
        "2 of 7 citations resolve to a sources.json record: \
         1 of 2 rulings and guidance, 1 of 5 legislative sections.\n"
    ));
}

#[test]
fn a_tree_whose_citations_all_resolve_passes() {
    let root = tempfile::tempdir().unwrap();
    skill(
        root.path(),
        "alpha",
        "Fuel Tax Act 2006 s 41-5 and [TR 2010/3](https://example.invalid).\n\
         ## References\n\
         The fuel must be acquired (s 41-10 of the\n\
         *Fuel Tax Act 2006*).\n",
        Some(SOURCES),
    );
    let (code, output) = run(root.path());
    assert_eq!(code, 0);
    assert_eq!(
        output,
        "3 of 3 citations resolve to a sources.json record: \
         1 of 1 rulings and guidance, 2 of 2 legislative sections.\n"
    );
}

#[test]
fn an_act_named_to_own_one_section_does_not_take_the_next() {
    let root = tempfile::tempdir().unwrap();
    skill(
        root.path(),
        "alpha",
        "Group under the Fuel Tax Act 2006 (s 70, via s 50 of the *Corporations Act 2001*), then s 71.\n\
         Later, s 72 applies.\n",
        Some(SOURCES),
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (4, 2));
    let alpha = ".claude/skills/alpha/SKILL.md";
    assert_eq!(
        report.unmatched,
        [
            missing(
                alpha,
                1,
                "s 50",
                "no record names its Act (Corporations Act 2001)"
            ),
            missing(alpha, 2, "s 72", "names no Act"),
        ]
    );
}

// The Act named in an earlier sentence, line or section of the skill does not
// own a section. Each case mirrors a citation the check once credited wrongly.
#[test]
fn a_section_takes_only_an_act_its_own_sentence_names() {
    let root = tempfile::tempdir().unwrap();
    skill(
        root.path(),
        "alpha",
        "Apply the Fuel Tax Act 2006 here.\n\
         \n\
         ## Super\n\
         \n\
         Deduct under s 8-1 of the\n\
         ITAA 1997.\n\
         See section 3 below for the steps.\n\
         Then s 43-10 applies.\n\
         \n\
         Under the ITAA 1997 and the Fuel Tax Act 2006, s 41-5 applies.\n",
        Some(SOURCES),
    );
    // au-client-departure: the Code Determination named a paragraph earlier
    // was credited with Corporations Act s 286.
    skill(
        root.path(),
        "beta",
        "Follow the *Tax Agent Services (Code of Professional Conduct) Determination 2024*.\n\
         \n\
         Record the lien question with the section 286 and ledger access limits.\n",
        Some(
            r#"{"sources": [{"title": "Tax Agent Services (Code of Professional Conduct) Determination 2024",
              "url": "https://www.legislation.gov.au/F2024L00888/latest/text"}]}"#,
        ),
    );
    // coal-lsl-levy: "the Administration Act" names no year, so the levy
    // collection Act on the item before took s 44 and s 45.
    skill(
        root.path(),
        "gamma",
        "1. The Payroll Levy Collection Act 1992 sets the deadline.\n\
         2. Claim under Part 7 of the Administration Act (s 44, with the rules made under s 45).\n",
        Some(
            r#"{"sources": [{"title": "Coal Mining Industry (Long Service Leave) Payroll Levy Collection Act 1992",
              "url": "https://www.legislation.gov.au/C2004A04354/latest/text"}]}"#,
        ),
    );
    // au-trust-distributions and au-tax-agent-obligations: an amending Act
    // named on the line before took ITAA 1936 s 100A and TASA s 50-20. An
    // amending Act does not own the sections it inserts either.
    skill(
        root.path(),
        "delta",
        "- [*Treasury Laws Amendment (Tax Reform No. 1) Act 2026*](https://www.legislation.gov.au/C2026A00049/asmade/text)\n\
         - [TR 2022/4 Income tax: section 100A reimbursement agreements](https://www.ato.gov.au/law/view/document?DocID=TXR/TR20224/NAT/ATO/00001)\n\
         \n\
         The *Treasury Laws Amendment (Tax Reform No. 1) Act 2026* inserted s 26-155.\n\
         Note section 50-20 of the Act.\n",
        Some(
            r#"{"sources": [
              {"title": "Treasury Laws Amendment (Tax Reform No. 1) Act 2026", "url": "https://www.legislation.gov.au/C2026A00049/asmade/text"},
              {"title": "TR 2022/4", "url": "https://www.ato.gov.au/law/view/document?DocID=TXR/TR20224/NAT/ATO/00001"}
            ]}"#,
        ),
    );
    // payroll-tax-contractors: an Act named to own one section does not own
    // the others in its sentence ("s 70" and "s 71" are of the Payroll Tax Act).
    skill(
        root.path(),
        "epsilon",
        "Part 5 groups related bodies (s 70, via s 50 of the *Corporations Act 2001*) and common employees (s 71).\n\
         A list shares its Act: s 72 or s 73 of the *Corporations Act 2001*.\n\
         Section 74 of the *Corporations Act 2001* applies and s 75 sets the time.\n",
        Some(
            r#"{"sources": [{"title": "Corporations Act 2001",
              "url": "https://www.legislation.gov.au/C2004A00818/latest/text"}]}"#,
        ),
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (16, 5));
    let file = |name: &str| format!(".claude/skills/{name}/SKILL.md");
    assert_eq!(
        report.unmatched,
        [
            missing(
                &file("alpha"),
                5,
                "s 8-1",
                "no record names its Act (Income Tax Assessment Act 1997)"
            ),
            missing(&file("alpha"), 8, "s 43-10", "names no Act"),
            missing(
                &file("alpha"),
                10,
                "s 41-5",
                "its sentence names more than one Act (ITAA 1997; Fuel Tax Act)"
            ),
            missing(&file("beta"), 3, "section 286", "names no Act"),
            missing(&file("delta"), 2, "section 100A", "names no Act"),
            missing(&file("delta"), 4, "s 26-155", "names no Act"),
            missing(
                &file("delta"),
                5,
                "section 50-20",
                "names its Act only as 'the Act'"
            ),
            missing(
                &file("epsilon"),
                1,
                "s 70",
                "names its Act only beside another section"
            ),
            missing(
                &file("epsilon"),
                1,
                "s 71",
                "names its Act only beside another section"
            ),
            missing(&file("gamma"), 2, "s 44", "names no Act"),
            missing(&file("gamma"), 2, "s 45", "names no Act"),
        ]
    );
}

#[test]
fn a_record_off_a_legislation_register_owns_no_section() {
    let root = tempfile::tempdir().unwrap();
    skill(
        root.path(),
        "alpha",
        "Deduct under s 8-1 of the ITAA 1997 and s 26-50 of the ITAA 1997.\n",
        Some(
            r#"{"sources": [
              {"title": "ATO page about deductions under the Income Tax Assessment Act 1997", "url": "https://www.ato.gov.au/x"},
              {"title": "PCG 2026/3 Application of section 26-50 of the Income Tax Assessment Act 1997", "url": "https://www.ato.gov.au/law/view/document?DocID=COG/PCG20263/NAT/ATO/00001"}
            ]}"#,
        ),
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (2, 0));
    // The ATO legal database's copy of the Act is register text.
    fs::write(
        root.path().join(".claude/skills/alpha/sources.json"),
        r#"{"sources": [{"title": "Income Tax Assessment Act 1997",
          "url": "https://www.ato.gov.au/law/view/document?DocID=PAC/19970038/8-1"}]}"#,
    )
    .unwrap();
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (2, 2));
}

#[test]
fn a_malformed_index_or_root_is_refused() {
    let root = tempfile::tempdir().unwrap();
    skill(
        root.path(),
        "alpha",
        "s 8-1",
        Some(r#"{"sources": [null]}"#),
    );
    let error = check(root.path()).unwrap_err().to_string();
    assert!(error.ends_with("record 1 is not an object"), "{error}");
    let empty = tempfile::tempdir().unwrap();
    assert_eq!(run(empty.path()).0, 1);
}
