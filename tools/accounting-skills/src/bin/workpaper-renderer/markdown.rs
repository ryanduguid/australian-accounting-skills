// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Parse a Markdown workpaper (optional `---` front matter, headings,
//! paragraphs, bullet lists and pipe tables) into a [`Workpaper`].

use crate::model::{CellSpec, ExceptionItem, Section, Sheet, TextTable, Workpaper};

fn strip_quotes(value: &str) -> String {
    let trimmed = value.trim();
    if trimmed.len() >= 2
        && ((trimmed.starts_with('"') && trimmed.ends_with('"'))
            || (trimmed.starts_with('\'') && trimmed.ends_with('\'')))
    {
        trimmed[1..trimmed.len() - 1].to_owned()
    } else {
        trimmed.to_owned()
    }
}

fn is_separator_row(line: &str) -> bool {
    let trimmed = line.trim().trim_matches('|');
    !trimmed.is_empty()
        && trimmed.split('|').all(|cell| {
            let cell = cell.trim();
            !cell.is_empty()
                && cell.bytes().all(|b| matches!(b, b'-' | b':' | b' '))
                && cell.contains('-')
        })
}

fn split_pipe_row(line: &str) -> Vec<String> {
    let trimmed = line.trim();
    let inner = trimmed.strip_prefix('|').unwrap_or(trimmed);
    let inner = inner.strip_suffix('|').unwrap_or(inner);
    inner
        .split('|')
        .map(|cell| cell.trim().to_owned())
        .collect()
}

fn parse_cell_from_markdown(text: &str) -> CellSpec {
    let trimmed = text.trim();
    let numeric = trimmed
        .strip_prefix('$')
        .unwrap_or(trimmed)
        .replace(',', "");
    if !numeric.is_empty()
        && !trimmed.starts_with('=')
        && let Ok(value) = numeric.parse::<f64>()
        && value.is_finite()
    {
        return CellSpec::Number(value);
    }
    CellSpec::Text(trimmed.to_owned())
}

fn parse_front_matter(lines: &[&str], wp: &mut Workpaper) -> usize {
    if lines.first().copied() != Some("---") {
        return 0;
    }
    let Some(end_offset) = lines[1..].iter().position(|line| *line == "---") else {
        return 0;
    };
    for line in &lines[1..1 + end_offset] {
        if let Some((key, value)) = line.split_once(':') {
            let value = strip_quotes(value);
            match key.trim() {
                "title" => wp.title = value,
                "entity_code" | "entity" => wp.entity_code = value,
                "period" => wp.period = value,
                "prepared_on" => wp.prepared_on = value,
                "reviewer" => wp.reviewer = value,
                "status" if !value.is_empty() => wp.status = value,
                "summary" => wp.summary = value,
                _ => {}
            }
        }
    }
    end_offset + 2
}

struct ParserState {
    wp: Workpaper,
    current: Section,
    has_section: bool,
    paragraph_buf: Vec<String>,
}

impl ParserState {
    fn flush_paragraph(&mut self) {
        if self.paragraph_buf.is_empty() {
            return;
        }
        let joined = self.paragraph_buf.join(" ");
        self.paragraph_buf.clear();
        if self.has_section {
            self.current.paragraphs.push(joined);
        } else if self.wp.summary.is_empty() {
            self.wp.summary = joined;
        } else {
            self.wp.summary.push(' ');
            self.wp.summary.push_str(&joined);
        }
    }

    fn ensure_section(&mut self, default_heading: &str) {
        if !self.has_section {
            self.current.heading = default_heading.to_owned();
            self.has_section = true;
        }
    }

    fn consume_table(&mut self, lines: &[&str], start: usize) -> usize {
        self.flush_paragraph();
        self.ensure_section("Schedule");
        let headers = split_pipe_row(lines[start].trim());
        let mut index = start + 2;
        let mut rows = Vec::new();
        while index < lines.len() {
            let row_line = lines[index].trim();
            if row_line.is_empty() || !row_line.contains('|') {
                break;
            }
            rows.push(split_pipe_row(row_line));
            index += 1;
        }
        let sheet_rows = rows
            .iter()
            .map(|row| row.iter().map(|c| parse_cell_from_markdown(c)).collect())
            .collect();
        let sheet_name = if self.current.heading.is_empty() {
            format!("Schedule {}", self.wp.sheets.len() + 1)
        } else {
            self.current.heading.clone()
        };
        self.wp.sheets.push(Sheet {
            name: sheet_name,
            headers: headers.clone(),
            rows: sheet_rows,
        });
        self.current.table = Some(TextTable { headers, rows });
        index
    }

    fn consume_bullet(&mut self, item: &str) {
        self.flush_paragraph();
        self.ensure_section("Notes");
        let text = item.trim().to_owned();
        if self
            .current
            .heading
            .to_ascii_lowercase()
            .contains("exception")
            || text.contains("UNVERIFIED")
        {
            self.wp.exceptions.push(ExceptionItem {
                id: format!("EXC-{}", self.wp.exceptions.len() + 1),
                item: text.clone(),
                status: if text.contains("UNVERIFIED") {
                    "UNVERIFIED".to_owned()
                } else {
                    "OPEN".to_owned()
                },
                evidence_needed: String::new(),
                owner: "Reviewer".to_owned(),
            });
        }
        self.current.bullets.push(text);
    }
}

impl ParserState {
    fn step_line(&mut self, lines: &[&str], index: usize) -> usize {
        let trimmed = lines[index].trim();
        if trimmed.is_empty() {
            self.flush_paragraph();
        } else if let Some(title) = trimmed.strip_prefix("# ")
            && self.wp.title.is_empty()
        {
            self.flush_paragraph();
            self.wp.title = title.trim().to_owned();
        } else if let Some(heading) = trimmed
            .strip_prefix("## ")
            .or_else(|| trimmed.strip_prefix("### "))
        {
            self.flush_paragraph();
            if self.has_section {
                self.wp.sections.push(std::mem::take(&mut self.current));
            }
            self.current.heading = heading.trim().to_owned();
            self.has_section = true;
        } else if trimmed.contains('|')
            && index + 1 < lines.len()
            && is_separator_row(lines[index + 1])
        {
            return self.consume_table(lines, index);
        } else if let Some(item) = trimmed
            .strip_prefix("- ")
            .or_else(|| trimmed.strip_prefix("* "))
        {
            self.consume_bullet(item);
        } else {
            self.paragraph_buf.push(trimmed.to_owned());
        }
        index + 1
    }
}

pub fn parse_markdown(input: &str) -> Workpaper {
    let mut state = ParserState {
        wp: Workpaper {
            status: "DRAFT_FOR_REVIEW".to_owned(),
            ..Default::default()
        },
        current: Section::default(),
        has_section: false,
        paragraph_buf: Vec::new(),
    };
    let lines: Vec<&str> = input.lines().collect();
    let mut index = parse_front_matter(&lines, &mut state.wp);
    while index < lines.len() {
        index = state.step_line(&lines, index);
    }
    state.flush_paragraph();
    if state.has_section {
        state.wp.sections.push(state.current);
    }
    if state.wp.title.is_empty() {
        state.wp.title = "Workpaper draft".to_owned();
    }
    state.wp
}
