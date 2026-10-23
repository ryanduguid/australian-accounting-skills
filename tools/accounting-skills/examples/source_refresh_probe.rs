use accounting_skills::{Result, source_refresh as p};
use serde_json::{Value, json};
use std::io::{self, BufRead, Write};
use std::path::Path;

// An in-memory response qualifies raw text decoding through the production
// interpreter. It is available only in this offline example, never the CLI.
struct CodecResponse {
    header: String,
    body: Vec<u8>,
}
impl p::transport::Transport for CodecResponse {
    fn resolve(&mut self, _: &str) -> Result<()> {
        Ok(())
    }
    fn open(&mut self, url: &str) -> Result<p::transport::Response> {
        Ok(p::transport::Response {
            status: 200,
            reason: "OK".into(),
            final_url: url.into(),
            headers: vec![("Content-Type".into(), self.header.clone())],
            body: Box::new(std::io::Cursor::new(self.body.clone())),
        })
    }
}

fn request(input: &mut impl BufRead, event: Value) -> Result<Value> {
    println!("{event}");
    io::stdout().flush()?;
    let mut line = String::new();
    input.read_line(&mut line)?;
    let value: Value = serde_json::from_str(&line)?;
    if let Some(error) = value.get("__error").and_then(Value::as_str) {
        return Err(error.to_owned().into());
    }
    Ok(value)
}
fn invoke(r: &Value, input: &mut impl BufRead) -> Result<Value> {
    let text = |key: &str| r[key].as_str().unwrap_or("");
    let body = || {
        r["body"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_u64().unwrap() as u8)
            .collect::<Vec<_>>()
    };
    Ok(match text("op") {
        "decoded" => {
            let charset = text("charset").replace('\\', "\\\\").replace('"', "\\\"");
            let mut response = CodecResponse {
                header: format!("text/plain; charset=\"{charset}\""),
                body: body(),
            };
            json!(p::transport::fetch_with(
                &mut response,
                "https://www.ato.gov.au/example",
                1,
                0.0,
                true,
                |_| Ok(())
            ))
        }
        "text" => json!(p::readable_text(&body(), r["charset"].as_str())?),
        "digest" => json!(p::body_digest(
            &body(),
            text("kind"),
            r["charset"].as_str()
        )?),
        "hash" => json!(p::content_digest(text("text"))),
        "date" => json!(p::iso_day(text("text"))),
        "headers" => json!(p::transport::content_type(r["text"].as_str())?),
        "defrag" => json!(p::defrag(text("text"))),
        "join" => json!(p::transport::join(text("base"), text("reference"))),
        "upstream" => json!(p::transport::upstream_last_modified(
            &body(),
            r["last"].as_str(),
            r["served"].as_str()
        )?),
        "review_date" => json!(p::review_date(&r["record"])),
        "reverify" => json!(p::reverify_passed(&r["record"], text("today"))),
        "note" => json!(p::reverify_note(text("text"))),
        "latest" => json!(p::latest_upstream_date(
            &r["record"],
            &serde_json::from_value(r["fetched"].clone())?
        )),
        "classify" => json!(p::classify(
            &r["record"],
            &serde_json::from_value(r["fetched"].clone())?
        )),
        "apply" => {
            let mut record = r["record"].clone();
            p::apply_fetch(
                &mut record,
                &serde_json::from_value(r["fetched"].clone())?,
                text("today"),
            )?;
            record
        }
        "human" => json!(p::human_readiness(&r["record"], text("today"))),
        "readiness" => json!(p::source_readiness(
            &r["record"],
            &serde_json::from_value(r["outcome"].clone())?,
            text("today")
        )),
        "render" => json!(p::render_at(
            &serde_json::from_value(r["report"].clone())?,
            r["write"].as_bool().unwrap_or(false),
            text("swept")
        )),
        "refresh" => {
            let options = p::Options {
                only_skill: text("skill").into(),
                only_url: text("url").into(),
                write: r["write"].as_bool().unwrap_or(false),
                spacing: r["spacing"].as_f64().unwrap_or(0.0),
                today: text("today").into(),
            };
            // The callback is an offline qualification seam, not a production policy override.
            let cell = std::cell::RefCell::new(input);
            json!(p::refresh_with(
                Path::new(text("skills")),
                &options,
                |url| serde_json::from_value(
                    request(&mut *cell.borrow_mut(), json!({"event":"fetch","url":url})).unwrap()
                )
                .unwrap(),
                |seconds| {
                    request(
                        &mut *cell.borrow_mut(),
                        json!({"event":"sleep","seconds":seconds}),
                    )?;
                    Ok(())
                }
            )?)
        }
        "preflight" => {
            let cell = std::cell::RefCell::new(input);
            json!(p::preflight_with(
                text("skill"),
                Path::new(text("skills")),
                text("today"),
                r["spacing"].as_f64().unwrap_or(0.0),
                |url| serde_json::from_value(
                    request(&mut *cell.borrow_mut(), json!({"event":"fetch","url":url})).unwrap()
                )
                .unwrap(),
                |seconds| {
                    request(
                        &mut *cell.borrow_mut(),
                        json!({"event":"sleep","seconds":seconds}),
                    )?;
                    Ok(())
                }
            ))
        }
        "index_files" => json!(p::index_files(Path::new(text("skills")))?),
        "load" => p::load_index(Path::new(text("path")), Path::new(text("skills")))?,
        "dump" => {
            p::dump_index(
                Path::new(text("path")),
                &r["record"],
                Path::new(text("skills")),
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
        let value = match result {
            Ok(v) => json!({"ok":v}),
            Err(e) => json!({"error":e.to_string()}),
        };
        println!("{value}");
        io::stdout().flush().unwrap();
    }
}
