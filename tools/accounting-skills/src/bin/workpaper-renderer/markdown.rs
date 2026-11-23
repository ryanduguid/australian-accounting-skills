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
    if trimmed.is_empty() {
        return false;
    }
    trimmed.split('|').all(|cell| {
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

pub fn parse_markdown(input: &str) -> Workpaper {
    let mut wp = Workpaper {
        status: "DRAFT_FOR_REVIEW".to_owned(),
        ..Default::default()
    };
    let lines: Vec<&str> = input.lines().collect();
    let mut index = 0;

    if lines.first().copied() == Some("---")
        && let Some(end_offset) = lines[1..].iter().position(|line| *line == "---")
    {
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
        index = end_offset + 2;
    }

    let mut current = Section::default();
    let mut has_section = false;
    let mut paragraph_buf: Vec<String> = Vec::new();

    let flush_paragraph =
        |buf: &mut Vec<String>, wp: &mut Workpaper, current: &mut Section, has_section: bool| {
            if buf.is_empty() {
                return;
            }
            let joined = buf.join(" ");
            buf.clear();
            if has_section {
                current.paragraphs.push(joined);
            } else if wp.summary.is_empty() {
                wp.summary = joined;
            } else {
                wp.summary.push(' ');
                wp.summary.push_str(&joined);
            }
        };

    while index < lines.len() {
        let line = lines[index];
        let trimmed = line.trim();

        if trimmed.is_empty() {
            flush_paragraph(&mut paragraph_buf, &mut wp, &mut current, has_section);
            index += 1;
            continue;
        }

        if let Some(title) = trimmed.strip_prefix("# ")
            && wp.title.is_empty()
        {
            flush_paragraph(&mut paragraph_buf, &mut wp, &mut current, has_section);
            wp.title = title.trim().to_owned();
            index += 1;
            continue;
        }

        if let Some(heading) = trimmed
            .strip_prefix("## ")
            .or_else(|| trimmed.strip_prefix("### "))
        {
            flush_paragraph(&mut paragraph_buf, &mut wp, &mut current, has_section);
            if has_section {
                wp.sections.push(current);
            }
            current = Section {
                heading: heading.trim().to_owned(),
                ..Default::default()
            };
            has_section = true;
            index += 1;
            continue;
        }

        if trimmed.contains('|') && index + 1 < lines.len() && is_separator_row(lines[index + 1]) {
            flush_paragraph(&mut paragraph_buf, &mut wp, &mut current, has_section);
            if !has_section {
                current.heading = "Schedule".to_owned();
                has_section = true;
            }
            let headers = split_pipe_row(trimmed);
            index += 2;
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
            let sheet_name = if current.heading.is_empty() {
                format!("Schedule {}", wp.sheets.len() + 1)
            } else {
                current.heading.clone()
            };
            wp.sheets.push(Sheet {
                name: sheet_name,
                headers: headers.clone(),
                rows: sheet_rows,
            });
            current.table = Some(TextTable { headers, rows });
            continue;
        }

        if let Some(item) = trimmed
            .strip_prefix("- ")
            .or_else(|| trimmed.strip_prefix("* "))
        {
            flush_paragraph(&mut paragraph_buf, &mut wp, &mut current, has_section);
            if !has_section {
                current.heading = "Notes".to_owned();
                has_section = true;
            }
            let text = item.trim().to_owned();
            if current.heading.to_ascii_lowercase().contains("exception")
                || text.contains("UNVERIFIED")
            {
                wp.exceptions.push(ExceptionItem {
                    id: format!("EXC-{}", wp.exceptions.len() + 1),
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
            current.bullets.push(text);
            index += 1;
            continue;
        }

        paragraph_buf.push(trimmed.to_owned());
        index += 1;
    }

    flush_paragraph(&mut paragraph_buf, &mut wp, &mut current, has_section);
    if has_section {
        wp.sections.push(current);
    }
    if wp.title.is_empty() {
        wp.title = "Workpaper draft".to_owned();
    }
    wp
}
