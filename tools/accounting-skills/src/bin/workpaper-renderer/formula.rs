// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Spreadsheet cell coordinates, tokenizer and recursive-descent parser for
//! deterministic `.xlsx` formula verification.

use crate::formula_funcs::{ArgValue, DISALLOWED_FUNCTIONS, Value, compare_values, eval_function};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct CellCoord {
    pub sheet: String,
    pub row: usize,
    pub col: usize,
}

#[derive(Debug, Clone)]
pub enum GridCell {
    Number(f64),
    Text(String),
    Bool(bool),
    Formula(String),
    Error(String),
}

pub fn col_to_letters(mut col: usize) -> String {
    let mut out = Vec::new();
    loop {
        out.push(b'A' + (col % 26) as u8);
        if col < 26 {
            break;
        }
        col = col / 26 - 1;
    }
    out.reverse();
    String::from_utf8(out).unwrap_or_default()
}

pub fn cell_ref(row: usize, col: usize) -> String {
    format!("{}{}", col_to_letters(col), row + 1)
}

pub fn parse_cell_ref(token: &str) -> Option<(usize, usize)> {
    let clean: String = token.chars().filter(|c| *c != '$').collect();
    let split = clean.find(|c: char| c.is_ascii_digit())?;
    if split == 0 {
        return None;
    }
    let letters = &clean[..split];
    let digits = &clean[split..];
    if !letters.bytes().all(|b| b.is_ascii_alphabetic())
        || !digits.bytes().all(|b| b.is_ascii_digit())
    {
        return None;
    }
    let mut col: usize = 0;
    for b in letters.bytes() {
        let idx = usize::from(b.to_ascii_uppercase() - b'A') + 1;
        col = col.checked_mul(26)?.checked_add(idx)?;
    }
    let row = digits.parse::<usize>().ok()?;
    if row == 0 || col == 0 {
        return None;
    }
    Some((row - 1, col - 1))
}

#[derive(Debug, Clone, PartialEq)]
enum Token {
    Number(f64),
    String(String),
    Ident(String),
    QuotedSheet(String),
    Plus,
    Minus,
    Star,
    Slash,
    LParen,
    RParen,
    Comma,
    Colon,
    Bang,
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
}

fn read_quoted(
    chars: &[char],
    start: usize,
    quote: char,
    err: &str,
) -> Result<(String, usize), String> {
    let mut i = start + 1;
    let mut s = String::new();
    while i < chars.len() {
        if chars[i] == quote {
            if i + 1 < chars.len() && chars[i + 1] == quote {
                s.push(quote);
                i += 2;
            } else {
                return Ok((s, i + 1));
            }
        } else {
            s.push(chars[i]);
            i += 1;
        }
    }
    Err(err.to_owned())
}

fn read_punctuation(chars: &[char], i: usize) -> Option<(Token, usize)> {
    let tok = match chars[i] {
        '+' => (Token::Plus, 1),
        '-' => (Token::Minus, 1),
        '*' => (Token::Star, 1),
        '/' => (Token::Slash, 1),
        '(' => (Token::LParen, 1),
        ')' => (Token::RParen, 1),
        ',' => (Token::Comma, 1),
        ':' => (Token::Colon, 1),
        '!' => (Token::Bang, 1),
        '=' => (Token::Eq, 1),
        '<' if chars.get(i + 1) == Some(&'=') => (Token::Le, 2),
        '<' if chars.get(i + 1) == Some(&'>') => (Token::Ne, 2),
        '<' => (Token::Lt, 1),
        '>' if chars.get(i + 1) == Some(&'=') => (Token::Ge, 2),
        '>' => (Token::Gt, 1),
        _ => return None,
    };
    Some((tok.0, i + tok.1))
}

fn read_atom(chars: &[char], start: usize) -> Result<(Token, usize), String> {
    let mut i = start;
    if chars[i] == '"' {
        let (s, next) = read_quoted(chars, i, '"', "#VALUE!: unterminated string literal")?;
        return Ok((Token::String(s), next));
    }
    if chars[i] == '\'' {
        let (s, next) = read_quoted(chars, i, '\'', "#NAME?: unterminated sheet name")?;
        return Ok((Token::QuotedSheet(s), next));
    }
    if chars[i].is_ascii_digit() || chars[i] == '.' {
        while i < chars.len() && (chars[i].is_ascii_digit() || chars[i] == '.') {
            i += 1;
        }
        let text: String = chars[start..i].iter().collect();
        let val = text
            .parse::<f64>()
            .map_err(|_| format!("#VALUE!: invalid number '{text}'"))?;
        return Ok((Token::Number(val), i));
    }
    if chars[i].is_ascii_alphabetic() || matches!(chars[i], '_' | '$') {
        while i < chars.len()
            && (chars[i].is_ascii_alphanumeric() || matches!(chars[i], '_' | '$' | '.'))
        {
            i += 1;
        }
        return Ok((Token::Ident(chars[start..i].iter().collect()), i));
    }
    Err(format!("#VALUE!: unexpected character '{}'", chars[i]))
}

fn tokenize(formula: &str) -> Result<Vec<Token>, String> {
    let expr = formula.trim().strip_prefix('=').unwrap_or(formula.trim());
    if expr.is_empty() {
        return Err("#VALUE!: empty formula".to_owned());
    }
    if expr.contains('[') || expr.contains(']') {
        return Err("#REF!: external workbook references are disallowed".to_owned());
    }
    let chars: Vec<char> = expr.chars().collect();
    let mut tokens = Vec::new();
    let mut i = 0;
    while i < chars.len() {
        if chars[i].is_ascii_whitespace() {
            i += 1;
        } else if let Some((tok, next)) = read_punctuation(&chars, i) {
            tokens.push(tok);
            i = next;
        } else {
            let (tok, next) = read_atom(&chars, i)?;
            tokens.push(tok);
            i = next;
        }
    }
    Ok(tokens)
}

pub struct WorkbookEvaluator<'a> {
    pub grid: &'a BTreeMap<CellCoord, GridCell>,
    cache: BTreeMap<CellCoord, Result<Value, String>>,
    visiting: BTreeSet<CellCoord>,
}

impl<'a> WorkbookEvaluator<'a> {
    pub fn new(grid: &'a BTreeMap<CellCoord, GridCell>) -> Self {
        Self {
            grid,
            cache: BTreeMap::new(),
            visiting: BTreeSet::new(),
        }
    }

    pub fn eval_numeric(&mut self, coord: &CellCoord) -> Result<f64, String> {
        let num = self.eval_cell(coord)?.as_number()?;
        if !num.is_finite() {
            return Err("#NUM!: non-finite result".to_owned());
        }
        Ok(num)
    }

    fn eval_cell(&mut self, coord: &CellCoord) -> Result<Value, String> {
        if let Some(cached) = self.cache.get(coord) {
            return cached.clone();
        }
        if !self.visiting.insert(coord.clone()) {
            return Err(format!(
                "#REF!: circular reference at {}!{}",
                coord.sheet,
                cell_ref(coord.row, coord.col)
            ));
        }
        let result = match self.grid.get(coord) {
            None => Ok(Value::Empty),
            Some(GridCell::Number(n)) => Ok(Value::Number(*n)),
            Some(GridCell::Bool(b)) => Ok(Value::Bool(*b)),
            Some(GridCell::Text(t)) => Ok(Value::Text(t.clone())),
            Some(GridCell::Error(err)) => Err(err.clone()),
            Some(GridCell::Formula(formula)) => {
                let tokens = tokenize(formula)?;
                let mut parser = Parser {
                    tokens: &tokens,
                    pos: 0,
                    current_sheet: &coord.sheet,
                    eval: self,
                };
                let value = parser.parse_comparison()?;
                if parser.pos != parser.tokens.len() {
                    Err("#VALUE!: unexpected trailing tokens in formula".to_owned())
                } else {
                    Ok(value)
                }
            }
        };
        self.visiting.remove(coord);
        self.cache.insert(coord.clone(), result.clone());
        result
    }
}

struct Parser<'a, 'b> {
    tokens: &'a [Token],
    pos: usize,
    current_sheet: &'a str,
    eval: &'a mut WorkbookEvaluator<'b>,
}

impl<'a, 'b> Parser<'a, 'b> {
    fn peek(&self) -> Option<&Token> {
        self.tokens.get(self.pos)
    }

    fn next(&mut self) -> Option<Token> {
        let tok = self.tokens.get(self.pos)?.clone();
        self.pos += 1;
        Some(tok)
    }

    fn parse_comparison(&mut self) -> Result<Value, String> {
        let mut left = self.parse_additive()?;
        while let Some(
            op @ (Token::Eq | Token::Ne | Token::Lt | Token::Le | Token::Gt | Token::Ge),
        ) = self.peek().cloned()
        {
            self.pos += 1;
            let right = self.parse_additive()?;
            let cmp = compare_values(&left, &right)?;
            left = Value::Bool(match op {
                Token::Eq => cmp == 0,
                Token::Ne => cmp != 0,
                Token::Lt => cmp < 0,
                Token::Le => cmp <= 0,
                Token::Gt => cmp > 0,
                Token::Ge => cmp >= 0,
                _ => unreachable!(),
            });
        }
        Ok(left)
    }

    fn parse_additive(&mut self) -> Result<Value, String> {
        let mut left = self.parse_multiplicative()?;
        while let Some(op @ (Token::Plus | Token::Minus)) = self.peek().cloned() {
            self.pos += 1;
            let right = self.parse_multiplicative()?;
            let (l, r) = (left.as_number()?, right.as_number()?);
            left = Value::Number(if op == Token::Plus { l + r } else { l - r });
        }
        Ok(left)
    }

    fn parse_multiplicative(&mut self) -> Result<Value, String> {
        let mut left = self.parse_unary()?;
        while let Some(op @ (Token::Star | Token::Slash)) = self.peek().cloned() {
            self.pos += 1;
            let right = self.parse_unary()?;
            let (l, r) = (left.as_number()?, right.as_number()?);
            if op == Token::Slash {
                if r == 0.0 {
                    return Err("#DIV/0!: division by zero".to_owned());
                }
                left = Value::Number(l / r);
            } else {
                left = Value::Number(l * r);
            }
        }
        Ok(left)
    }

    fn parse_unary(&mut self) -> Result<Value, String> {
        match self.peek() {
            Some(Token::Plus) => {
                self.pos += 1;
                Ok(Value::Number(self.parse_unary()?.as_number()?))
            }
            Some(Token::Minus) => {
                self.pos += 1;
                Ok(Value::Number(-self.parse_unary()?.as_number()?))
            }
            _ => self.parse_primary(),
        }
    }

    fn parse_sheet_cell(&mut self, sheet: String) -> Result<Value, String> {
        if self.next() != Some(Token::Bang) {
            return Err("#REF!: expected '!' after sheet name".to_owned());
        }
        let Some(Token::Ident(cell_tok)) = self.next() else {
            return Err("#REF!: expected cell reference after '!'".to_owned());
        };
        let (row, col) = parse_cell_ref(&cell_tok)
            .ok_or_else(|| format!("#REF!: invalid cell reference '{cell_tok}'"))?;
        self.eval.eval_cell(&CellCoord { sheet, row, col })
    }

    fn parse_ident(&mut self, ident: String) -> Result<Value, String> {
        if self.peek() == Some(&Token::LParen) {
            return self.parse_function(&ident);
        }
        if self.peek() == Some(&Token::Bang) {
            return self.parse_sheet_cell(ident);
        }
        match ident.to_ascii_uppercase().as_str() {
            "TRUE" => Ok(Value::Bool(true)),
            "FALSE" => Ok(Value::Bool(false)),
            _ => {
                let (row, col) = parse_cell_ref(&ident)
                    .ok_or_else(|| format!("#NAME?: unknown identifier '{ident}'"))?;
                self.eval.eval_cell(&CellCoord {
                    sheet: self.current_sheet.to_owned(),
                    row,
                    col,
                })
            }
        }
    }

    fn parse_primary(&mut self) -> Result<Value, String> {
        match self.next() {
            Some(Token::Number(n)) => Ok(Value::Number(n)),
            Some(Token::String(s)) => Ok(Value::Text(s)),
            Some(Token::LParen) => {
                let value = self.parse_comparison()?;
                if self.next() != Some(Token::RParen) {
                    return Err("#VALUE!: missing closing parenthesis".to_owned());
                }
                Ok(value)
            }
            Some(Token::QuotedSheet(sheet)) => self.parse_sheet_cell(sheet),
            Some(Token::Ident(ident)) => self.parse_ident(ident),
            _ => Err("#VALUE!: unexpected token in formula".to_owned()),
        }
    }

    fn try_parse_range(&mut self) -> Result<Option<Vec<Value>>, String> {
        let saved = self.pos;
        let sheet = match self.peek() {
            Some(Token::QuotedSheet(s) | Token::Ident(s))
                if self.tokens.get(self.pos + 1) == Some(&Token::Bang) =>
            {
                let s = s.clone();
                self.pos += 2;
                s
            }
            _ => self.current_sheet.to_owned(),
        };
        let (Some(Token::Ident(a)), Some(Token::Colon), Some(Token::Ident(b))) = (
            self.tokens.get(self.pos).cloned(),
            self.tokens.get(self.pos + 1),
            self.tokens.get(self.pos + 2).cloned(),
        ) else {
            self.pos = saved;
            return Ok(None);
        };
        let (Some((r1, c1)), Some((r2, c2))) = (parse_cell_ref(&a), parse_cell_ref(&b)) else {
            self.pos = saved;
            return Ok(None);
        };
        self.pos += 3;
        let mut values = Vec::new();
        for row in r1.min(r2)..=r1.max(r2) {
            for col in c1.min(c2)..=c1.max(c2) {
                values.push(self.eval.eval_cell(&CellCoord {
                    sheet: sheet.clone(),
                    row,
                    col,
                })?);
            }
        }
        Ok(Some(values))
    }

    fn parse_function(&mut self, name: &str) -> Result<Value, String> {
        let upper = name.to_ascii_uppercase();
        if DISALLOWED_FUNCTIONS.contains(&upper.as_str()) {
            return Err(format!(
                "#NAME?: disallowed external or volatile function '{upper}'"
            ));
        }
        self.pos += 1;
        if upper == "IFERROR" {
            let first = self.parse_comparison();
            if self.next() != Some(Token::Comma) {
                return Err("#VALUE!: IFERROR requires 2 arguments".to_owned());
            }
            let fallback = self.parse_comparison()?;
            if self.next() != Some(Token::RParen) {
                return Err("#VALUE!: missing closing parenthesis for IFERROR".to_owned());
            }
            return Ok(first.unwrap_or(fallback));
        }
        let mut args = Vec::new();
        if self.peek() != Some(&Token::RParen) {
            loop {
                if let Some(range) = self.try_parse_range()? {
                    args.push(ArgValue::Range(range));
                } else {
                    args.push(ArgValue::Scalar(self.parse_comparison()?));
                }
                match self.peek() {
                    Some(Token::Comma) => self.pos += 1,
                    Some(Token::RParen) => break,
                    _ => return Err(format!("#VALUE!: malformed arguments in {upper}()")),
                }
            }
        }
        if self.next() != Some(Token::RParen) {
            return Err(format!(
                "#VALUE!: missing closing parenthesis for {upper}()"
            ));
        }
        eval_function(&upper, &args)
    }
}
