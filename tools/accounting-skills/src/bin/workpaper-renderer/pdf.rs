// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Pure-Rust PDF 1.4 workpaper renderer with A4 pages, multi-page pagination,
//! running `DRAFT FOR HUMAN REVIEW` header, page-numbered footer, wrapped
//! paragraphs, bullet lists and structured tables.

use crate::model::{DRAFT_BANNER, Workpaper};

const PAGE_WIDTH: f32 = 595.0;
const PAGE_HEIGHT: f32 = 842.0;
const MARGIN_X: f32 = 50.0;
const TOP_Y: f32 = 775.0;
const BOTTOM_Y: f32 = 60.0;

fn pdf_escape(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    for ch in text.chars() {
        let mapped = match ch {
            '\u{2013}' | '\u{2014}' => '-',
            '\u{2018}' | '\u{2019}' => '\'',
            '\u{201C}' | '\u{201D}' => '"',
            '\u{2022}' => '*',
            c if c.is_ascii() && (c as u32) >= 0x20 => c,
            '\t' => ' ',
            _ => '?',
        };
        match mapped {
            '\\' => out.push_str("\\\\"),
            '(' => out.push_str("\\("),
            ')' => out.push_str("\\)"),
            c => out.push(c),
        }
    }
    out
}

fn wrap_text(text: &str, max_chars: usize) -> Vec<String> {
    let mut lines = Vec::new();
    let mut current = String::new();
    for word in text.split_whitespace() {
        if current.is_empty() {
            current.push_str(word);
        } else if current.len() + 1 + word.len() <= max_chars {
            current.push(' ');
            current.push_str(word);
        } else {
            lines.push(current);
            current = word.to_owned();
        }
    }
    if !current.is_empty() || lines.is_empty() {
        lines.push(current);
    }
    lines
}

fn assemble_pdf(objects: &[String]) -> Vec<u8> {
    let mut pdf = Vec::new();
    pdf.extend_from_slice(b"%PDF-1.4\n");
    let mut offsets = Vec::with_capacity(objects.len() + 1);
    offsets.push(0usize);
    for (i, body) in objects.iter().enumerate() {
        offsets.push(pdf.len());
        pdf.extend_from_slice(format!("{} 0 obj\n{body}\nendobj\n", i + 1).as_bytes());
    }
    let xref_pos = pdf.len();
    pdf.extend_from_slice(format!("xref\n0 {}\n", objects.len() + 1).as_bytes());
    pdf.extend_from_slice(b"0000000000 65535 f \n");
    for offset in offsets.iter().skip(1) {
        pdf.extend_from_slice(format!("{offset:010} 00000 n \n").as_bytes());
    }
    pdf.extend_from_slice(
        format!(
            "trailer\n<< /Size {} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n",
            objects.len() + 1
        )
        .as_bytes(),
    );
    pdf
}

struct PdfBuilder {
    pages: Vec<String>,
    current: String,
    y: f32,
}

impl PdfBuilder {
    fn new() -> Self {
        Self {
            pages: Vec::new(),
            current: String::new(),
            y: TOP_Y,
        }
    }

    fn ensure_space(&mut self, needed: f32) {
        if self.y - needed < BOTTOM_Y {
            let finished = std::mem::take(&mut self.current);
            self.pages.push(finished);
            self.y = TOP_Y;
        }
    }

    fn write_line(&mut self, text: &str, font: &str, size: f32, rgb: (f32, f32, f32)) {
        let step = size + 4.0;
        self.ensure_space(step);
        self.current.push_str(&format!(
            "BT /{font} {size:.1} Tf {:.2} {:.2} {:.2} rg {MARGIN_X:.1} {:.1} Td ({}) Tj ET\n",
            rgb.0,
            rgb.1,
            rgb.2,
            self.y,
            pdf_escape(text)
        ));
        self.y -= step;
    }

    fn write_wrapped(&mut self, text: &str, font: &str, size: f32, max_chars: usize) {
        for line in wrap_text(text, max_chars) {
            self.write_line(&line, font, size, (0.12, 0.16, 0.22));
        }
    }

    fn write_table(&mut self, headers: &[String], rows: &[Vec<String>]) {
        if !headers.is_empty() {
            self.write_line(&headers.join(" | "), "F2", 9.5, (0.11, 0.21, 0.36));
        }
        for row in rows {
            for wrapped in wrap_text(&row.join(" | "), 92) {
                self.write_line(&wrapped, "F1", 9.0, (0.12, 0.16, 0.22));
            }
        }
        self.y -= 6.0;
    }

    fn build_objects(&self, title: &str) -> Vec<String> {
        let total = self.pages.len();
        let mut objects = Vec::with_capacity(4 + total * 2);
        objects.push("<< /Type /Catalog /Pages 2 0 R >>".to_owned());
        let kids: String = (0..total).map(|i| format!("{} 0 R ", 5 + i * 2)).collect();
        objects.push(format!("<< /Type /Pages /Kids [ {kids}] /Count {total} >>"));
        objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>".to_owned());
        objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>".to_owned());
        for (idx, body) in self.pages.iter().enumerate() {
            let content_obj = 6 + idx * 2;
            let header = format!(
                "0.99 0.95 0.78 rg {MARGIN_X:.1} 800.0 {:.1} 20.0 re f\n\
                 BT /F2 8.5 Tf 0.57 0.25 0.05 rg {:.1} 807.0 Td ({}) Tj ET\n",
                PAGE_WIDTH - 2.0 * MARGIN_X,
                MARGIN_X + 6.0,
                pdf_escape(DRAFT_BANNER)
            );
            let footer = format!(
                "BT /F1 8.0 Tf 0.40 0.45 0.55 rg {MARGIN_X:.1} 30.0 Td ({} - Page {} of {total}) Tj ET\n",
                pdf_escape(title),
                idx + 1
            );
            let stream = format!("{header}{body}{footer}");
            objects.push(format!(
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH:.0} {PAGE_HEIGHT:.0}] \
                 /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_obj} 0 R >>"
            ));
            objects.push(format!(
                "<< /Length {} >>\nstream\n{stream}endstream",
                stream.len()
            ));
        }
        objects
    }

    fn finish(mut self, title: &str) -> Vec<u8> {
        if !self.current.is_empty() || self.pages.is_empty() {
            self.pages.push(std::mem::take(&mut self.current));
        }
        assemble_pdf(&self.build_objects(title))
    }
}

fn write_exceptions(pdf: &mut PdfBuilder, wp: &Workpaper) {
    if wp.exceptions.is_empty() {
        return;
    }
    pdf.write_line(
        "Reviewer exception register",
        "F2",
        12.0,
        (0.11, 0.21, 0.36),
    );
    let rows: Vec<Vec<String>> = wp
        .exceptions
        .iter()
        .enumerate()
        .map(|(i, e)| {
            let id = if e.id.is_empty() {
                format!("EXC-{}", i + 1)
            } else {
                e.id.clone()
            };
            vec![
                id,
                e.item.clone(),
                e.status.clone(),
                e.evidence_needed.clone(),
                e.owner.clone(),
            ]
        })
        .collect();
    let headers = ["ID", "Item", "Status", "Evidence needed", "Owner"]
        .map(str::to_owned)
        .to_vec();
    pdf.write_table(&headers, &rows);
}

fn write_sources(pdf: &mut PdfBuilder, wp: &Workpaper) {
    if wp.sources.is_empty() {
        return;
    }
    pdf.write_line("Primary sources checked", "F2", 12.0, (0.11, 0.21, 0.36));
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
    let headers = ["Source", "Reference", "Checked on", "Status"]
        .map(str::to_owned)
        .to_vec();
    pdf.write_table(&headers, &rows);
}

fn write_registers(pdf: &mut PdfBuilder, wp: &Workpaper) {
    write_exceptions(pdf, wp);
    write_sources(pdf, wp);
}

pub fn render_pdf(wp: &Workpaper) -> Vec<u8> {
    let mut pdf = PdfBuilder::new();
    pdf.write_line(&wp.title, "F2", 16.0, (0.11, 0.21, 0.36));
    pdf.y -= 4.0;
    pdf.write_line(
        &format!(
            "Entity: {} | Period: {} | Status: {} | Prepared: {} | Reviewer: {}",
            wp.entity_code, wp.period, wp.status, wp.prepared_on, wp.reviewer
        ),
        "F1",
        9.5,
        (0.25, 0.30, 0.38),
    );
    let unverified = wp.unverified_mentions();
    if !wp.exceptions.is_empty() || unverified > 0 {
        pdf.write_line(
            &format!(
                "OPEN REVIEW ITEMS: {} exception(s), {unverified} UNVERIFIED mention(s).",
                wp.exceptions.len()
            ),
            "F2",
            9.5,
            (0.57, 0.25, 0.05),
        );
    }
    pdf.y -= 6.0;
    if !wp.summary.is_empty() {
        pdf.write_line("Summary", "F2", 12.0, (0.11, 0.21, 0.36));
        pdf.write_wrapped(&wp.summary, "F1", 10.0, 88);
        pdf.y -= 6.0;
    }
    for section in &wp.sections {
        pdf.write_line(&section.heading, "F2", 12.0, (0.11, 0.21, 0.36));
        for p in &section.paragraphs {
            pdf.write_wrapped(p, "F1", 10.0, 88);
        }
        for b in &section.bullets {
            pdf.write_wrapped(&format!("- {b}"), "F1", 10.0, 86);
        }
        if let Some(tbl) = &section.table {
            pdf.write_table(&tbl.headers, &tbl.rows);
        }
        pdf.y -= 4.0;
    }
    write_registers(&mut pdf, wp);
    pdf.finish(&wp.title)
}
