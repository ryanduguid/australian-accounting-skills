// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Deterministic spreadsheet formula validator and evaluator for audit-grade
//! `.xlsx` workpapers. Rejects external workbook links and unsafe functions,
//! detects circular references and division by zero, and evaluates supported
//! arithmetic, comparison, range and accounting functions.

use std::collections::{BTreeMap, BTreeSet};

const DISALLOWED_FUNCTIONS: [&str; 9] = [
    "WEBSERVICE",
    "HYPERLINK",
    "CALL",
    "REGISTER.ID",
    "IMPORTXML",
    "IMPORTDATA",
    "IMPORTHTML",
    "EXEC",
    "CMD",
];

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

#[derive(Debug, Clone)]
enum Value {
    Number(f64),
    Bool(bool),
    Text(String),
    Empty,
}

impl Value {
    fn as_number(&self) -> Result<f64, String> {
        match self {
            Self::Number(n) => Ok(*n),
            Self::Bool(b) => Ok(if *b { 1.0 } else { 0.0 }),
            Self::Empty => Ok(0.0),
            Self::Text(t) => t
                .trim()
                .parse::<f64>()
                .map_err(|_| format!("#VALUE!: cannot convert text '{t}' to number")),
        }
    }

    fn as_bool(&self) -> Result<bool, String> {
        match self {
            Self::Bool(b) => Ok(*b),
            Self::Number(n) => Ok(*n != 0.0),
            Self::Empty => Ok(false),
            Self::Text(t) => Err(format!("#VALUE!: cannot treat text '{t}' as boolean")),
        }
    }
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
        match chars[i] {
            c if c.is_ascii_whitespace() => i += 1,
            '+' => {
                tokens.push(Token::Plus);
                i += 1;
            }
            '-' => {
                tokens.push(Token::Minus);
                i += 1;
            }
            '*' => {
                tokens.push(Token::Star);
                i += 1;
            }
            '/' => {
                tokens.push(Token::Slash);
                i += 1;
            }
            '(' => {
                tokens.push(Token::LParen);
                i += 1;
            }
            ')' => {
                tokens.push(Token::RParen);
                i += 1;
            }
            ',' => {
                tokens.push(Token::Comma);
                i += 1;
            }
            ':' => {
                tokens.push(Token::Colon);
                i += 1;
            }
            '!' => {
                tokens.push(Token::Bang);
                i += 1;
            }
            '=' => {
                tokens.push(Token::Eq);
                i += 1;
            }
            '<' => {
                if i + 1 < chars.len() && chars[i + 1] == '=' {
                    tokens.push(Token::Le);
                    i += 2;
                } else if i + 1 < chars.len() && chars[i + 1] == '>' {
                    tokens.push(Token::Ne);
                    i += 2;
                } else {
                    tokens.push(Token::Lt);
                    i += 1;
                }
            }
            '>' => {
                if i + 1 < chars.len() && chars[i + 1] == '=' {
                    tokens.push(Token::Ge);
                    i += 2;
                } else {
                    tokens.push(Token::Gt);
                    i += 1;
                }
            }
            '"' => {
                i += 1;
                let mut s = String::new();
                let mut closed = false;
                while i < chars.len() {
                    if chars[i] == '"' {
                        if i + 1 < chars.len() && chars[i + 1] == '"' {
                            s.push('"');
                            i += 2;
                        } else {
                            i += 1;
                            closed = true;
                            break;
                        }
                    } else {
                        s.push(chars[i]);
                        i += 1;
                    }
                }
                if !closed {
                    return Err("#VALUE!: unterminated string literal".to_owned());
                }
                tokens.push(Token::String(s));
            }
            '\'' => {
                i += 1;
                let mut s = String::new();
                let mut closed = false;
                while i < chars.len() {
                    if chars[i] == '\'' {
                        if i + 1 < chars.len() && chars[i + 1] == '\'' {
                            s.push('\'');
                            i += 2;
                        } else {
                            i += 1;
                            closed = true;
                            break;
                        }
                    } else {
                        s.push(chars[i]);
                        i += 1;
                    }
                }
                if !closed {
                    return Err("#NAME?: unterminated sheet name".to_owned());
                }
                tokens.push(Token::QuotedSheet(s));
            }
            c if c.is_ascii_digit() || c == '.' => {
                let start = i;
                while i < chars.len() && (chars[i].is_ascii_digit() || chars[i] == '.') {
                    i += 1;
                }
                let text: String = chars[start..i].iter().collect();
                let value = text
                    .parse::<f64>()
                    .map_err(|_| format!("#VALUE!: invalid number '{text}'"))?;
                tokens.push(Token::Number(value));
            }
            c if c.is_ascii_alphabetic() || c == '_' || c == '$' => {
                let start = i;
                while i < chars.len()
                    && (chars[i].is_ascii_alphanumeric() || matches!(chars[i], '_' | '$' | '.'))
                {
                    i += 1;
                }
                let ident: String = chars[start..i].iter().collect();
                tokens.push(Token::Ident(ident));
            }
            other => return Err(format!("#VALUE!: unexpected character '{other}'")),
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
        let value = self.eval_cell(coord)?;
        let num = value.as_number()?;
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

enum ArgValue {
    Scalar(Value),
    Range(Vec<Value>),
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
            let matched = match op {
                Token::Eq => cmp == 0,
                Token::Ne => cmp != 0,
                Token::Lt => cmp < 0,
                Token::Le => cmp <= 0,
                Token::Gt => cmp > 0,
                Token::Ge => cmp >= 0,
                _ => unreachable!(),
            };
            left = Value::Bool(matched);
        }
        Ok(left)
    }

    fn parse_additive(&mut self) -> Result<Value, String> {
        let mut left = self.parse_multiplicative()?;
        while let Some(op @ (Token::Plus | Token::Minus)) = self.peek().cloned() {
            self.pos += 1;
            let right = self.parse_multiplicative()?;
            let l = left.as_number()?;
            let r = right.as_number()?;
            left = Value::Number(if op == Token::Plus { l + r } else { l - r });
        }
        Ok(left)
    }

    fn parse_multiplicative(&mut self) -> Result<Value, String> {
        let mut left = self.parse_unary()?;
        while let Some(op @ (Token::Star | Token::Slash)) = self.peek().cloned() {
            self.pos += 1;
            let right = self.parse_unary()?;
            let l = left.as_number()?;
            let r = right.as_number()?;
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
            Some(Token::QuotedSheet(sheet)) => {
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
            Some(Token::Ident(ident)) => {
                if self.peek() == Some(&Token::LParen) {
                    return self.parse_function(&ident);
                }
                if self.peek() == Some(&Token::Bang) {
                    self.pos += 1;
                    let Some(Token::Ident(cell_tok)) = self.next() else {
                        return Err("#REF!: expected cell reference after '!'".to_owned());
                    };
                    let (row, col) = parse_cell_ref(&cell_tok)
                        .ok_or_else(|| format!("#REF!: invalid cell reference '{cell_tok}'"))?;
                    return self.eval.eval_cell(&CellCoord {
                        sheet: ident,
                        row,
                        col,
                    });
                }
                let upper = ident.to_ascii_uppercase();
                if upper == "TRUE" {
                    return Ok(Value::Bool(true));
                }
                if upper == "FALSE" {
                    return Ok(Value::Bool(false));
                }
                let (row, col) = parse_cell_ref(&ident)
                    .ok_or_else(|| format!("#NAME?: unknown identifier '{ident}'"))?;
                self.eval.eval_cell(&CellCoord {
                    sheet: self.current_sheet.to_owned(),
                    row,
                    col,
                })
            }
            _ => Err("#VALUE!: unexpected token in formula".to_owned()),
        }
    }

    fn try_parse_range(&mut self) -> Result<Option<Vec<Value>>, String> {
        let saved = self.pos;
        let sheet = match self.peek() {
            Some(Token::QuotedSheet(s)) if self.tokens.get(self.pos + 1) == Some(&Token::Bang) => {
                let s = s.clone();
                self.pos += 2;
                s
            }
            Some(Token::Ident(s)) if self.tokens.get(self.pos + 1) == Some(&Token::Bang) => {
                let s = s.clone();
                self.pos += 2;
                s
            }
            _ => self.current_sheet.to_owned(),
        };
        let Some(Token::Ident(start_tok)) = self.peek().cloned() else {
            self.pos = saved;
            return Ok(None);
        };
        if self.tokens.get(self.pos + 1) != Some(&Token::Colon) {
            self.pos = saved;
            return Ok(None);
        }
        let Some(Token::Ident(end_tok)) = self.tokens.get(self.pos + 2).cloned() else {
            self.pos = saved;
            return Ok(None);
        };
        let Some((r1, c1)) = parse_cell_ref(&start_tok) else {
            self.pos = saved;
            return Ok(None);
        };
        let Some((r2, c2)) = parse_cell_ref(&end_tok) else {
            self.pos = saved;
            return Ok(None);
        };
        self.pos += 3;
        let (r_min, r_max) = (r1.min(r2), r1.max(r2));
        let (c_min, c_max) = (c1.min(c2), c1.max(c2));
        let mut values = Vec::new();
        for row in r_min..=r_max {
            for col in c_min..=c_max {
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
            return Ok(match first {
                Ok(v) => v,
                Err(_) => fallback,
            });
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

        match upper.as_str() {
            "SUM" => {
                let mut sum = 0.0;
                for n in flatten_numeric(&args)? {
                    sum += n;
                }
                Ok(Value::Number(sum))
            }
            "AVERAGE" => {
                let nums = flatten_numeric(&args)?;
                if nums.is_empty() {
                    return Err("#DIV/0!: AVERAGE of empty set".to_owned());
                }
                Ok(Value::Number(nums.iter().sum::<f64>() / nums.len() as f64))
            }
            "MIN" => {
                let nums = flatten_numeric(&args)?;
                Ok(Value::Number(
                    nums.into_iter().reduce(f64::min).unwrap_or(0.0),
                ))
            }
            "MAX" => {
                let nums = flatten_numeric(&args)?;
                Ok(Value::Number(
                    nums.into_iter().reduce(f64::max).unwrap_or(0.0),
                ))
            }
            "COUNT" => Ok(Value::Number(flatten_numeric(&args)?.len() as f64)),
            "ABS" => {
                if args.len() != 1 {
                    return Err("#VALUE!: ABS expects 1 argument".to_owned());
                }
                Ok(Value::Number(scalar_number(&args[0])?.abs()))
            }
            "ROUND" => {
                if args.len() != 2 {
                    return Err("#VALUE!: ROUND expects 2 arguments".to_owned());
                }
                let val = scalar_number(&args[0])?;
                let digits = scalar_number(&args[1])?.trunc() as i32;
                let factor = 10_f64.powi(digits);
                Ok(Value::Number((val * factor).round() / factor))
            }
            "IF" => {
                if !(2..=3).contains(&args.len()) {
                    return Err("#VALUE!: IF expects 2 or 3 arguments".to_owned());
                }
                let cond = match &args[0] {
                    ArgValue::Scalar(v) => v.as_bool()?,
                    ArgValue::Range(_) => {
                        return Err("#VALUE!: IF condition must be scalar".to_owned());
                    }
                };
                if cond {
                    match &args[1] {
                        ArgValue::Scalar(v) => Ok(v.clone()),
                        ArgValue::Range(_) => Err("#VALUE!: IF branch must be scalar".to_owned()),
                    }
                } else if args.len() == 3 {
                    match &args[2] {
                        ArgValue::Scalar(v) => Ok(v.clone()),
                        ArgValue::Range(_) => Err("#VALUE!: IF branch must be scalar".to_owned()),
                    }
                } else {
                    Ok(Value::Bool(false))
                }
            }
            "SUMIF" => {
                if !(2..=3).contains(&args.len()) {
                    return Err("#VALUE!: SUMIF expects 2 or 3 arguments".to_owned());
                }
                let ArgValue::Range(criteria_range) = &args[0] else {
                    return Err("#VALUE!: SUMIF first argument must be a range".to_owned());
                };
                let ArgValue::Scalar(criterion) = &args[1] else {
                    return Err("#VALUE!: SUMIF criterion must be scalar".to_owned());
                };
                let sum_range = if args.len() == 3 {
                    let ArgValue::Range(r) = &args[2] else {
                        return Err("#VALUE!: SUMIF third argument must be a range".to_owned());
                    };
                    r
                } else {
                    criteria_range
                };
                let mut total = 0.0;
                for (i, item) in criteria_range.iter().enumerate() {
                    if matches_criterion(item, criterion)
                        && let Some(Value::Number(n)) = sum_range.get(i)
                    {
                        total += n;
                    }
                }
                Ok(Value::Number(total))
            }
            _ => Err(format!("#NAME?: unsupported function '{upper}'")),
        }
    }
}

fn scalar_number(arg: &ArgValue) -> Result<f64, String> {
    match arg {
        ArgValue::Scalar(v) => v.as_number(),
        ArgValue::Range(_) => Err("#VALUE!: expected scalar argument, found range".to_owned()),
    }
}

fn flatten_numeric(args: &[ArgValue]) -> Result<Vec<f64>, String> {
    let mut out = Vec::new();
    for arg in args {
        match arg {
            ArgValue::Scalar(Value::Empty) => {}
            ArgValue::Scalar(v) => out.push(v.as_number()?),
            ArgValue::Range(values) => {
                for v in values {
                    if let Value::Number(n) = v {
                        out.push(*n);
                    }
                }
            }
        }
    }
    Ok(out)
}

fn compare_values(left: &Value, right: &Value) -> Result<i32, String> {
    match (left, right) {
        (Value::Text(a), Value::Text(b)) => {
            Ok(a.to_ascii_lowercase().cmp(&b.to_ascii_lowercase()) as i32)
        }
        _ => {
            let a = left.as_number()?;
            let b = right.as_number()?;
            if (a - b).abs() < 1e-12 {
                Ok(0)
            } else if a < b {
                Ok(-1)
            } else {
                Ok(1)
            }
        }
    }
}

fn matches_criterion(value: &Value, criterion: &Value) -> bool {
    match (value, criterion) {
        (Value::Text(a), Value::Text(b)) => a.eq_ignore_ascii_case(b),
        (Value::Number(a), Value::Number(b)) => (a - b).abs() < 1e-12,
        (Value::Number(a), Value::Text(expr)) => {
            if let Some(rest) = expr.strip_prefix(">=")
                && let Ok(n) = rest.trim().parse::<f64>()
            {
                return *a >= n;
            }
            if let Some(rest) = expr.strip_prefix("<=")
                && let Ok(n) = rest.trim().parse::<f64>()
            {
                return *a <= n;
            }
            if let Some(rest) = expr.strip_prefix('>')
                && let Ok(n) = rest.trim().parse::<f64>()
            {
                return *a > n;
            }
            if let Some(rest) = expr.strip_prefix('<')
                && let Ok(n) = rest.trim().parse::<f64>()
            {
                return *a < n;
            }
            expr.trim()
                .parse::<f64>()
                .is_ok_and(|n| (*a - n).abs() < 1e-12)
        }
        _ => false,
    }
}
