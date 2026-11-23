// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! OOXML `.docx` workpaper generator with running draft header/footer,
//! metadata table, open review flags callout, structured sections, tables,
//! exception register and primary-sources table.

use crate::{
    model::{DRAFT_BANNER, Workpaper},
    xlsx::xml_escape,
    zip::write_zip,
};
use std::collections::BTreeMap;

fn paragraph(text: &str, style: Option<&str>, bold: bool, colour: Option<&str>) -> String {
    let mut xml = String::from("    <w:p>");
    if let Some(s) = style {
        xml.push_str(&format!("<w:pPr><w:pStyle w:val=\"{s}\"/></w:pPr>"));
    }
    xml.push_str("<w:r>");
    if bold || colour.is_some() {
        xml.push_str("<w:rPr>");
        if bold {
            xml.push_str("<w:b/>");
        }
        if let Some(hex) = colour {
            xml.push_str(&format!("<w:color w:val=\"{hex}\"/>"));
        }
        xml.push_str("</w:rPr>");
    }
    xml.push_str(&format!(
        "<w:t xml:space=\"preserve\">{}</w:t></w:r></w:p>\n",
        xml_escape(text)
    ));
    xml
}

fn shaded_banner(text: &str) -> String {
    format!(
        "    <w:p><w:pPr><w:shd w:val=\"clear\" w:color=\"auto\" w:fill=\"FEF3C7\"/></w:pPr>\
         <w:r><w:rPr><w:b/><w:color w:val=\"92400E\"/></w:rPr>\
         <w:t xml:space=\"preserve\">{}</w:t></w:r></w:p>\n",
        xml_escape(text)
    )
}

fn table_xml(headers: &[String], rows: &[Vec<String>]) -> String {
    let mut xml = String::from(
        "    <w:tbl><w:tblPr><w:tblBorders>\
         <w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"CBD5E1\"/>\
         <w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"CBD5E1\"/>\
         <w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"CBD5E1\"/>\
         <w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"CBD5E1\"/>\
         <w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"E2E8F0\"/>\
         <w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"E2E8F0\"/>\
         </w:tblBorders></w:tblPr>\n",
    );
    if !headers.is_empty() {
        xml.push_str("      <w:tr>\n");
        for h in headers {
            xml.push_str(&format!(
                "        <w:tc><w:tcPr><w:shd w:val=\"clear\" w:color=\"auto\" w:fill=\"1B365D\"/></w:tcPr>\
                 <w:p><w:r><w:rPr><w:b/><w:color w:val=\"FFFFFF\"/></w:rPr>\
                 <w:t xml:space=\"preserve\">{}</w:t></w:r></w:p></w:tc>\n",
                xml_escape(h)
            ));
        }
        xml.push_str("      </w:tr>\n");
    }
    for row in rows {
        xml.push_str("      <w:tr>\n");
        for cell in row {
            xml.push_str(&format!(
                "        <w:tc><w:p><w:r><w:t xml:space=\"preserve\">{}</w:t></w:r></w:p></w:tc>\n",
                xml_escape(cell)
            ));
        }
        xml.push_str("      </w:tr>\n");
    }
    xml.push_str("    </w:tbl>\n");
    xml
}

pub fn render_docx(wp: &Workpaper) -> Result<Vec<u8>, String> {
    let mut body = String::new();
    body.push_str(&shaded_banner(DRAFT_BANNER));
    body.push_str(&paragraph(
        &wp.title,
        Some("Heading1"),
        true,
        Some("1B365D"),
    ));

    let meta_rows = vec![
        vec!["Entity code".to_owned(), wp.entity_code.clone()],
        vec!["Period".to_owned(), wp.period.clone()],
        vec!["Status".to_owned(), wp.status.clone()],
        vec!["Prepared on".to_owned(), wp.prepared_on.clone()],
        vec!["Reviewer".to_owned(), wp.reviewer.clone()],
        vec![
            "Open review items".to_owned(),
            format!(
                "{} exceptions, {} UNVERIFIED mentions",
                wp.exceptions.len(),
                wp.unverified_mentions()
            ),
        ],
    ];
    body.push_str(&table_xml(
        &["Field".to_owned(), "Detail".to_owned()],
        &meta_rows,
    ));

    if !wp.exceptions.is_empty() || wp.unverified_mentions() > 0 {
        body.push_str(&shaded_banner(&format!(
            "OPEN REVIEW ITEMS PRESENT: {} exception(s), {} UNVERIFIED item(s). Reviewer sign-off required before any external use.",
            wp.exceptions.len(),
            wp.unverified_mentions()
        )));
    }

    if !wp.summary.is_empty() {
        body.push_str(&paragraph(
            "Summary",
            Some("Heading2"),
            true,
            Some("1B365D"),
        ));
        body.push_str(&paragraph(&wp.summary, None, false, None));
    }

    for section in &wp.sections {
        body.push_str(&paragraph(
            &section.heading,
            Some("Heading2"),
            true,
            Some("1B365D"),
        ));
        for p in &section.paragraphs {
            body.push_str(&paragraph(p, None, false, None));
        }
        for b in &section.bullets {
            body.push_str(&paragraph(&format!("- {b}"), None, false, None));
        }
        if let Some(tbl) = &section.table {
            body.push_str(&table_xml(&tbl.headers, &tbl.rows));
        }
    }

    if !wp.exceptions.is_empty() {
        body.push_str(&paragraph(
            "Reviewer exception register",
            Some("Heading2"),
            true,
            Some("1B365D"),
        ));
        let rows: Vec<Vec<String>> = wp
            .exceptions
            .iter()
            .enumerate()
            .map(|(i, e)| {
                vec![
                    if e.id.is_empty() {
                        format!("EXC-{}", i + 1)
                    } else {
                        e.id.clone()
                    },
                    e.item.clone(),
                    e.status.clone(),
                    e.evidence_needed.clone(),
                    e.owner.clone(),
                ]
            })
            .collect();
        body.push_str(&table_xml(
            &[
                "ID".to_owned(),
                "Item".to_owned(),
                "Status".to_owned(),
                "Evidence needed".to_owned(),
                "Owner".to_owned(),
            ],
            &rows,
        ));
    }

    if !wp.sources.is_empty() {
        body.push_str(&paragraph(
            "Primary sources checked",
            Some("Heading2"),
            true,
            Some("1B365D"),
        ));
        let rows: Vec<Vec<String>> = wp
            .sources
            .iter()
            .map(|s| {
                vec![
                    s.title.clone(),
                    s.reference.clone(),
                    s.checked_at.clone(),
                    s.status.clone(),
                ]
            })
            .collect();
        body.push_str(&table_xml(
            &[
                "Source".to_owned(),
                "Reference".to_owned(),
                "Checked on".to_owned(),
                "Status".to_owned(),
            ],
            &rows,
        ));
    }

    let document_xml = format!(
        r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
{body}    <w:sectPr>
      <w:headerReference w:type="default" r:id="rId1"/>
      <w:footerReference w:type="default" r:id="rId2"/>
    </w:sectPr>
  </w:body>
</w:document>
"#
    );

    let header_xml = format!(
        r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="92400E"/></w:rPr><w:t>{}</w:t></w:r></w:p>
</w:hdr>
"#,
        xml_escape(DRAFT_BANNER)
    );

    let footer_xml = format!(
        r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:r><w:rPr><w:sz w:val="18"/><w:color w:val="64748B"/></w:rPr><w:t>{} | Prep workpaper only; authorised human reviews and decides.</w:t></w:r></w:p>
</w:ftr>
"#,
        xml_escape(&wp.title)
    );

    let styles_xml = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:rPr><w:b/><w:sz w:val="32"/><w:color w:val="1B365D"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:rPr><w:b/><w:sz w:val="26"/><w:color w:val="1B365D"/></w:rPr>
  </w:style>
</w:styles>
"#;

    let mut files: BTreeMap<String, Vec<u8>> = BTreeMap::new();
    files.insert(
        "[Content_Types].xml".to_owned(),
        br#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>
"#
        .to_vec(),
    );
    files.insert(
        "_rels/.rels".to_owned(),
        br#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"#
        .to_vec(),
    );
    files.insert(
        "word/_rels/document.xml.rels".to_owned(),
        br#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"#
        .to_vec(),
    );
    files.insert("word/document.xml".to_owned(), document_xml.into_bytes());
    files.insert("word/styles.xml".to_owned(), styles_xml.as_bytes().to_vec());
    files.insert("word/header1.xml".to_owned(), header_xml.into_bytes());
    files.insert("word/footer1.xml".to_owned(), footer_xml.into_bytes());

    write_zip(&files)
}
