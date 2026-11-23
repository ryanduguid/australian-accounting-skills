// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: Apache-2.0

//! Value conversions, comparison helpers and spreadsheet function dispatch for
//! deterministic `.xlsx` formula verification.

pub const DISALLOWED_FUNCTIONS: [&str; 9] = [
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

#[derive(Debug, Clone)]
pub enum EvalError {
    /// Non-catchable security or policy violation (e.g. disallowed external function).
    Policy(String),
    /// Ordinary spreadsheet evaluation error catchable by `IFERROR`.
    Formula(String),
}

impl EvalError {
    pub fn into_message(self) -> String {
        match self {
            Self::Policy(msg) | Self::Formula(msg) => msg,
        }
    }
}

#[derive(Debug, Clone)]
pub enum Value {
    Number(f64),
    Bool(bool),
    Text(String),
    Empty,
}

impl Value {
    pub fn as_number(&self) -> Result<f64, EvalError> {
        match self {
            Self::Number(n) => Ok(*n),
            Self::Bool(b) => Ok(if *b { 1.0 } else { 0.0 }),
            Self::Empty => Ok(0.0),
            Self::Text(t) => t
                .trim()
                .parse::<f64>()
                .ok()
                .filter(|n| n.is_finite())
                .ok_or_else(|| {
                    EvalError::Formula(format!("#VALUE!: cannot convert text '{t}' to number"))
                }),
        }
    }

    pub fn as_bool(&self) -> Result<bool, EvalError> {
        match self {
            Self::Bool(b) => Ok(*b),
            Self::Number(n) => Ok(*n != 0.0),
            Self::Empty => Ok(false),
            Self::Text(t) => Err(EvalError::Formula(format!(
                "#VALUE!: cannot treat text '{t}' as boolean"
            ))),
        }
    }
}

pub enum ArgValue {
    Scalar(Value),
    Range(Vec<Value>),
}

fn scalar_number(arg: &ArgValue) -> Result<f64, EvalError> {
    match arg {
        ArgValue::Scalar(v) => v.as_number(),
        ArgValue::Range(_) => Err(EvalError::Formula(
            "#VALUE!: expected scalar argument, found range".to_owned(),
        )),
    }
}

fn scalar_value(arg: &ArgValue, msg: &str) -> Result<Value, EvalError> {
    match arg {
        ArgValue::Scalar(v) => Ok(v.clone()),
        ArgValue::Range(_) => Err(EvalError::Formula(msg.to_owned())),
    }
}

fn flatten_numeric(args: &[ArgValue]) -> Result<Vec<f64>, EvalError> {
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

pub fn compare_values(left: &Value, right: &Value) -> Result<i32, EvalError> {
    match (left, right) {
        (Value::Text(a), Value::Text(b)) => {
            Ok(a.to_ascii_lowercase().cmp(&b.to_ascii_lowercase()) as i32)
        }
        _ => {
            let (a, b) = (left.as_number()?, right.as_number()?);
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
        (Value::Number(a), Value::Text(expr)) => match_numeric_expr(*a, expr),
        _ => false,
    }
}

fn match_numeric_expr(a: f64, expr: &str) -> bool {
    type CmpOp = (&'static str, fn(f64, f64) -> bool);
    let ops: [CmpOp; 4] = [
        (">=", |x, y| x >= y),
        ("<=", |x, y| x <= y),
        (">", |x, y| x > y),
        ("<", |x, y| x < y),
    ];
    for (prefix, cmp) in ops {
        if let Some(rest) = expr.strip_prefix(prefix)
            && let Ok(n) = rest.trim().parse::<f64>()
        {
            return cmp(a, n);
        }
    }
    expr.trim()
        .parse::<f64>()
        .is_ok_and(|n| (a - n).abs() < 1e-12)
}

fn eval_if(args: &[ArgValue]) -> Result<Value, EvalError> {
    if !(2..=3).contains(&args.len()) {
        return Err(EvalError::Formula(
            "#VALUE!: IF expects 2 or 3 arguments".to_owned(),
        ));
    }
    let cond = scalar_value(&args[0], "#VALUE!: IF condition must be scalar")?.as_bool()?;
    if cond {
        scalar_value(&args[1], "#VALUE!: IF branch must be scalar")
    } else if args.len() == 3 {
        scalar_value(&args[2], "#VALUE!: IF branch must be scalar")
    } else {
        Ok(Value::Bool(false))
    }
}

fn eval_sumif(args: &[ArgValue]) -> Result<Value, EvalError> {
    if !(2..=3).contains(&args.len()) {
        return Err(EvalError::Formula(
            "#VALUE!: SUMIF expects 2 or 3 arguments".to_owned(),
        ));
    }
    let ArgValue::Range(criteria_range) = &args[0] else {
        return Err(EvalError::Formula(
            "#VALUE!: SUMIF first argument must be a range".to_owned(),
        ));
    };
    let ArgValue::Scalar(criterion) = &args[1] else {
        return Err(EvalError::Formula(
            "#VALUE!: SUMIF criterion must be scalar".to_owned(),
        ));
    };
    let sum_range = if args.len() == 3 {
        let ArgValue::Range(r) = &args[2] else {
            return Err(EvalError::Formula(
                "#VALUE!: SUMIF third argument must be a range".to_owned(),
            ));
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

pub fn eval_function(upper: &str, args: &[ArgValue]) -> Result<Value, EvalError> {
    match upper {
        "SUM" => Ok(Value::Number(flatten_numeric(args)?.into_iter().sum())),
        "AVERAGE" => {
            let nums = flatten_numeric(args)?;
            if nums.is_empty() {
                return Err(EvalError::Formula(
                    "#DIV/0!: AVERAGE of empty set".to_owned(),
                ));
            }
            Ok(Value::Number(nums.iter().sum::<f64>() / nums.len() as f64))
        }
        "MIN" => Ok(Value::Number(
            flatten_numeric(args)?
                .into_iter()
                .reduce(f64::min)
                .unwrap_or(0.0),
        )),
        "MAX" => Ok(Value::Number(
            flatten_numeric(args)?
                .into_iter()
                .reduce(f64::max)
                .unwrap_or(0.0),
        )),
        "COUNT" => Ok(Value::Number(flatten_numeric(args)?.len() as f64)),
        "ABS" => eval_abs(args),
        "ROUND" => eval_round(args),
        "IF" => eval_if(args),
        "SUMIF" => eval_sumif(args),
        _ => Err(EvalError::Formula(format!(
            "#NAME?: unsupported function '{upper}'"
        ))),
    }
}

fn eval_abs(args: &[ArgValue]) -> Result<Value, EvalError> {
    if args.len() != 1 {
        return Err(EvalError::Formula(
            "#VALUE!: ABS expects 1 argument".to_owned(),
        ));
    }
    Ok(Value::Number(scalar_number(&args[0])?.abs()))
}

fn eval_round(args: &[ArgValue]) -> Result<Value, EvalError> {
    if args.len() != 2 {
        return Err(EvalError::Formula(
            "#VALUE!: ROUND expects 2 arguments".to_owned(),
        ));
    }
    let val = scalar_number(&args[0])?;
    let digits = scalar_number(&args[1])?.trunc() as i32;
    let factor = 10_f64.powi(digits);
    Ok(Value::Number((val * factor).round() / factor))
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
