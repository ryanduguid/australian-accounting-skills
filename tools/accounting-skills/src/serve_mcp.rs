// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! `accounting-skills serve-mcp`: a read-only Model Context Protocol server
//! over stdio. Its 3 tools list, search and return the skills under
//! `.claude/skills` of one tree. It reads only regular files inside that
//! folder, follows no link that leaves it and opens no network connection.
//!
//! It speaks the stateless 2026-07-28 revision, where each request carries its
//! protocol version in `_meta`, and answers `initialize` for clients of the
//! handshake revisions listed in `HANDSHAKE`.
use crate::{Result, canonical_root, discover_skills, strict_yaml::card_mapping, within_root};
use serde_json::{Map, Value, json};
use std::{
    ffi::OsString,
    fs,
    io::{self, BufRead, Write},
    path::{Path, PathBuf},
};

/// The revision a request names in `_meta`.
const STATELESS: &[&str] = &["2026-07-28"];
/// Revisions that begin with `initialize`, newest first. The messages this
/// server sends have the same shape in each.
const HANDSHAKE: &[&str] = &["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"];
const VERSION_KEY: &str = "io.modelcontextprotocol/protocolVersion";
const CAPABILITIES_KEY: &str = "io.modelcontextprotocol/clientCapabilities";
const SERVER_INFO_KEY: &str = "io.modelcontextprotocol/serverInfo";
const INSTRUCTIONS: &str = "Australian accounting and tax preparation workflows. Call list_skills or search_skills to find a workflow, then get_skill and follow the SKILL.md it returns. Preparation only: nothing here lodges, files or pays, and an authorised person reviews every output.";

/// A JSON-RPC error: code, message and optional data.
struct Fault(i64, String, Option<Value>);

fn invalid_params(message: impl Into<String>) -> Fault {
    Fault(-32602, message.into(), None)
}

struct Server {
    root: PathBuf,
    skills: PathBuf,
    /// The revision agreed by `initialize`, if a client sent one.
    handshake: Option<&'static str>,
}

impl Server {
    /// A server for the tree at `root`, which must hold `.claude/skills`.
    fn new(root: &Path) -> Result<Self> {
        let root = canonical_root(root)?;
        let skills = root.join(".claude/skills");
        if !skills.is_dir() {
            return Err(format!("{} holds no .claude/skills folder", root.display()).into());
        }
        Ok(Self {
            root,
            skills,
            handshake: None,
        })
    }

    /// The reply to one line of input, or `None` for a notification or a
    /// response from the client.
    fn handle(&mut self, line: &[u8]) -> Option<Value> {
        let Ok(message) = serde_json::from_slice::<Value>(line) else {
            return Some(reply(
                Value::Null,
                Err(Fault(-32700, "Parse error".into(), None)),
            ));
        };
        let Some(request) = message.as_object() else {
            return Some(reply(
                Value::Null,
                Err(Fault(-32600, "Invalid Request".into(), None)),
            ));
        };
        let id = request.get("id");
        let method = request.get("method").and_then(Value::as_str);
        if method.is_none() && (request.contains_key("result") || request.contains_key("error")) {
            return None;
        }
        if method.is_some() && id.is_none() {
            return None;
        }
        let (Some(method), Some(id)) = (
            method,
            id.filter(|id| id.is_string() || id.is_i64() || id.is_u64()),
        ) else {
            return Some(reply(
                Value::Null,
                Err(Fault(-32600, "Invalid Request".into(), None)),
            ));
        };
        if request.get("jsonrpc") != Some(&json!("2.0")) {
            return Some(reply(
                id.clone(),
                Err(Fault(-32600, "Invalid Request".into(), None)),
            ));
        }
        let empty = Map::new();
        let params = match request.get("params") {
            None => &empty,
            Some(Value::Object(params)) => params,
            Some(_) => {
                return Some(reply(
                    id.clone(),
                    Err(invalid_params("params must be an object")),
                ));
            }
        };
        Some(reply(id.clone(), self.respond(method, params)))
    }

    fn respond(
        &mut self,
        method: &str,
        params: &Map<String, Value>,
    ) -> std::result::Result<Value, Fault> {
        if method == "initialize" {
            return self.initialize(params);
        }
        self.check_version(method, params)?;
        match method {
            "server/discover" => Ok(complete(json!({
                "supportedVersions": STATELESS,
                "capabilities": {"tools": {}},
                "instructions": INSTRUCTIONS,
                "ttlMs": 0,
                "cacheScope": "public",
            }))),
            "ping" => Ok(complete(json!({}))),
            "tools/list" => Ok(complete(
                json!({"tools": tools(), "ttlMs": 0, "cacheScope": "public"}),
            )),
            "tools/call" => self.call(params),
            _ => Err(Fault(-32601, format!("Method not found: {method}"), None)),
        }
    }

    /// Refuse a request that names an unsupported version in `_meta`, or
    /// names none when no `initialize` came first. `server/discover` needs no
    /// version.
    fn check_version(
        &self,
        method: &str,
        params: &Map<String, Value>,
    ) -> std::result::Result<(), Fault> {
        let meta = params.get("_meta").and_then(Value::as_object);
        let Some(version) = meta.and_then(|meta| meta.get(VERSION_KEY)) else {
            if method == "server/discover" || self.handshake.is_some() {
                return Ok(());
            }
            return Err(invalid_params(format!(
                "_meta must carry {VERSION_KEY}, or the client must send initialize first"
            )));
        };
        let version = version.as_str().unwrap_or_default();
        if !STATELESS.contains(&version) {
            return Err(Fault(
                -32022,
                "Unsupported protocol version".into(),
                Some(json!({"supported": STATELESS, "requested": version})),
            ));
        }
        let declared = meta
            .and_then(|meta| meta.get(CAPABILITIES_KEY))
            .is_some_and(Value::is_object);
        if method != "server/discover" && !declared {
            return Err(invalid_params(format!(
                "_meta must carry {CAPABILITIES_KEY}"
            )));
        }
        Ok(())
    }

    fn initialize(&mut self, params: &Map<String, Value>) -> std::result::Result<Value, Fault> {
        let requested = params
            .get("protocolVersion")
            .and_then(Value::as_str)
            .ok_or_else(|| invalid_params("initialize needs protocolVersion"))?;
        // Speak, friend, and enter: a client asking for a revision this server
        // lacks is offered the newest.
        let agreed = HANDSHAKE
            .iter()
            .copied()
            .find(|version| *version == requested)
            .unwrap_or(HANDSHAKE[0]);
        self.handshake = Some(agreed);
        Ok(complete(json!({
            "protocolVersion": agreed,
            "capabilities": {"tools": {}},
            "serverInfo": server_info(),
            "instructions": INSTRUCTIONS,
        })))
    }

    fn call(&self, params: &Map<String, Value>) -> std::result::Result<Value, Fault> {
        let name = params
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| invalid_params("tools/call needs a tool name"))?;
        let empty = Map::new();
        let arguments = match params.get("arguments") {
            None => &empty,
            Some(Value::Object(arguments)) => arguments,
            Some(_) => return Err(invalid_params("arguments must be an object")),
        };
        let outcome = match name {
            "list_skills" => self.list(None),
            "search_skills" => {
                text_argument(arguments, "query").and_then(|query| self.list(Some(query)))
            }
            "get_skill" => text_argument(arguments, "name").and_then(|skill| self.get(skill)),
            _ => return Err(invalid_params(format!("Unknown tool: {name}"))),
        };
        Ok(complete(match outcome {
            Ok((content, structured)) => {
                json!({"content": content, "structuredContent": structured, "isError": false})
            }
            Err(error) => json!({"content": [text(&error.to_string())], "isError": true}),
        }))
    }

    /// Every skill, or those whose name, description or `SKILL.md` holds each
    /// word of `query`; name and description matches first, then by name.
    fn list(&self, query: Option<&str>) -> Result<(Value, Value)> {
        let words: Option<Vec<String>> =
            query.map(|query| query.split_whitespace().map(str::to_lowercase).collect());
        if words.as_ref().is_some_and(Vec::is_empty) {
            return Err("query must contain a word".into());
        }
        let mut found = Vec::new();
        for skill in discover_skills(&self.root)? {
            let body = self
                .read(&skill, "SKILL.md")?
                .ok_or_else(|| format!("{skill}/SKILL.md is missing"))?;
            let description =
                description(&body).map_err(|error| format!("{skill}/SKILL.md: {error}"))?;
            let rank = match &words {
                None => 0,
                Some(words) => {
                    let head = format!("{skill}\n{description}").to_lowercase();
                    let body = body.to_lowercase();
                    if words.iter().all(|word| head.contains(word)) {
                        0
                    } else if words
                        .iter()
                        .all(|word| head.contains(word) || body.contains(word))
                    {
                        1
                    } else {
                        continue;
                    }
                }
            };
            found.push((rank, json!({"name": skill, "description": description})));
        }
        // discover_skills returns names in order, and the sort is stable.
        found.sort_by_key(|(rank, _)| *rank);
        let structured =
            json!({"skills": found.into_iter().map(|(_, skill)| skill).collect::<Vec<_>>()});
        Ok((json!([text(&structured.to_string())]), structured))
    }

    /// A skill's `SKILL.md`, its sources file and the files in its
    /// `references` folder, which its `SKILL.md` tells the agent to read, each
    /// exactly as on disk.
    fn get(&self, skill: &str) -> Result<(Value, Value)> {
        // Only a name list_skills returns is read, so a path, `..` or a
        // different spelling never reaches the file system.
        if !discover_skills(&self.root)?
            .iter()
            .any(|known| known == skill)
        {
            return Err(format!("no skill is named {skill:?}; list_skills gives the names").into());
        }
        let body = self
            .read(skill, "SKILL.md")?
            .ok_or_else(|| format!("{skill}/SKILL.md is missing"))?;
        let mut content = vec![text(&body)];
        let mut structured =
            json!({"name": skill, "skill_md": body, "sources_file": null, "sources": null});
        for file in ["sources.json", "sources.exempt.json"] {
            if let Some(sources) = self.read(skill, file)? {
                content.push(text(&sources));
                structured["sources_file"] = json!(file);
                structured["sources"] = json!(sources);
                break;
            }
        }
        let mut references = Vec::new();
        for (path, body) in self.references(skill)? {
            content.push(text(&body));
            references.push(json!({"path": path, "text": body}));
        }
        structured["references"] = json!(references);
        Ok((Value::Array(content), structured))
    }

    /// Each file in the skill's `references` folder, by name, as
    /// (`references/NAME`, text).
    fn references(&self, skill: &str) -> Result<Vec<(String, String)>> {
        let folder = within_root(&self.skills, &Path::new(skill).join("references"))
            .map_err(|error| format!("{skill}/references: {error}"))?;
        if !fs::symlink_metadata(&folder).is_ok_and(|metadata| metadata.is_dir()) {
            return Ok(Vec::new());
        }
        let mut names = Vec::new();
        for entry in fs::read_dir(&folder)? {
            names.push(
                entry?
                    .file_name()
                    .into_string()
                    .map_err(|_| format!("{skill}/references holds a name that is not Unicode"))?,
            );
        }
        names.sort();
        let mut files = Vec::new();
        for name in names {
            let path = format!("references/{name}");
            let body = self
                .read(skill, &path)?
                .ok_or_else(|| format!("{skill}/{path} disappeared"))?;
            files.push((path, body));
        }
        Ok(files)
    }

    /// The text of `file` in the skill folder, or `None` when it does not
    /// exist. Refuses a path, or a link along it, that leaves `.claude/skills`,
    /// and a file that is not UTF-8.
    fn read(&self, skill: &str, file: &str) -> Result<Option<String>> {
        let path = within_root(&self.skills, &Path::new(skill).join(file))
            .map_err(|error| format!("{skill}/{file}: {error}"))?;
        match fs::symlink_metadata(&path) {
            Ok(metadata) if metadata.is_file() => Ok(Some(
                String::from_utf8(fs::read(&path)?)
                    .map_err(|_| format!("{skill}/{file} is not UTF-8"))?,
            )),
            Ok(_) => Err(format!("{skill}/{file} is not a regular file").into()),
            Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(None),
            Err(error) => Err(error.into()),
        }
    }
}

fn reply(id: Value, outcome: std::result::Result<Value, Fault>) -> Value {
    match outcome {
        Ok(result) => json!({"jsonrpc": "2.0", "id": id, "result": result}),
        Err(Fault(code, message, data)) => {
            let mut error = json!({"code": code, "message": message});
            if let Some(data) = data {
                error["data"] = data;
            }
            json!({"jsonrpc": "2.0", "id": id, "error": error})
        }
    }
}

fn server_info() -> Value {
    json!({"name": "accounting-skills", "version": env!("CARGO_PKG_VERSION")})
}

/// A result as the 2026-07-28 revision requires it; earlier revisions ignore
/// the added fields.
fn complete(mut result: Value) -> Value {
    result["resultType"] = json!("complete");
    result["_meta"] = json!({SERVER_INFO_KEY: server_info()});
    result
}

fn text(body: &str) -> Value {
    json!({"type": "text", "text": body})
}

fn text_argument<'a>(arguments: &'a Map<String, Value>, name: &str) -> Result<&'a str> {
    Ok(arguments
        .get(name)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("{name} must be a string"))?)
}

fn tools() -> Value {
    let read_only = json!({"readOnlyHint": true, "openWorldHint": false});
    let string = |description: &str| json!({"type": "string", "description": description});
    json!([
        {
            "name": "list_skills",
            "description": "List every skill in the pack with its description.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": false},
            "annotations": read_only,
        },
        {
            "name": "search_skills",
            "description": "List the skills whose name, description or SKILL.md contains every word of the query, ignoring case; name and description matches first.",
            "inputSchema": {
                "type": "object",
                "properties": {"query": string("Words to find, such as 'BAS GST'.")},
                "required": ["query"],
                "additionalProperties": false,
            },
            "annotations": read_only,
        },
        {
            "name": "get_skill",
            "description": "Return a skill's SKILL.md, then its sources.json (or sources.exempt.json), then each file in its references folder, exactly as in the pack. Follow the SKILL.md.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": string("A name list_skills returns, such as 'bas-preparation'.")},
                "required": ["name"],
                "additionalProperties": false,
            },
            "annotations": read_only,
        },
    ])
}

/// The `description` field of a `SKILL.md` front matter block.
fn description(body: &str) -> Result<String> {
    let body = body.replace("\r\n", "\n");
    let raw = body
        .strip_prefix("---\n")
        .and_then(|rest| rest.split_once("\n---\n"))
        .ok_or("front matter must open and close with '---'")?
        .0;
    Ok(card_mapping(raw)?["description"]
        .as_str()
        .ok_or("front matter needs a description")?
        .to_owned())
}

/// Answer each line of `input` on `output` until `input` ends.
fn serve(root: &Path, input: impl BufRead, mut output: impl Write) -> Result<()> {
    let mut server = Server::new(root)?;
    for line in input.split(b'\n') {
        let line = line?;
        let line = line.strip_suffix(b"\r").unwrap_or(&line);
        if line.iter().all(u8::is_ascii_whitespace) {
            continue;
        }
        if let Some(reply) = server.handle(line) {
            // serde_json escapes every newline inside a string, so one reply is one line.
            serde_json::to_writer(&mut output, &reply)?;
            output.write_all(b"\n")?;
            output.flush()?;
        }
    }
    Ok(())
}

pub fn cli(mut args: impl Iterator<Item = OsString>) -> Result<u8> {
    let mut root = std::env::current_dir()?;
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--root") => {
                root = PathBuf::from(
                    args.next()
                        .filter(|arg| !arg.as_encoded_bytes().starts_with(b"-"))
                        .ok_or("--root requires a path")?,
                );
            }
            _ => return Err("usage: accounting-skills serve-mcp [--root PATH]".into()),
        }
    }
    serve(&root, io::stdin().lock(), io::stdout().lock())?;
    Ok(0)
}
