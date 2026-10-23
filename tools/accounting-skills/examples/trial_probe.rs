//! Offline qualification with a link-check callback for the original mock seam.
use accounting_skills::{Result, trial};
use serde_json::{Value, json};
use std::{
    io::{self, BufRead, Write},
    path::Path,
};

fn invoke(r: &Value, input: &mut impl BufRead) -> Result<Value> {
    let text = |key: &str| r[key].as_str().unwrap_or("");
    Ok(match text("op") {
        "hash" => json!(trial::digest(&serde_json::from_value::<Vec<u8>>(
            r["bytes"].clone()
        )?)),
        "credential" => json!(trial::credential_name(text("name"))),
        "input" => {
            let (bytes, skills) = trial::task_input(
                &serde_json::from_value::<Vec<u8>>(r["bytes"].clone())?,
                text("name"),
            )?;
            json!({"bytes":bytes,"skills":skills})
        }
        "prepare" => {
            trial::prepare_with(
                text("case"),
                Path::new(text("destination")),
                text("model"),
                text("runtime"),
                Path::new(text("root")),
                |path| {
                    println!("{}", json!({"event":"link","path":path}));
                    io::stdout().flush()?;
                    let mut line = String::new();
                    input.read_line(&mut line)?;
                    Ok(serde_json::from_str::<bool>(&line)?)
                },
            )?;
            Value::Null
        }
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
        let reply = match result {
            Ok(value) => json!({"ok":value}),
            Err(error) => json!({"error":error.to_string()}),
        };
        println!("{reply}");
        io::stdout().flush().unwrap();
    }
}
