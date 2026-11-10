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
    assert_eq!((report.sections, report.sections_resolved), (5, 2));
    let alpha = ".claude/skills/alpha/SKILL.md";
    let beta = ".claude/skills/beta/SKILL.md";
    assert_eq!(
        report.unmatched,
        [
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
    assert!(
        output.starts_with(".claude/skills/alpha/SKILL.md:3: PCG 2016/8: no record names it\n")
    );
    assert!(output.ends_with(
        "3 of 7 citations resolve to a sources.json record: \
         1 of 2 rulings and guidance, 2 of 5 legislative sections.\n"
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
         The fuel must be acquired (s 41-10).\n",
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
    assert_eq!((report.sections, report.sections_resolved), (4, 3));
    assert_eq!(
        report.unmatched,
        [missing(
            ".claude/skills/alpha/SKILL.md",
            1,
            "s 50",
            "no record names its Act (Corporations Act 2001)"
        )]
    );
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
