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
         1 of 2 rulings and guidance, 1 of 5 legislative sections.\n\
         0 of 1 resolved sections checked against an index of their Act: \
         0 found, 0 listed exceptions, 0 absent; 1 in an Act with no index.\n"
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
         1 of 1 rulings and guidance, 2 of 2 legislative sections.\n\
         0 of 2 resolved sections checked against an index of their Act: \
         0 found, 0 listed exceptions, 0 absent; 2 in an Act with no index.\n"
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
                "its sentence names more than one Act (ITAA 1997; Fuel Tax Act 2006)"
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

const FUEL: &str = r#"{"sources": [{"title": "Fuel Tax Act 2006",
  "url": "https://www.legislation.gov.au/C2006A00072/latest/text"}]}"#;

fn record(title: &str, url: &str) -> String {
    format!(r#"{{"sources": [{{"title": "{title}", "url": "{url}"}}]}}"#)
}

/// The only unmatched citation in a skill holding `text` and `sources`, after
/// checking that the command exits 2.
fn only_unmatched(text: &str, sources: &str) -> Unmatched {
    let root = tempfile::tempdir().unwrap();
    skill(root.path(), "alpha", text, Some(sources));
    assert_eq!(run(root.path()).0, 2, "{text}");
    let mut report = check(root.path()).unwrap();
    assert_eq!(report.unmatched.len(), 1, "{:?}", report.unmatched);
    report.unmatched.remove(0)
}

fn unmatched_in_alpha(line: usize, citation: &str, reason: &str) -> Unmatched {
    missing(".claude/skills/alpha/SKILL.md", line, citation, reason)
}

// Each case is a citation an earlier version of the check credited to an Act
// that is not its own, or to a record that is not a copy of its Act.
#[test]
fn a_sentence_that_starts_with_a_section_does_not_take_the_last_ones_act() {
    let text = "Apply the Fuel Tax Act 2006 to the fuel. s 8-1 allows the deduction.\n";
    assert_eq!(
        only_unmatched(text, FUEL),
        unmatched_in_alpha(1, "s 8-1", "names no Act")
    );
    let text = "1. Apply the Fuel Tax Act 2006 to the fuel.\n   s 8-1 allows the deduction.\n";
    assert_eq!(
        only_unmatched(text, FUEL),
        unmatched_in_alpha(2, "s 8-1", "names no Act")
    );
}

#[test]
fn lower_case_and_numeric_sentence_starts_do_not_borrow_an_act() {
    for text in [
        "Fuel Tax Act 2006 applies. the deduction under s 8-1 needs review.\n",
        "Fuel Tax Act 2006 applies. 2 taxpayers claim under s 8-1.\n",
        "Fuel Tax Act 2006 applies? the deduction under s 8-1 needs review.\n",
        "Fuel Tax Act 2006 applies! 2 taxpayers claim under s 8-1.\n",
    ] {
        assert_eq!(
            only_unmatched(text, FUEL),
            unmatched_in_alpha(1, "s 8-1", "names no Act")
        );
    }
}

#[test]
fn explicit_abbreviations_keep_sections_in_their_sentence() {
    for text in [
        "Fuel Tax Act 2006 applies, e.g. s 41-5 needs review.\n",
        "Fuel Tax Act 2006 applies, i.e. s 41-5 needs review.\n",
        "Fuel Tax Act 2006 applies to example No. 1 under s 41-5.\n",
    ] {
        let root = tempfile::tempdir().unwrap();
        skill(root.path(), "alpha", text, Some(FUEL));
        assert_eq!(run(root.path()).0, 0, "{text}");
        assert!(check(root.path()).unwrap().unmatched.is_empty());
    }
}

#[test]
fn an_act_the_text_does_not_name_in_full_is_not_another_named_act() {
    let text = "Claim under s 44 of the Administration Act, and keep the records the Fuel Tax Act 2006 requires.\n";
    assert_eq!(
        only_unmatched(text, FUEL),
        unmatched_in_alpha(1, "s 44", "names its Act only as 'the Administration Act'")
    );
    let text = "Section 8-1 of that Act applies, unlike the Fuel Tax Act 2006.\n";
    assert_eq!(
        only_unmatched(text, FUEL),
        unmatched_in_alpha(1, "Section 8-1", "names its Act only as 'that Act'")
    );
}

#[test]
fn an_act_the_sentence_says_amends_does_not_own_its_sections() {
    let text = "The Tax and Superannuation Laws (Integrity Measures) Act 2026 inserted s 26-155.\n";
    let sources = record(
        "Tax and Superannuation Laws (Integrity Measures) Act 2026",
        "https://www.legislation.gov.au/C2026A00077/asmade/text",
    );
    assert_eq!(
        only_unmatched(text, &sources),
        unmatched_in_alpha(1, "s 26-155", "names no Act")
    );
}

#[test]
fn a_record_owns_only_the_instrument_it_is_a_copy_of() {
    let text = "Deduct under s 8-1 of the ITAA 1997.\n";
    let itaa = "no record names its Act (Income Tax Assessment Act 1997)";
    for (title, url) in [
        // An instrument made under the Act.
        (
            "Fuel Tax (Correcting Fuel Tax Errors) Determination 2023, made under the Income Tax Assessment Act 1997",
            "https://www.legislation.gov.au/F2023L01234/latest/text",
        ),
        // An Act that amends it.
        (
            "Treasury Laws Amendment (Tax Reform No. 1) Act 2026, amending the Income Tax Assessment Act 1997",
            "https://www.legislation.gov.au/C2026A00049/asmade/text",
        ),
        // The Fuel Tax Act's register copy, titled as the ITAA 1997.
        (
            "Income Tax Assessment Act 1997",
            "https://www.legislation.gov.au/C2006A00072/latest/text",
        ),
        // An F-series legislative instrument cannot be the Act its title names.
        (
            "Income Tax Assessment Act 1997",
            "https://www.legislation.gov.au/F2023L01234/latest/text",
        ),
        // ATO guidance whose title holds the Act's register identifier.
        (
            "Income Tax Assessment Act 1997 C2004A05138",
            "https://www.ato.gov.au/law/view/document?DocID=TXR/TR20103/NAT/ATO/00001",
        ),
    ] {
        assert_eq!(
            only_unmatched(text, &record(title, url)),
            unmatched_in_alpha(1, "s 8-1", itaa),
            "{title}"
        );
    }
    // A record whose title names no jurisdiction takes its register's.
    let text = "Apply s 32 of the Payroll Tax Act 2007 (Vic).\n";
    let sources = record(
        "Payroll Tax Act 2007",
        "https://legislation.nsw.gov.au/view/html/inforce/current/act-2007-021",
    );
    assert_eq!(
        only_unmatched(text, &sources),
        unmatched_in_alpha(
            1,
            "s 32",
            "no record names its Act (Payroll Tax Act 2007 (Vic))"
        )
    );
}

#[test]
fn a_cited_title_is_not_replaced_by_its_link_or_a_short_name_inside_it() {
    let itaa = "no record names its Act (Income Tax Assessment Act 1997)";
    // A link to another Act's register copy.
    let text = "Deduct under s 8-1 of the [ITAA 1997](https://www.legislation.gov.au/C2006A00072/latest/text).\n";
    assert_eq!(
        only_unmatched(text, FUEL),
        unmatched_in_alpha(1, "s 8-1", itaa)
    );
    let text = "Deduct under s 8-1 of [ITAA 1997](https://www.legislation.gov.au/C1936A00027/latest/text).\n";
    let sources = record(
        "Income Tax Assessment Act 1936",
        "https://www.legislation.gov.au/C1936A00027/latest/text",
    );
    assert_eq!(
        only_unmatched(text, &sources),
        unmatched_in_alpha(1, "s 8-1", itaa)
    );
    // "Fair Work Act" is the short name of the Fair Work Act 2009, not of
    // South Australia's Fair Work Act 1994.
    let text = "Apply s 4 of Fair Work Act 1994 (SA).\n";
    let sources = record(
        "Fair Work Act 2009",
        "https://www.legislation.gov.au/C2009A00028/latest/text",
    );
    assert_eq!(
        only_unmatched(text, &sources),
        unmatched_in_alpha(
            1,
            "s 4",
            "no record names its Act (Fair Work Act 1994 (SA))"
        )
    );
}

#[test]
fn contradictory_register_copies_do_not_resolve_either_jurisdiction() {
    let sources = r#"{"sources":[{
        "title":"Payroll Tax Act 2007",
        "url":"https://legislation.nsw.gov.au/view/html/inforce/current/act-2007-021",
        "final_url":"https://www.legislation.vic.gov.au/in-force/acts/payroll-tax-act-2007"
    }]}"#;
    for place in ["Vic", "NSW"] {
        let text = format!("Apply s 32 of Payroll Tax Act 2007 ({place}).\n");
        assert_eq!(
            only_unmatched(&text, sources),
            unmatched_in_alpha(
                1,
                "s 32",
                &format!("no record names its Act (Payroll Tax Act 2007 ({place}))")
            )
        );
    }
}

#[test]
fn a_register_homepage_or_search_query_is_not_a_document() {
    let text = "Apply s 32 of Payroll Tax Act 2007 (NSW).\n";
    for url in [
        "https://legislation.nsw.gov.au/#act-2007-021",
        "https://legislation.nsw.gov.au/search?query=act-2007-021",
        "https://legislation.nsw.gov.au/view/html/inforce/current/sl-2007-021",
    ] {
        assert_eq!(
            only_unmatched(text, &record("Payroll Tax Act 2007", url)),
            unmatched_in_alpha(
                1,
                "s 32",
                "no record names its Act (Payroll Tax Act 2007 (NSW))"
            )
        );
    }
}

#[test]
fn a_state_register_link_and_a_schedule_resolve() {
    let root = tempfile::tempdir().unwrap();
    skill(
        root.path(),
        "alpha",
        "Read [Payroll Tax Act 2007](https://legislation.nsw.gov.au/view/html/inforce/current/act-2007-021) s 32.\n\
         Report under s 131-5 of Schedule 1 to the TAA 1953.\n",
        Some(
            r#"{"sources": [
              {"title": "Payroll Tax Act 2007 (NSW)", "url": "https://legislation.nsw.gov.au/view/html/inforce/current/act-2007-021"},
              {"title": "Taxation Administration Act 1953", "url": "https://www.legislation.gov.au/C1953A00001/latest/text"}
            ]}"#,
        ),
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (2, 2));
    // The link places the Act in New South Wales, so a Victorian copy is not it.
    fs::write(
        root.path().join(".claude/skills/alpha/sources.json"),
        record(
            "Payroll Tax Act 2007 (Vic)",
            "https://www.legislation.vic.gov.au/in-force/acts/payroll-tax-act-2007",
        ),
    )
    .unwrap();
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (2, 0));
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

#[test]
fn document_identifiers_at_the_register_root_resolve() {
    for (title, url, citation) in [
        (
            "Payroll Tax Act 2011 (ACT)",
            "https://www.legislation.act.gov.au/a/2011-18/",
            "s 31 of the Payroll Tax Act 2011 (ACT).\n",
        ),
        (
            "Payroll Tax Act 2009 (SA)",
            "https://www.legislation.sa.gov.au/lz?path=/c/a/payroll%20tax%20act%202009",
            "s 31 of the Payroll Tax Act 2009 (SA).\n",
        ),
    ] {
        let root = tempfile::tempdir().unwrap();
        skill(root.path(), "alpha", citation, Some(&record(title, url)));
        let report = check(root.path()).unwrap();
        assert_eq!((report.sections, report.sections_resolved), (1, 1), "{url}");
        assert!(report.unmatched.is_empty(), "{:?}", report.unmatched);
        assert_eq!(run(root.path()).0, 0, "{url}");
    }
}

#[test]
fn full_section_numbers_are_preserved_in_diagnostics_and_ownership() {
    let root = tempfile::tempdir().unwrap();
    let text = "Read s 159GZZZK of the ITAA 1936.\n\
        Read ss 159GZZZP(3) and 159GZZZPA of the ITAA 1936.\n\
        Read reg 6.17A of the Superannuation Industry (Supervision) Regulations 1994.\n\
        Read Regulation 8.02B of the Superannuation Industry (Supervision) Regulations 1994.\n\
        Read Regulations 6.21 and 6.22 of the Superannuation Industry (Supervision) Regulations 1994.\n\
        Read s 307-125.02 of the Income Tax Assessment (1997 Act) Regulations 2021.\n";
    skill(root.path(), "alpha", text, None);
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (8, 0));
    assert_eq!(
        report
            .unmatched
            .iter()
            .map(|item| item.citation.as_str())
            .collect::<Vec<_>>(),
        [
            "s 159GZZZK",
            "ss 159GZZZP(3)",
            "ss 159GZZZPA",
            "reg 6.17A",
            "Regulation 8.02B",
            "Regulations 6.21",
            "Regulations 6.22",
            "s 307-125.02"
        ]
    );
    fs::write(
        root.path().join(".claude/skills/alpha/sources.json"),
        record(
            "Superannuation Industry (Supervision) Regulations 1994",
            "https://www.legislation.gov.au/F1996B00580/latest/text",
        ),
    )
    .unwrap();
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (8, 4));
    assert!(
        report
            .unmatched
            .iter()
            .all(|item| item.citation.starts_with("s ") || item.citation.starts_with("ss "))
    );
    skill(
        root.path(),
        "alpha",
        text,
        Some(
            r#"{"sources": [
          {"title": "Income Tax Assessment Act 1936", "url": "https://www.legislation.gov.au/C1936A00027/latest/text"},
          {"title": "Superannuation Industry (Supervision) Regulations 1994", "url": "https://www.legislation.gov.au/F1996B00580/latest/text"},
          {"title": "Income Tax Assessment (1997 Act) Regulations 2021", "url": "https://www.legislation.gov.au/F2021L00206/latest/text"}
        ]}"#,
        ),
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (8, 8));
    assert!(report.unmatched.is_empty(), "{:?}", report.unmatched);
}

#[test]
fn a_section_inside_an_inferred_title_is_still_checked() {
    let root = tempfile::tempdir().unwrap();
    skill(
        root.path(),
        "alpha",
        "TASA (s 30-35) and the Corporations Act 2001.\n",
        None,
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (1, 0));
    assert_eq!(report.unmatched[0].citation, "s 30-35");
}

/// Write the section index of a fabricated Commonwealth Act.
fn index(root: &Path, register_id: &str, title: &str, sections: &[&str]) {
    let folder = root.join("tools/accounting-skills/section-index");
    fs::create_dir_all(&folder).unwrap();
    fs::write(
        folder.join(format!("{register_id}.txt")),
        index_text(register_id, title, sections),
    )
    .unwrap();
}

fn index_text(register_id: &str, title: &str, sections: &[&str]) -> String {
    format!(
        "# title: {title}\n# register-id: {register_id}\n# compilation: C2099C00001\n\
         # compilation-number: 1\n# in-force-from: 2099-01-01\n\
         # source: https://example.invalid/{register_id}\n# retrieved: 2099-01-02\n\
         # sha256: {}\n{}\n",
        "0".repeat(64),
        sections.join("\n")
    )
}

fn exceptions(root: &Path, text: &str) {
    fs::write(
        root.join("tools/accounting-skills/section-index/exceptions.txt"),
        text,
    )
    .unwrap();
}

const INDEXED: &str = r#"{"sources": [
  {"title": "Fuel Tax Act 2006", "url": "https://www.legislation.gov.au/C2006A00072/latest/text"},
  {"title": "Corporations Act 2001", "url": "https://www.legislation.gov.au/C2004A00818/latest/text"},
  {"title": "Payroll Tax Act 2007 (NSW)", "url": "https://legislation.nsw.gov.au/view/html/inforce/current/act-2007-021"}
]}"#;

#[test]
fn a_section_absent_from_its_acts_index_fails_and_an_unindexed_act_does_not() {
    let root = tempfile::tempdir().unwrap();
    index(
        root.path(),
        "C2006A00072",
        "Fuel Tax Act 2006",
        &["41-5", "43-10"],
    );
    // A Commonwealth Act sharing the title and year of the state Act the
    // skill cites without its jurisdiction: the record, not the index, owns it.
    index(root.path(), "C2099A00001", "Payroll Tax Act 2007", &["1"]);
    skill(
        root.path(),
        "alpha",
        "Apply s 41-5 and s 43-10(4) of the Fuel Tax Act 2006.\n\
         Then s 41-99 of the Fuel Tax Act 2006 applies.\n\
         See s 180 of the Corporations Act 2001.\n\
         See s 99 of the Payroll Tax Act 2007.\n",
        Some(INDEXED),
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (5, 5));
    assert_eq!(
        (
            report.sections_exist,
            report.sections_absent,
            report.sections_excepted,
            report.sections_not_indexed
        ),
        (2, 1, 0, 2)
    );
    assert_eq!(
        report.unmatched,
        [unmatched_in_alpha(
            2,
            "s 41-99",
            "absent from the section index of Fuel Tax Act 2006, compilation C2099C00001"
        )]
    );
    let (code, output) = run(root.path());
    assert_eq!(code, 2);
    assert!(output.ends_with(
        "3 of 5 resolved sections checked against an index of their Act: \
         2 found, 0 listed exceptions, 1 absent; 2 in an Act with no index.\n"
    ));
}

#[test]
fn a_listed_exception_is_counted_apart_and_an_unused_one_fails() {
    let root = tempfile::tempdir().unwrap();
    index(root.path(), "C2006A00072", "Fuel Tax Act 2006", &["41-5"]);
    skill(
        root.path(),
        "alpha",
        "The Bill would insert s 41-77 of the Fuel Tax Act 2006.\n",
        Some(FUEL),
    );
    exceptions(
        root.path(),
        "# Reasoned exceptions.\n\
         C2006A00072 41-77: proposed by a Bill\n\
         C2006A00072 41-5: the index has it\n",
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections_excepted, report.sections_absent), (1, 0));
    assert_eq!(
        report.unmatched,
        [missing(
            "tools/accounting-skills/section-index/exceptions.txt",
            3,
            "C2006A00072 41-5",
            "no cited section absent from the index needs this exception"
        )]
    );
    assert_eq!(run(root.path()).0, 2);

    exceptions(root.path(), "C2006A00072 41-77: proposed by a Bill\n");
    let (code, output) = run(root.path());
    assert_eq!(code, 0);
    assert!(output.ends_with(
        "1 of 1 resolved sections checked against an index of their Act: \
         0 found, 1 listed exceptions, 0 absent; 0 in an Act with no index.\n"
    ));
}

#[test]
fn a_hyphen_between_two_indexed_sections_reads_as_a_range() {
    let root = tempfile::tempdir().unwrap();
    index(
        root.path(),
        "C2004A04402",
        "Superannuation Guarantee (Administration) Act 1992",
        &["17A", "17B", "18C"],
    );
    skill(
        root.path(),
        "alpha",
        "See SGAA ss 17A-18C, and ss 17A-19 of the SGAA.\n",
        Some(&record(
            "Superannuation Guarantee (Administration) Act 1992",
            "https://www.legislation.gov.au/C2004A04402/latest/text",
        )),
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections_exist, report.sections_absent), (1, 1));
    assert_eq!(report.unmatched[0].citation, "ss 17A-19");
}

// An Act whose list holds hyphenated schedule sections beside plain body
// sections reads a hyphen as part of a section number, never as a range, so
// a section of another Act cited against it is absent.
#[test]
fn a_hyphen_is_no_range_in_an_act_that_lists_hyphenated_sections() {
    let root = tempfile::tempdir().unwrap();
    index(
        root.path(),
        "C1953A00001",
        "Taxation Administration Act 1953",
        &["1", "8", "12-35"],
    );
    index(
        root.path(),
        "C1936A00027",
        "Income Tax Assessment Act 1936",
        &["45", "202", "265-5"],
    );
    index(
        root.path(),
        "C2004A00818",
        "Corporations Act 2001",
        &["5", "197", "90-15"],
    );
    index(
        root.path(),
        "C2004A04402",
        "Superannuation Guarantee (Administration) Act 1992",
        &["17B", "17D"],
    );
    skill(
        root.path(),
        "alpha",
        "Apply s 8-1 of the TAA 1953.\n\
         Apply s 202-45 of the ITAA 1936.\n\
         Apply s 197-5 of the Corporations Act 2001.\n\
         Apply s 12-35 of Schedule 1 to the TAA 1953.\n\
         Apply SGAA ss 17B-17D.\n",
        Some(
            r#"{"sources": [
  {"title": "Taxation Administration Act 1953", "url": "https://www.legislation.gov.au/C1953A00001/latest/text"},
  {"title": "Income Tax Assessment Act 1936", "url": "https://www.legislation.gov.au/C1936A00027/latest/text"},
  {"title": "Corporations Act 2001", "url": "https://www.legislation.gov.au/C2004A00818/latest/text"},
  {"title": "Superannuation Guarantee (Administration) Act 1992", "url": "https://www.legislation.gov.au/C2004A04402/latest/text"}
]}"#,
        ),
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections_exist, report.sections_absent), (2, 3));
    let absent: Vec<_> = report
        .unmatched
        .iter()
        .map(|missing| (missing.line, missing.citation.as_str()))
        .collect();
    assert_eq!(absent, [(1, "s 8-1"), (2, "s 202-45"), (3, "s 197-5")]);
}

#[test]
fn a_malformed_section_index_or_exception_is_refused() {
    let root = tempfile::tempdir().unwrap();
    skill(
        root.path(),
        "alpha",
        "s 41-5 of the Fuel Tax Act 2006.\n",
        Some(FUEL),
    );
    index(root.path(), "C2006A00072", "Fuel Tax Act 2006", &["41-5"]);
    exceptions(root.path(), "C2099A00009 1: no index for this Act\n");
    let error = check(root.path()).unwrap_err().to_string();
    assert!(
        error.ends_with("no section index for C2099A00009"),
        "{error}"
    );
    exceptions(root.path(), "C2006A00072 41-6:  \n");
    assert!(check(root.path()).is_err());
    exceptions(root.path(), "");
    index(
        root.path(),
        "C2006A00072",
        "Fuel Tax Act 2006",
        &["41-5", "s 41-6"],
    );
    let error = check(root.path()).unwrap_err().to_string();
    assert!(error.ends_with("not a section number: s 41-6"), "{error}");
    let folder = root.path().join("tools/accounting-skills/section-index");
    fs::write(
        folder.join("C2006A00072.txt"),
        "# title: Fuel Tax Act 2006\n41-5\n",
    )
    .unwrap();
    let error = check(root.path()).unwrap_err().to_string();
    assert!(error.ends_with("missing field register-id"), "{error}");
}

// A Federal Register identifier with no year check ties a record to its
// address only through a section list's header, in both directions.
#[test]
fn a_record_whose_title_and_register_id_disagree_with_a_section_list_owns_nothing() {
    let sis = "Superannuation Industry (Supervision) Regulations 1994";
    let root = tempfile::tempdir().unwrap();
    index(root.path(), "F1996B00580", sis, &["8.02B"]);
    skill(
        root.path(),
        "alpha",
        "Apply reg 8.02B of the Superannuation Industry (Supervision) Regulations 1994.\n",
        Some(&record(
            sis,
            "https://www.legislation.gov.au/F2018L01289/latest/text",
        )),
    );
    skill(
        root.path(),
        "beta",
        "Apply reg 8.02B of the Retirement Savings Accounts Regulations 1997.\n",
        Some(&record(
            "Retirement Savings Accounts Regulations 1997",
            "https://www.legislation.gov.au/F1996B00580/latest/text",
        )),
    );
    skill(
        root.path(),
        "gamma",
        "Apply reg 8.02B of the Superannuation Industry (Supervision) Regulations 1994.\n",
        Some(&record(
            sis,
            "https://www.legislation.gov.au/F1996B00580/latest/text",
        )),
    );
    let report = check(root.path()).unwrap();
    assert_eq!((report.sections, report.sections_resolved), (3, 1));
    assert_eq!(report.sections_exist, 1);
    assert_eq!(
        report.unmatched,
        [
            missing(
                ".claude/skills/alpha/SKILL.md",
                1,
                "reg 8.02B",
                "sources.json record 1 ('Superannuation Industry (Supervision) Regulations 1994' \
                 at F2018L01289) disagrees with the section list for F1996B00580 \
                 ('Superannuation Industry (Supervision) Regulations 1994')"
            ),
            missing(
                ".claude/skills/beta/SKILL.md",
                1,
                "reg 8.02B",
                "sources.json record 1 ('Retirement Savings Accounts Regulations 1997' \
                 at F1996B00580) disagrees with the section list for F1996B00580 \
                 ('Superannuation Industry (Supervision) Regulations 1994')"
            ),
        ]
    );
    assert_eq!(run(root.path()).0, 2);
}

#[test]
fn each_malformed_section_list_or_exception_is_refused() {
    let valid = index_text("C2006A00072", "Fuel Tax Act 2006", &["41-5"]);
    let zeros = "0".repeat(64);
    let cases = [
        (
            "C2006A00072.txt",
            valid.replace("# source:", "# title: Fuel Tax Act 2006\n# source:"),
            "",
            "repeated field title",
        ),
        (
            "C2006A00072.txt",
            format!("{valid}41-5\n"),
            "",
            "repeated section 41-5",
        ),
        (
            "C2006A00072.txt",
            format!("# note: extra\n{valid}"),
            "",
            "unknown field note",
        ),
        (
            "C2006A00073.txt",
            valid.clone(),
            "",
            "the file must be named REGISTER-ID.txt",
        ),
        (
            "C2006A00072.txt",
            valid.replace("Fuel Tax Act 2006", "Fuel Tax Act"),
            "",
            "the title must end with its year",
        ),
        (
            "C2006A00072.txt",
            valid.replace(&zeros, "00"),
            "",
            "sha256 must be 64 lower-case hexadecimal digits",
        ),
        (
            "C2006A00072.txt",
            valid.replace("2099-01-02", "2 January 2099"),
            "",
            "retrieved must be a date written YYYY-MM-DD",
        ),
        (
            "C2006A00072.txt",
            valid.replace("2099-01-01", "2099-02-30"),
            "",
            "in-force-from must be a date written YYYY-MM-DD",
        ),
        (
            "C2006A00072.txt",
            valid.clone(),
            "C2006A00072 41-77: proposed\nC2006A00072 41-77: again\n",
            "exceptions.txt:2: repeats the exception on line 1",
        ),
    ];
    for (file, text, exceptions, expected) in cases {
        let root = tempfile::tempdir().unwrap();
        skill(
            root.path(),
            "alpha",
            "s 41-5 of the Fuel Tax Act 2006.\n",
            Some(FUEL),
        );
        let folder = root.path().join("tools/accounting-skills/section-index");
        fs::create_dir_all(&folder).unwrap();
        fs::write(folder.join(file), text).unwrap();
        fs::write(folder.join("exceptions.txt"), exceptions).unwrap();
        let error = check(root.path()).map(|_| ()).unwrap_err().to_string();
        assert!(error.ends_with(expected), "{expected}: {error}");
    }
}
