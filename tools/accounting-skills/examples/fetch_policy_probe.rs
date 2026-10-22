use accounting_skills::{Result, source_fetch_policy as p};
use serde_json::{Value, json};
use std::io::{self, BufRead, Read, Write};

struct Body {
    bytes: Vec<u8>,
    position: usize,
    chunk: usize,
    fail: Option<usize>,
    reads: Vec<usize>,
}
impl Read for Body {
    fn read(&mut self, out: &mut [u8]) -> io::Result<usize> {
        self.reads.push(out.len());
        if self.fail.is_some_and(|n| self.position >= n) {
            return Err(io::Error::other("fabricated read failure"));
        }
        let n = out
            .len()
            .min(self.chunk)
            .min(self.bytes.len() - self.position);
        out[..n].copy_from_slice(&self.bytes[self.position..self.position + n]);
        self.position += n;
        Ok(n)
    }
}
fn invoke(r: &Value) -> Result<Value> {
    Ok(match r["op"].as_str().unwrap() {
        "url" => json!(p::checked_url(r["url"].as_str().unwrap())?),
        "address" => json!(p::is_public_address(
            r["address"]
                .as_str()
                .unwrap()
                .split('%')
                .next()
                .unwrap()
                .parse()?
        )),
        "addresses" => {
            let addresses = r["addresses"]
                .as_array()
                .unwrap()
                .iter()
                .map(|v| v.as_str().unwrap().parse())
                .collect::<std::result::Result<Vec<_>, _>>()?;
            p::check_addresses(addresses)?;
            Value::Null
        }
        "constants" => {
            json!({"hosts":p::APPROVED_HOSTS,"edges":p::APPROVED_REDIRECT_EDGES,"redirects":p::MAX_REDIRECTS,"automatic_redirects":p::AUTOMATIC_REDIRECTS,"ceiling":p::MAX_RESPONSE_BYTES,"chunk":p::READ_CHUNK_BYTES})
        }
        "body" => {
            let pattern = r["pattern"]
                .as_array()
                .map(|v| {
                    v.iter()
                        .map(|v| v.as_u64().unwrap() as u8)
                        .collect::<Vec<_>>()
                })
                .unwrap_or_else(|| vec![120]);
            let length = r["size"].as_u64().unwrap() as usize;
            let mut reader = Body {
                bytes: pattern.iter().copied().cycle().take(length).collect(),
                position: 0,
                chunk: r["chunk"].as_u64().unwrap_or(usize::MAX as u64) as usize,
                fail: r["fail"].as_u64().map(|v| v as usize),
                reads: Vec::new(),
            };
            let result = p::bounded_body(&mut reader, r["encoding"].as_str(), r["length"].as_str());
            let result = match result {
                Ok(bytes) => {
                    let mut counts = vec![0usize; 256];
                    for &b in &bytes {
                        counts[b as usize] += 1;
                    }
                    json!({"ok":{"size":bytes.len(),"counts":counts,"prefix":&bytes[..bytes.len().min(64)],"suffix":&bytes[bytes.len().saturating_sub(64)..]}})
                }
                Err(e) => {
                    json!({"error":e.to_string(),"kind":if e.is::<io::Error>() { "io" } else { "policy" }})
                }
            };
            json!({"result":result,"reads":reader.reads,"consumed":reader.position})
        }
        _ => return Err("unknown probe operation".into()),
    })
}
fn main() {
    let input = io::stdin();
    let mut out = io::BufWriter::new(io::stdout());
    for line in input.lock().lines() {
        let result = (|| -> Result<Value> { invoke(&serde_json::from_str::<Value>(&line?)?) })();
        let value = match result {
            Ok(v) => json!({"ok":v}),
            Err(e) => {
                json!({"error":e.to_string(),"kind":if e.is::<io::Error>() { "io" } else { "policy" }})
            }
        };
        writeln!(out, "{value}").unwrap();
        out.flush().unwrap();
    }
}
