use accounting_skills::{Result, validation as v};
use serde_json::{Value, json};
use std::{
    collections::BTreeSet,
    io::{self, BufRead, Write},
    path::Path,
};

fn invoke(request: &Value) -> Result<Value> {
    let s = |key: &str| request[key].as_str().unwrap_or("");
    let names = |key: &str| {
        request[key]
            .as_array()
            .map(|items| {
                items
                    .iter()
                    .map(|v| v.as_str().unwrap().to_owned())
                    .collect::<BTreeSet<_>>()
            })
            .unwrap_or_default()
    };
    let path = Path::new(s("path"));
    let root = Path::new(s("root"));
    Ok(match s("op") {
        "front" => {
            let (metadata, body) = v::parse_front_matter(s("text"), s("name"))?;
            json!([metadata, body])
        }
        "normalise" => json!(v::normalise_for_sensitive_scan(s("text"))?),
        "sensitive" => {
            v::check_sensitive_content(
                s("text"),
                &names("waived").into_iter().collect::<Vec<_>>(),
            )?;
            Value::Null
        }
        "read" => json!(v::read_utf8(path)?),
        "reparse" => json!(v::is_reparse_point(path)?),
        "expected_path" => {
            v::check_expected_path(path, root)?;
            Value::Null
        }
        "inventory" => json!(v::inventory_validation_tree(root)?),
        "discover" => json!(v::discover_case_names(root)?),
        "expected" => json!(v::expected_validation(&names("names"))),
        "ids" => json!(v::case_ids(&names("names"))),
        "split" => {
            let (a, b) = v::split_result_files(&names("names"));
            json!([a, b])
        }
        "git" => json!(v::git_entries(
            &names("names").into_iter().collect::<Vec<_>>(),
            root
        )?),
        "ignored" => {
            v::check_ignored(s("path"), root)?;
            Value::Null
        }
        "schema" => {
            v::check_results_schema(s("text"), &names("known"))?;
            Value::Null
        }
        "result" => json!(v::check_result_file(s("path"), s("text"), &names("known"))?),
        "published" => {
            v::check_published_inventories(&names("names"), root)?;
            Value::Null
        }
        "text" => {
            v::check_text(s("path"), s("text"))?;
            Value::Null
        }
        "main" => {
            let (code, output) = v::main(root)?;
            json!({"code":code,"output":output})
        }
        _ => return Err("unknown probe operation".into()),
    })
}
fn main() {
    let input = io::stdin();
    let mut out = io::BufWriter::new(io::stdout());
    for line in input.lock().lines() {
        let response = (|| -> Result<Value> { invoke(&serde_json::from_str::<Value>(&line?)?) })();
        let value = match response {
            Ok(value) => json!({"ok":value}),
            Err(error) => json!({"error":error.to_string()}),
        };
        writeln!(out, "{value}").unwrap();
        out.flush().unwrap();
    }
}
