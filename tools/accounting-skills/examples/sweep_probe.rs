//! Test-only protocol for replaying unchanged original test objects.
use serde_json::{Value, json};
use std::io::{self, BufRead, Write};

fn main() {
    for line in io::stdin().lock().lines() {
        let request: Value = serde_json::from_str(&line.unwrap()).unwrap();
        let text = |key: &str| request[key].as_str().unwrap();
        let result = accounting_skills::sweep::outcome(
            request["status"].as_i64().unwrap(),
            std::path::Path::new(text("report")),
            text("started"),
            std::path::Path::new(text("within")),
        );
        let response = match result {
            Ok(outcome) => json!({"outcome": outcome}),
            Err(error) => json!({"error": error.to_string()}),
        };
        println!("{response}");
        io::stdout().flush().unwrap();
    }
}
