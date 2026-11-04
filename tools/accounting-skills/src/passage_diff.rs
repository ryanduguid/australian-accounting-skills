//! Bounded equivalent of Python 3.14.8 difflib's default SequenceMatcher and
//! unified_diff (no junk callback, autojunk enabled, two context lines).
//! Algorithm derived from CPython Lib/difflib.py, under PYTHON-LICENSE.txt.
use std::collections::HashMap;

#[derive(Clone, Copy)]
struct Code {
    tag: char,
    i: usize,
    end_i: usize,
    j: usize,
    end_j: usize,
}

fn longest(
    a: &[&str],
    b: &[&str],
    positions: &HashMap<&str, Vec<usize>>,
    (alo, ahi, blo, bhi): (usize, usize, usize, usize),
) -> (usize, usize, usize) {
    let (mut best_i, mut best_j, mut size) = (alo, blo, 0);
    let mut lengths = HashMap::new();
    for (i, line) in a.iter().enumerate().take(ahi).skip(alo) {
        let mut next = HashMap::new();
        for &j in positions.get(line).into_iter().flatten() {
            if j < blo {
                continue;
            }
            if j >= bhi {
                break;
            }
            let k = j
                .checked_sub(1)
                .and_then(|p| lengths.get(&p))
                .copied()
                .unwrap_or(0)
                + 1;
            next.insert(j, k);
            if k > size {
                (best_i, best_j, size) = (i + 1 - k, j + 1 - k, k);
            }
        }
        lengths = next;
    }
    // Popular elements are excluded from the search, but can extend a match.
    while best_i > alo && best_j > blo && a[best_i - 1] == b[best_j - 1] {
        best_i -= 1;
        best_j -= 1;
        size += 1;
    }
    while best_i + size < ahi && best_j + size < bhi && a[best_i + size] == b[best_j + size] {
        size += 1;
    }
    (best_i, best_j, size)
}

fn opcodes(a: &[&str], b: &[&str]) -> Vec<Code> {
    let mut positions: HashMap<&str, Vec<usize>> = HashMap::new();
    for (j, line) in b.iter().enumerate() {
        positions.entry(line).or_default().push(j);
    }
    if b.len() >= 200 {
        let threshold = b.len() / 100 + 1;
        positions.retain(|_, indices| indices.len() <= threshold);
    }
    let mut queue = vec![(0, a.len(), 0, b.len())];
    let mut matches = Vec::new();
    while let Some(bounds @ (alo, ahi, blo, bhi)) = queue.pop() {
        let (i, j, size) = longest(a, b, &positions, bounds);
        if size > 0 {
            matches.push((i, j, size));
            if alo < i && blo < j {
                queue.push((alo, i, blo, j));
            }
            if i + size < ahi && j + size < bhi {
                queue.push((i + size, ahi, j + size, bhi));
            }
        }
    }
    matches.sort_unstable();
    let mut blocks: Vec<(usize, usize, usize)> = Vec::new();
    for (i, j, size) in matches {
        if let Some(last) = blocks.last_mut()
            && last.0 + last.2 == i
            && last.1 + last.2 == j
        {
            last.2 += size;
            continue;
        }
        blocks.push((i, j, size));
    }
    blocks.push((a.len(), b.len(), 0));
    let (mut i, mut j) = (0, 0);
    let mut codes = Vec::new();
    for (ai, bj, size) in blocks {
        let tag = match (i < ai, j < bj) {
            (true, true) => 'r',
            (true, false) => 'd',
            (false, true) => 'i',
            _ => ' ',
        };
        if tag != ' ' {
            codes.push(Code {
                tag,
                i,
                end_i: ai,
                j,
                end_j: bj,
            });
        }
        (i, j) = (ai + size, bj + size);
        if size > 0 {
            codes.push(Code {
                tag: 'e',
                i: ai,
                end_i: i,
                j: bj,
                end_j: j,
            });
        }
    }
    codes
}

fn groups(mut codes: Vec<Code>) -> Vec<Vec<Code>> {
    if codes.is_empty() {
        return Vec::new();
    }
    let first = codes.first_mut().unwrap();
    if first.tag == 'e' {
        first.i = first.i.max(first.end_i.saturating_sub(2));
        first.j = first.j.max(first.end_j.saturating_sub(2));
    }
    let last = codes.last_mut().unwrap();
    if last.tag == 'e' {
        last.end_i = last.end_i.min(last.i + 2);
        last.end_j = last.end_j.min(last.j + 2);
    }
    let mut groups = Vec::new();
    let mut group = Vec::new();
    for mut code in codes {
        if code.tag == 'e' && code.end_i - code.i > 4 {
            group.push(Code {
                end_i: code.i + 2,
                end_j: code.j + 2,
                ..code
            });
            groups.push(group);
            group = Vec::new();
            code.i = code.end_i - 2;
            code.j = code.end_j - 2;
        }
        group.push(code);
    }
    if !group.is_empty() && !(group.len() == 1 && group[0].tag == 'e') {
        groups.push(group);
    }
    groups
}

fn range(start: usize, stop: usize) -> String {
    match stop - start {
        0 => format!("{start},0"),
        1 => (start + 1).to_string(),
        size => format!("{},{size}", start + 1),
    }
}

pub(crate) fn unified(a: &[&str], b: &[&str]) -> Vec<String> {
    let groups = groups(opcodes(a, b));
    let mut lines = Vec::new();
    if !groups.is_empty() {
        lines.extend(["--- before".into(), "+++ after".into()]);
    }
    for group in groups {
        let first = group.first().unwrap();
        let last = group.last().unwrap();
        lines.push(format!(
            "@@ -{} +{} @@",
            range(first.i, last.end_i),
            range(first.j, last.end_j)
        ));
        for code in group {
            if code.tag == 'e' {
                lines.extend(a[code.i..code.end_i].iter().map(|line| format!(" {line}")));
            } else {
                if matches!(code.tag, 'd' | 'r') {
                    lines.extend(a[code.i..code.end_i].iter().map(|line| format!("-{line}")));
                }
                if matches!(code.tag, 'i' | 'r') {
                    lines.extend(b[code.j..code.end_j].iter().map(|line| format!("+{line}")));
                }
            }
        }
    }
    lines
}

pub(crate) fn splitlines(text: &str) -> Vec<&str> {
    let mut lines = Vec::new();
    let mut start = 0;
    let mut chars = text.char_indices().peekable();
    while let Some((i, ch)) = chars.next() {
        if matches!(
            ch,
            '\n' | '\r' | '\u{b}' | '\u{c}' | '\u{1c}'
                ..='\u{1e}' | '\u{85}' | '\u{2028}' | '\u{2029}'
        ) {
            lines.push(&text[start..i]);
            start = i + ch.len_utf8();
            if ch == '\r' && chars.peek().is_some_and(|(_, next)| *next == '\n') {
                start = chars.next().unwrap().0 + 1;
            }
        }
    }
    if start < text.len() {
        lines.push(&text[start..]);
    }
    lines
}
