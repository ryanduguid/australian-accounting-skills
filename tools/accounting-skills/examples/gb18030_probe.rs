//! Offline comparison seam compiling the exact private production decoder.
//! It exposes both modes without adding a public library or CLI interface.
#[path = "../src/source_gb18030.rs"]
mod source_gb18030;
#[path = "../src/source_gb18030_rules.rs"]
mod source_gb18030_rules;
use std::io::{self, BufRead, Write};
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn main() -> Result<()> {
    for line in io::stdin().lock().lines() {
        let bodies: Vec<Vec<u8>> = serde_json::from_str(&line?)?;
        let values: Vec<_> = bodies
            .iter()
            .map(|body| {
                let replacement = source_gb18030::decode(body, false).unwrap();
                let strict = source_gb18030::decode(body, true).ok();
                (replacement, strict)
            })
            .collect();
        serde_json::to_writer(io::stdout().lock(), &values)?;
        println!();
        io::stdout().flush()?;
    }
    Ok(())
}
