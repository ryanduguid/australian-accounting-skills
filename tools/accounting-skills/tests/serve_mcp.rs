// Copyright 2026 Ryan Duguid
// SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

//! `serve-mcp` driven as an MCP client drives it: JSON-RPC lines over the
//! child process's stdin and stdout.
use serde_json::{Value, json};
use std::{
    fs,
    io::Write,
    path::{Path, PathBuf},
    process::{Command, Stdio},
};

fn repository() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

/// Send `lines` to a server for `root`, close its input and return each
/// reply line, parsed.
fn session(root: &Path, lines: &[String]) -> Vec<Value> {
    let mut child = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args(["serve-mcp", "--root"])
        .arg(root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let mut input = child.stdin.take().unwrap();
    for line in lines {
        input.write_all(line.as_bytes()).unwrap();
        input.write_all(b"\n").unwrap();
    }
    drop(input);
    let output = child.wait_with_output().unwrap();
    assert!(output.status.success(), "{output:?}");
    String::from_utf8(output.stdout)
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect()
}

fn request(id: u64, method: &str, params: Value) -> String {
    json!({"jsonrpc": "2.0", "id": id, "method": method, "params": params}).to_string()
}

fn call(id: u64, tool: &str, arguments: Value) -> String {
    request(
        id,
        "tools/call",
        json!({"name": tool, "arguments": arguments}),
    )
}

fn stateless(mut params: Value) -> Value {
    params["_meta"] = json!({
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
    });
    params
}

fn initialize(version: &str) -> String {
    request(
        1,
        "initialize",
        json!({"protocolVersion": version, "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}}),
    )
}

fn reply(replies: &[Value], id: u64) -> &Value {
    let found: Vec<&Value> = replies
        .iter()
        .filter(|reply| reply["id"] == json!(id))
        .collect();
    assert_eq!(found.len(), 1, "one reply for id {id}: {replies:?}");
    found[0]
}

/// The skill folders a person sees: each folder under `.claude/skills`
/// holding a `SKILL.md`.
fn skill_folders(root: &Path) -> Vec<String> {
    let mut names: Vec<String> = fs::read_dir(root.join(".claude/skills"))
        .unwrap()
        .map(|entry| entry.unwrap().path())
        .filter(|path| path.join("SKILL.md").is_file())
        .map(|path| path.file_name().unwrap().to_str().unwrap().to_owned())
        .collect();
    names.sort();
    names
}

#[test]
fn a_client_lists_every_skill_and_gets_each_one_byte_for_byte() {
    let root = repository();
    let expected = skill_folders(&root);
    assert!(expected.iter().any(|name| name == "bas-preparation"));
    let mut lines = vec![
        initialize("2025-11-25"),
        json!({"jsonrpc": "2.0", "method": "notifications/initialized"}).to_string(),
        request(2, "tools/list", json!({})),
        call(3, "list_skills", json!({})),
    ];
    for (index, name) in expected.iter().enumerate() {
        lines.push(call(100 + index as u64, "get_skill", json!({"name": name})));
    }
    let replies = session(&root, &lines);
    assert_eq!(
        replies.len(),
        3 + expected.len(),
        "the notification gets no reply"
    );

    let init = &reply(&replies, 1)["result"];
    assert_eq!(init["protocolVersion"], "2025-11-25");
    assert_eq!(init["capabilities"], json!({"tools": {}}));
    assert_eq!(init["serverInfo"]["name"], "accounting-skills");

    let tools: Vec<&str> = reply(&replies, 2)["result"]["tools"]
        .as_array()
        .unwrap()
        .iter()
        .map(|tool| tool["name"].as_str().unwrap())
        .collect();
    assert_eq!(tools, ["list_skills", "search_skills", "get_skill"]);

    let listed = &reply(&replies, 3)["result"];
    assert_eq!(listed["isError"], false);
    let names: Vec<&str> = listed["structuredContent"]["skills"]
        .as_array()
        .unwrap()
        .iter()
        .map(|skill| skill["name"].as_str().unwrap())
        .collect();
    assert_eq!(names, expected);
    let text: Value = serde_json::from_str(listed["content"][0]["text"].as_str().unwrap()).unwrap();
    assert_eq!(text, listed["structuredContent"]);

    for (index, name) in expected.iter().enumerate() {
        let result = &reply(&replies, 100 + index as u64)["result"];
        let folder = root.join(".claude/skills").join(name);
        assert_eq!(result["isError"], false, "{name}: {result}");
        let skill_md = fs::read(folder.join("SKILL.md")).unwrap();
        assert_eq!(
            result["content"][0]["text"].as_str().unwrap().as_bytes(),
            skill_md,
            "{name}"
        );
        assert_eq!(
            result["structuredContent"]["skill_md"]
                .as_str()
                .unwrap()
                .as_bytes(),
            skill_md,
            "{name}"
        );
        let file = ["sources.json", "sources.exempt.json"]
            .into_iter()
            .find(|file| folder.join(file).is_file())
            .unwrap_or_else(|| panic!("{name} has no sources file"));
        let sources = fs::read(folder.join(file)).unwrap();
        assert_eq!(result["structuredContent"]["sources_file"], file, "{name}");
        assert_eq!(
            result["structuredContent"]["sources"]
                .as_str()
                .unwrap()
                .as_bytes(),
            sources,
            "{name}"
        );
        assert_eq!(
            result["content"][1]["text"].as_str().unwrap().as_bytes(),
            sources,
            "{name}"
        );
        let mut references: Vec<PathBuf> = fs::read_dir(folder.join("references"))
            .map(|entries| entries.map(|entry| entry.unwrap().path()).collect())
            .unwrap_or_default();
        references.sort();
        let served = result["structuredContent"]["references"]
            .as_array()
            .unwrap();
        assert_eq!(served.len(), references.len(), "{name}");
        assert_eq!(
            result["content"].as_array().unwrap().len(),
            2 + references.len(),
            "{name}"
        );
        for (index, path) in references.iter().enumerate() {
            let bytes = fs::read(path).unwrap();
            let relative = format!("references/{}", path.file_name().unwrap().to_str().unwrap());
            assert_eq!(served[index]["path"], relative.as_str(), "{name}");
            assert_eq!(
                served[index]["text"].as_str().unwrap().as_bytes(),
                bytes,
                "{name}"
            );
            assert_eq!(
                result["content"][2 + index]["text"]
                    .as_str()
                    .unwrap()
                    .as_bytes(),
                bytes,
                "{name}"
            );
        }
        if name == "bas-preparation" {
            assert_eq!(served[0]["path"], "references/transaction-gst-review.md");
        }
    }
}

#[test]
fn the_stateless_revision_needs_no_initialize() {
    let root = repository();
    let lines = [
        request(1, "server/discover", stateless(json!({}))),
        request(2, "tools/list", stateless(json!({}))),
        request(
            3,
            "tools/call",
            stateless(json!({"name": "get_skill", "arguments": {"name": "bas-preparation"}})),
        ),
        request(
            4,
            "tools/call",
            stateless(json!({"name": "search_skills", "arguments": {"query": "BAS gst"}})),
        ),
        request(5, "ping", stateless(json!({}))),
    ];
    let replies = session(&root, &lines);
    let discover = &reply(&replies, 1)["result"];
    assert_eq!(discover["supportedVersions"], json!(["2026-07-28"]));
    assert_eq!(discover["resultType"], "complete");
    assert_eq!(
        discover["_meta"]["io.modelcontextprotocol/serverInfo"]["name"],
        "accounting-skills"
    );
    assert_eq!(
        reply(&replies, 2)["result"]["tools"]
            .as_array()
            .unwrap()
            .len(),
        3
    );
    let skill_md = fs::read(root.join(".claude/skills/bas-preparation/SKILL.md")).unwrap();
    assert_eq!(
        reply(&replies, 3)["result"]["content"][0]["text"]
            .as_str()
            .unwrap()
            .as_bytes(),
        skill_md
    );
    let found = reply(&replies, 4)["result"]["structuredContent"]["skills"]
        .as_array()
        .unwrap();
    let in_head: Vec<(bool, &str)> = found
        .iter()
        .map(|skill| {
            let name = skill["name"].as_str().unwrap();
            let head = format!("{name}\n{}", skill["description"].as_str().unwrap()).to_lowercase();
            (head.contains("bas") && head.contains("gst"), name)
        })
        .collect();
    assert!(in_head.contains(&(true, "bas-preparation")), "{in_head:?}");
    assert!(
        in_head.iter().any(|(head, _)| !head),
        "some matches are in SKILL.md only: {in_head:?}"
    );
    assert!(
        in_head.is_sorted_by(|a, b| a.0 >= b.0),
        "name and description matches come first: {in_head:?}"
    );
    for (_, name) in &in_head {
        let body = fs::read_to_string(root.join(".claude/skills").join(name).join("SKILL.md"))
            .unwrap()
            .to_lowercase();
        assert!(body.contains("bas") && body.contains("gst"), "{name}");
    }
    assert_eq!(reply(&replies, 5)["result"]["resultType"], "complete");
}

#[test]
fn version_and_message_errors_follow_the_specification() {
    let root = repository();
    let mut unknown_version = stateless(json!({}));
    unknown_version["_meta"]["io.modelcontextprotocol/protocolVersion"] = json!("1900-01-01");
    let lines = [
        request(1, "tools/list", json!({})),
        request(2, "tools/list", unknown_version),
        request(
            3,
            "tools/list",
            json!({"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}}),
        ),
        "not json".to_owned(),
        "[]".to_owned(),
        json!({"id": 4, "method": "ping"}).to_string(),
        request(5, "resources/list", stateless(json!({}))),
        request(
            6,
            "tools/call",
            stateless(json!({"name": "delete_skill", "arguments": {}})),
        ),
        request(
            7,
            "tools/call",
            stateless(json!({"name": "get_skill", "arguments": {}})),
        ),
        request(
            8,
            "tools/call",
            stateless(json!({"name": "search_skills", "arguments": {"query": "  "}})),
        ),
        json!({"jsonrpc": "2.0", "id": 9, "method": "tools/list", "params": []}).to_string(),
        json!({"jsonrpc": "2.0", "id": 10, "result": {}}).to_string(),
        request(
            11,
            "tools/call",
            stateless(json!({"name": "get_skill", "arguments": "bas-preparation"})),
        ),
    ];
    let replies = session(&root, &lines);
    let code = |id: u64| reply(&replies, id)["error"]["code"].as_i64().unwrap();
    assert_eq!(
        code(1),
        -32602,
        "a request with no version and no initialize is malformed"
    );
    assert_eq!(code(2), -32022);
    assert_eq!(
        reply(&replies, 2)["error"]["data"],
        json!({"supported": ["2026-07-28"], "requested": "1900-01-01"})
    );
    assert_eq!(code(3), -32602, "clientCapabilities is required");
    let unaddressed: Vec<i64> = replies
        .iter()
        .filter(|reply| reply["id"].is_null())
        .map(|reply| reply["error"]["code"].as_i64().unwrap())
        .collect();
    assert_eq!(unaddressed, [-32700, -32600]);
    assert_eq!(code(4), -32600, "jsonrpc must be 2.0");
    assert_eq!(code(5), -32601);
    assert_eq!(code(6), -32602);
    for id in [7, 8] {
        assert_eq!(reply(&replies, id)["result"]["isError"], true, "{id}");
    }
    assert_eq!(code(9), -32602);
    assert_eq!(code(11), -32602);
    assert_eq!(replies.len(), 12, "the client's own response gets no reply");
}

#[test]
fn initialize_offers_the_newest_handshake_revision_for_an_unknown_one() {
    for (asked, agreed) in [("2025-06-18", "2025-06-18"), ("2024-01-01", "2025-11-25")] {
        let replies = session(
            &repository(),
            &[initialize(asked), request(2, "tools/list", json!({}))],
        );
        assert_eq!(reply(&replies, 1)["result"]["protocolVersion"], agreed);
        assert_eq!(
            reply(&replies, 2)["result"]["tools"]
                .as_array()
                .unwrap()
                .len(),
            3
        );
    }
}

const SECRET: &str = "SECRET-OUTSIDE-THE-SKILLS";

/// A tree with one skill, `a`, and a secret file beside `.claude`.
fn fixture() -> tempfile::TempDir {
    let root = tempfile::tempdir().unwrap();
    let skill = root.path().join(".claude/skills/a");
    fs::create_dir_all(&skill).unwrap();
    fs::write(
        skill.join("SKILL.md"),
        "---\nname: a\ndescription: \"Fixture.\"\n---\n\n# A\n",
    )
    .unwrap();
    fs::write(root.path().join("secret.txt"), SECRET).unwrap();
    fs::create_dir(root.path().join("outside")).unwrap();
    fs::write(
        root.path().join("outside/SKILL.md"),
        format!("---\nname: x\ndescription: \"{SECRET}\"\n---\n"),
    )
    .unwrap();
    root
}

fn assert_refused(replies: &[Value], id: u64) {
    let result = &reply(replies, id)["result"];
    assert_eq!(result["isError"], true, "{id}: {result}");
    assert!(!result.to_string().contains(SECRET), "{id}: {result}");
}

#[test]
fn get_skill_refuses_any_name_that_is_not_a_listed_skill() {
    let root = fixture();
    let secret = root.path().join("secret.txt");
    let names = [
        "../../secret.txt".to_owned(),
        "..".to_owned(),
        ".".to_owned(),
        String::new(),
        "a/../../../secret.txt".to_owned(),
        "../../outside".to_owned(),
        "a/SKILL.md".to_owned(),
        "A".to_owned(),
        secret.to_str().unwrap().to_owned(),
        "/etc/passwd".to_owned(),
        r"..\..\secret.txt".to_owned(),
        r"C:\Windows\win.ini".to_owned(),
    ];
    let lines: Vec<String> = std::iter::once(initialize("2025-11-25"))
        .chain(
            names
                .iter()
                .enumerate()
                .map(|(i, name)| call(10 + i as u64, "get_skill", json!({"name": name}))),
        )
        .chain([call(2, "get_skill", json!({"name": "a"}))])
        .collect();
    let replies = session(root.path(), &lines);
    for id in 10..10 + names.len() as u64 {
        assert_refused(&replies, id);
    }
    assert_eq!(
        reply(&replies, 2)["result"]["structuredContent"]["sources"],
        Value::Null
    );
}

#[cfg(unix)]
#[test]
fn links_that_leave_the_skills_folder_are_refused() {
    use std::os::unix::fs::symlink;
    for (link, target) in [
        (".claude/skills/linked", "outside"),
        (".claude/skills/a/sources.json", "secret.txt"),
        (".claude/skills/a/references", "outside"),
    ] {
        let root = fixture();
        symlink(root.path().join(target), root.path().join(link)).unwrap();
        let replies = session(
            root.path(),
            &[
                initialize("2025-11-25"),
                call(2, "list_skills", json!({})),
                call(3, "get_skill", json!({"name": "linked"})),
                call(4, "get_skill", json!({"name": "a"})),
            ],
        );
        if link.ends_with("linked") {
            assert_refused(&replies, 2);
            assert_refused(&replies, 3);
            assert_eq!(reply(&replies, 4)["result"]["isError"], false);
        } else {
            assert_eq!(reply(&replies, 2)["result"]["isError"], false);
            assert_refused(&replies, 4);
        }
    }
}

#[test]
fn a_tree_without_skills_is_refused_at_start() {
    let root = tempfile::tempdir().unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_accounting-skills"))
        .args(["serve-mcp", "--root"])
        .arg(root.path())
        .stdin(Stdio::null())
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(1));
    assert!(String::from_utf8_lossy(&output.stderr).contains("holds no .claude/skills folder"));
    assert!(
        output.stdout.is_empty(),
        "nothing but MCP messages may reach stdout"
    );
}
