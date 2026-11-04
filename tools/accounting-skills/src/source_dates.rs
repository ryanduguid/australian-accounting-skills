//! Day extraction follows datetime.fromisoformat and email._parseaddr (PSF-2.0).
use chrono::{NaiveDate, Weekday};
use fancy_regex::Regex;
use std::sync::LazyLock;

fn digit(c: char) -> Option<u8> {
    let n = c as u32;
    crate::source_date_rules::DECIMAL_ZEROES
        .iter()
        .find_map(|&zero| (zero..zero + 10).contains(&n).then(|| (n - zero) as u8))
}
fn is_digit(c: char) -> bool {
    let n = c as u32;
    crate::source_date_rules::DIGIT_RANGES
        .iter()
        .any(|&(lo, hi)| lo <= n && n <= hi)
}
fn integer(value: &str) -> Option<i64> {
    let value = value.trim_matches(super::source_content::space);
    let (negative, value) = if let Some(v) = value.strip_prefix('-') {
        (true, v)
    } else {
        (false, value.strip_prefix('+').unwrap_or(value))
    };
    let mut chars = value.chars().peekable();
    let mut number = 0i128;
    let mut digits = 0;
    let mut prior_digit = false;
    while let Some(c) = chars.next() {
        if c == '_' {
            if !prior_digit || !chars.peek().is_some_and(|&c| digit(c).is_some()) {
                return None;
            }
            prior_digit = false;
            continue;
        }
        let n = digit(c)?;
        digits += 1;
        if digits > 4300 {
            return None;
        }
        number = number.saturating_mul(10).saturating_add(n as i128);
        prior_digit = true;
    }
    if !prior_digit {
        return None;
    }
    let number = if negative { -number } else { number };
    Some(number.clamp(i64::MIN as i128, i64::MAX as i128) as i64)
}

fn day(date: NaiveDate) -> Option<String> {
    let text = date.format("%Y-%m-%d").to_string();
    (text.len() == 10 && !text.starts_with("0000")).then_some(text)
}
fn time(value: &str) -> Option<(u32, u32, u32)> {
    static TIME: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(r"^([0-9]{2})(?:(:)?([0-9]{2})(?:(?(2):)([0-9]{2}))?)?(?:[.,][0-9]+)?$").unwrap()
    });
    let found = TIME.captures(value).ok()??;
    if found.get(3).is_none() && value.contains(['.', ',']) {
        return None;
    }
    Some((
        found[1].parse().ok()?,
        found
            .get(3)
            .map(|v| v.as_str().parse())
            .transpose()
            .ok()?
            .unwrap_or(0),
        found
            .get(4)
            .map(|v| v.as_str().parse())
            .transpose()
            .ok()?
            .unwrap_or(0),
    ))
}
fn iso(value: &str) -> Option<String> {
    static ISO: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(r"(?s)^([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{4}-W[0-9]{2}(?:-[1-7])?|[0-9]{8}|[0-9]{4}W[0-9]{2}[1-7]?)(?:.(.+))?$").unwrap()
    });
    let found = ISO.captures(value).ok()??;
    let date = &found[1];
    let parsed = if date.contains('W') {
        let pieces = date.replace('-', "");
        let year = pieces[..4].parse().ok()?;
        let week = pieces[5..7].parse().ok()?;
        let weekday = match pieces.as_bytes().get(7).copied().unwrap_or(b'1') {
            b'1' => Weekday::Mon,
            b'2' => Weekday::Tue,
            b'3' => Weekday::Wed,
            b'4' => Weekday::Thu,
            b'5' => Weekday::Fri,
            b'6' => Weekday::Sat,
            b'7' => Weekday::Sun,
            _ => return None,
        };
        NaiveDate::from_isoywd_opt(year, week, weekday)?
    } else {
        NaiveDate::parse_from_str(
            date,
            if date.contains('-') {
                "%Y-%m-%d"
            } else {
                "%Y%m%d"
            },
        )
        .ok()?
    };
    if let Some(clock) = found.get(2) {
        let clock = clock.as_str();
        let tz = clock.find(['+', '-']);
        let (base, offset) = tz
            .map(|i| (&clock[..i], Some(&clock[i + 1..])))
            .unwrap_or((clock, None));
        let (h, m, s) = time(base)?;
        if h > 23 || m > 59 || s > 59 {
            return None;
        }
        if let Some(offset) = offset {
            let (h, m, s) = time(offset)?;
            if h * 3600 + m * 60 + s >= 86400 {
                return None;
            }
        }
    }
    day(parsed)
}
fn email(value: &str) -> Option<String> {
    let mut data: Vec<String> = value
        .split(super::source_content::space)
        .filter(|s| !s.is_empty())
        .map(str::to_owned)
        .collect();
    if data.is_empty() {
        return None;
    }
    if data[0].ends_with(',')
        || ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            .contains(&data[0].to_lowercase().as_str())
    {
        data.remove(0);
    } else if let Some(i) = data[0].rfind(',') {
        data[0] = data[0][i + 1..].to_owned();
    }
    if data.len() == 3 {
        let parts: Vec<_> = data[0].split('-').map(str::to_owned).collect();
        if parts.len() == 3 {
            data.splice(0..1, parts);
        }
    }
    if data.len() == 4 {
        let split = data[3].find('+').or_else(|| data[3].find('-'));
        if let Some(i) = split.filter(|&i| i > 0) {
            let zone = data[3][i..].to_owned();
            data[3].truncate(i);
            data.push(zone);
        } else {
            data.push(String::new());
        }
    }
    if data.len() < 5 {
        return None;
    }
    let (mut dd, mut mm, mut yy, mut tm, mut tz) = (
        data[0].clone(),
        data[1].to_lowercase(),
        data[2].clone(),
        data[3].clone(),
        data[4].clone(),
    );
    let months = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ];
    if !months.contains(&mm.as_str()) {
        let old = mm;
        mm = dd.to_lowercase();
        dd = old;
    }
    let month = (months.iter().position(|&m| m == mm)? % 12 + 1) as u32;
    dd = dd.strip_suffix(',').unwrap_or(&dd).into();
    if yy.find(':').is_some_and(|i| i > 0) {
        std::mem::swap(&mut yy, &mut tm);
    }
    yy = yy.strip_suffix(',').unwrap_or(&yy).into();
    if !yy.chars().next().is_some_and(is_digit) {
        std::mem::swap(&mut yy, &mut tz);
    }
    tm = tm.strip_suffix(',').unwrap_or(&tm).into();
    let clock: Vec<_> = if tm.contains(':') {
        tm.split(':').collect()
    } else {
        tm.split('.').collect()
    };
    if !(2..=3).contains(&clock.len()) {
        return None;
    }
    let h = integer(clock[0])?;
    let m = integer(clock[1])?;
    let s = integer(clock.get(2).unwrap_or(&"0"))?;
    if !(0..=23).contains(&h) || !(0..=59).contains(&m) || !(0..=59).contains(&s) {
        return None;
    }
    if let Some(offset) = integer(&tz) {
        let offset = offset.unsigned_abs();
        if offset / 100 >= 24 || offset / 100 * 3600 + offset % 100 * 60 >= 86400 {
            return None;
        }
    }
    let mut year = integer(&yy)?;
    if year < 100 {
        year += if year > 68 { 1900 } else { 2000 };
    }
    day(NaiveDate::from_ymd_opt(
        year.try_into().ok()?,
        month,
        integer(&dd)?.try_into().ok()?,
    )?)
}
pub fn iso_day(value: &str) -> String {
    let value = value.trim_matches(super::source_content::space);
    iso(&value.replace('Z', "+00:00"))
        .or_else(|| email(value))
        .unwrap_or_default()
}
