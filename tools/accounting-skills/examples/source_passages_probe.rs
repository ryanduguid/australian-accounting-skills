//! Offline qualification seam. Production capture always uses the URL policy
//! and transport; the probe asks its caller to supply a fabricated response.
use accounting_skills::{Result, source_passages as p};
use serde_json::{Value, json};
use std::{
    io::{self, BufRead, Write},
    path::Path,
};

fn invoke(r: &Value, input: &mut impl BufRead) -> Result<Value> {
    let text = |key: &str| r[key].as_str().unwrap_or("");
    let skills = Path::new(text("skills"));
    Ok(match text("op") {
        "indexed" => json!(p::indexed_url(text("url"), skills)?),
        "snapshot" => p::snapshot_with(text("url"), skills, |url| {
            println!(
                "{}",
                json!({"event":"fetch", "url":url, "include_text":true})
            );
            io::stdout().flush()?;
            let mut line = String::new();
            input.read_line(&mut line)?;
            Ok(serde_json::from_str(&line)?)
        })?,
        "load" => p::load_snapshot(Path::new(text("path")), skills)?,
        "compare" => p::compare(&r["before"], &r["after"])?,
        "render" => json!(p::rendered(&r["value"])?),
        _ => return Err("unknown operation".into()),
    })
}
fn main() {
    let mut input = io::stdin().lock();
    loop {
        let mut line = String::new();
        if input.read_line(&mut line).unwrap() == 0 {
            break;
        }
        let result =
            (|| -> Result<Value> { invoke(&serde_json::from_str::<Value>(&line)?, &mut input) })();
        let value = match result {
            Ok(value) => json!({"ok":value}),
            Err(error) => json!({"error":error.to_string()}),
        };
        println!("{value}");
        io::stdout().flush().unwrap();
    }
}
