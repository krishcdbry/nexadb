use anyhow::{Context, Result};
use clap::Parser;
use colored::*;
use rmp_serde::{Deserializer, Serializer};
use rustyline::error::ReadlineError;
use rustyline::DefaultEditor;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::io::{Read, Write};
use std::net::TcpStream;
const MAGIC: u32 = 0x4E455841; // "NEXA"
const VERSION: u8 = 0x01;

// Message types
const MSG_CONNECT: u8 = 0x01;
const MSG_CREATE: u8 = 0x02;
const MSG_READ: u8 = 0x03;
const MSG_UPDATE: u8 = 0x04;
const MSG_DELETE: u8 = 0x05;
const MSG_QUERY: u8 = 0x06;
const MSG_VECTOR_SEARCH: u8 = 0x07;
const MSG_LIST_COLLECTIONS: u8 = 0x20;

// Response types
const MSG_SUCCESS: u8 = 0x81;
const MSG_ERROR: u8 = 0x82;
const MSG_NOT_FOUND: u8 = 0x83;

#[derive(Parser, Debug)]
#[command(name = "nexa")]
#[command(about = "Nexa - Interactive CLI for NexaDB", long_about = None)]
struct Args {
    /// NexaDB server host
    #[arg(long, default_value = "localhost")]
    host: String,

    /// NexaDB server port
    #[arg(long, default_value = "6970")]
    port: u16,

    /// Username
    #[arg(short, long, default_value = "root")]
    username: String,

    /// Prompt for password
    #[arg(short, long)]
    password: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct Message {
    #[serde(flatten)]
    data: Value,
}

struct NexaClient {
    stream: TcpStream,
    current_collection: Option<String>,
}

impl NexaClient {
    fn connect(host: &str, port: u16, username: &str, password: &str) -> Result<Self> {
        println!("{}", format!("Connecting to {}:{}...", host, port).cyan());

        let stream = TcpStream::connect(format!("{}:{}", host, port))
            .context("Failed to connect to NexaDB server")?;

        let mut client = Self {
            stream,
            current_collection: None,
        };

        // Send handshake
        let auth_data = serde_json::json!({
            "username": username,
            "password": password
        });
        client.send_message(MSG_CONNECT, &auth_data)?;

        println!("{}", "✓ Connected to NexaDB v2.3.0".green().bold());
        println!();

        Ok(client)
    }

    fn send_message(&mut self, msg_type: u8, data: &Value) -> Result<Value> {
        // Encode payload with MessagePack
        let mut payload = Vec::new();
        data.serialize(&mut Serializer::new(&mut payload))?;

        // Build header (12 bytes)
        let mut header = vec![0u8; 12];
        header[0..4].copy_from_slice(&MAGIC.to_be_bytes());
        header[4] = VERSION;
        header[5] = msg_type;
        header[6..8].copy_from_slice(&0u16.to_be_bytes()); // Flags
        header[8..12].copy_from_slice(&(payload.len() as u32).to_be_bytes());

        // Send header + payload
        self.stream.write_all(&header)?;
        self.stream.write_all(&payload)?;
        self.stream.flush()?;

        // Read response
        self.read_response()
    }

    fn read_response(&mut self) -> Result<Value> {
        // Read header (12 bytes)
        let mut header = [0u8; 12];
        self.stream.read_exact(&mut header)?;

        let magic = u32::from_be_bytes([header[0], header[1], header[2], header[3]]);
        let msg_type = header[5];
        let payload_len = u32::from_be_bytes([header[8], header[9], header[10], header[11]]) as usize;

        if magic != MAGIC {
            anyhow::bail!("Invalid protocol magic: {:x}", magic);
        }

        // Read payload
        let mut payload = vec![0u8; payload_len];
        self.stream.read_exact(&mut payload)?;

        // Decode MessagePack
        let mut de = Deserializer::new(&payload[..]);
        let data: Value = Deserialize::deserialize(&mut de)?;

        // Handle response type
        match msg_type {
            MSG_SUCCESS => Ok(data),
            MSG_ERROR => {
                let error = data.get("error")
                    .and_then(|e| e.as_str())
                    .unwrap_or("Unknown error");
                anyhow::bail!("{}", error);
            }
            MSG_NOT_FOUND => anyhow::bail!("Not found"),
            _ => anyhow::bail!("Unknown response type: {}", msg_type),
        }
    }
}

fn print_banner() {
    let banner = r#"
╔═══════════════════════════════════════════════════════════════════════╗
║     ███╗   ██╗███████╗██╗  ██╗ █████╗ ██████╗ ██████╗               ║
║     ████╗  ██║██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗              ║
║     ██╔██╗ ██║█████╗   ╚███╔╝ ███████║██║  ██║██████╔╝              ║
║     ██║╚██╗██║██╔══╝   ██╔██╗ ██╔══██║██║  ██║██╔══██╗              ║
║     ██║ ╚████║███████╗██╔╝ ██╗██║  ██║██████╔╝██████╔╝              ║
║     ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝               ║
║                                                                       ║
║            Database for AI Developers - v2.3.0                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

Type 'help' for commands or 'exit' to quit.
    "#;
    println!("{}", banner.cyan());
}

fn print_help() {
    let help = r#"
╔═══════════════════════════════════════════════════════════════════╗
║                        Nexa CLI Commands                          ║
╚═══════════════════════════════════════════════════════════════════╝

Collection Management:
  use <collection>              Switch to a collection
  collections                   List all collections

Document Operations:
  create <json>                 Create a document
  query <json>                  Query documents
  update <id> <json>            Update a document
  delete <id>                   Delete a document
  count [json]                  Count documents

Vector Search:
  vector_search <vector> [limit] [dimensions]
                                Search by vector similarity

Examples:
  use movies
  create {"title": "The Matrix", "year": 1999}
  query {"year": {"$gte": 2000}}
  update doc_abc123 {"year": 2000}
  delete doc_abc123
  vector_search [0.1, 0.95, 0.1, 0.8] 3 4
  count {"status": "active"}

System:
  help                          Show this help
  exit / quit                   Exit CLI

Press Ctrl+C to cancel current command
Press Ctrl+D to quit
    "#;
    println!("{}", help.cyan());
}

fn handle_command(client: &mut NexaClient, line: &str) -> Result<bool> {
    let parts: Vec<&str> = line.trim().split_whitespace().collect();
    if parts.is_empty() {
        return Ok(false);
    }

    let cmd = parts[0].to_lowercase();

    match cmd.as_str() {
        "exit" | "quit" => {
            println!("{}", "Goodbye! 👋".blue());
            return Ok(true);
        }
        "help" => {
            print_help();
        }
        "use" => {
            if parts.len() < 2 {
                println!("{}", "✗ Collection name required".red());
                println!("{}", "Usage: use <collection>".blue());
                return Ok(false);
            }
            let collection = parts[1];
            client.current_collection = Some(collection.to_string());
            println!("{}", format!("✓ Switched to collection '{}'", collection).green());
        }
        "collections" => {
            let msg = serde_json::json!({});
            match client.send_message(MSG_LIST_COLLECTIONS, &msg) {
                Ok(result) => {
                    if let Some(collections) = result.get("collections").and_then(|c| c.as_array()) {
                        if collections.is_empty() {
                            println!("{}", "⚠ No collections found".yellow());
                        } else {
                            println!("{}", format!("✓ Found {} collection(s):", collections.len()).green());
                            for (i, col) in collections.iter().enumerate() {
                                let col_name = col.as_str().unwrap_or("unknown");
                                let marker = if Some(col_name.to_string()) == client.current_collection {
                                    "*"
                                } else {
                                    " "
                                };
                                println!("{} [{}] {}", marker, i + 1, col_name.cyan());
                            }
                        }
                    } else {
                        println!("{}", "⚠ No collections found".yellow());
                    }
                }
                Err(e) => println!("{}", format!("✗ Error: {}", e).red()),
            }
        }
        "create" => {
            if client.current_collection.is_none() {
                println!("{}", "✗ No collection selected. Use 'use <collection>' first.".red());
                return Ok(false);
            }
            let json_str = line.trim_start_matches("create").trim();
            if json_str.is_empty() {
                println!("{}", "✗ JSON data required".red());
                return Ok(false);
            }

            let data: Value = serde_json::from_str(json_str)?;
            let msg = serde_json::json!({
                "collection": client.current_collection,
                "data": data
            });

            match client.send_message(MSG_CREATE, &msg) {
                Ok(result) => {
                    let doc_id = result.get("document_id")
                        .and_then(|id| id.as_str())
                        .unwrap_or("N/A");
                    println!("{}", format!("✓ Document created: {}", doc_id).green());
                    println!("{}", serde_json::to_string_pretty(&result)?.cyan());
                }
                Err(e) => println!("{}", format!("✗ Error: {}", e).red()),
            }
        }
        "query" => {
            if client.current_collection.is_none() {
                println!("{}", "✗ No collection selected. Use 'use <collection>' first.".red());
                return Ok(false);
            }

            let json_str = line.trim_start_matches("query").trim();
            let filters: Value = if json_str.is_empty() {
                serde_json::json!({})
            } else {
                serde_json::from_str(json_str)?
            };

            let msg = serde_json::json!({
                "collection": client.current_collection,
                "filters": filters,
                "limit": 100
            });

            match client.send_message(MSG_QUERY, &msg) {
                Ok(result) => {
                    if let Some(docs) = result.get("documents").and_then(|d| d.as_array()) {
                        if docs.is_empty() {
                            println!("{}", "⚠ No documents found".yellow());
                        } else {
                            println!("{}", format!("✓ Found {} document(s):", docs.len()).green());
                            for (i, doc) in docs.iter().enumerate() {
                                println!("\n{}", format!("[{}]", i + 1).bold());
                                println!("{}", serde_json::to_string_pretty(doc)?.cyan());
                            }
                        }
                    } else {
                        println!("{}", "⚠ No documents found".yellow());
                    }
                }
                Err(e) => println!("{}", format!("✗ Error: {}", e).red()),
            }
        }
        "update" => {
            if client.current_collection.is_none() {
                println!("{}", "✗ No collection selected. Use 'use <collection>' first.".red());
                return Ok(false);
            }
            if parts.len() < 3 {
                println!("{}", "✗ Document ID and JSON data required".red());
                println!("{}", "Usage: update <doc_id> <json>".blue());
                return Ok(false);
            }

            let doc_id = parts[1];
            let json_str = line.split_whitespace().skip(2).collect::<Vec<&str>>().join(" ");

            if json_str.is_empty() {
                println!("{}", "✗ JSON data required".red());
                return Ok(false);
            }

            let data: Value = serde_json::from_str(&json_str)?;
            let msg = serde_json::json!({
                "collection": client.current_collection,
                "document_id": doc_id,
                "data": data
            });

            match client.send_message(MSG_UPDATE, &msg) {
                Ok(result) => {
                    println!("{}", format!("✓ Document updated: {}", doc_id).green());
                    println!("{}", serde_json::to_string_pretty(&result)?.cyan());
                }
                Err(e) => println!("{}", format!("✗ Error: {}", e).red()),
            }
        }
        "delete" => {
            if client.current_collection.is_none() {
                println!("{}", "✗ No collection selected. Use 'use <collection>' first.".red());
                return Ok(false);
            }
            if parts.len() < 2 {
                println!("{}", "✗ Document ID required".red());
                println!("{}", "Usage: delete <doc_id>".blue());
                return Ok(false);
            }

            let doc_id = parts[1];
            let msg = serde_json::json!({
                "collection": client.current_collection,
                "document_id": doc_id
            });

            match client.send_message(MSG_DELETE, &msg) {
                Ok(_) => {
                    println!("{}", format!("✓ Document deleted: {}", doc_id).green());
                }
                Err(e) => println!("{}", format!("✗ Error: {}", e).red()),
            }
        }
        "count" => {
            if client.current_collection.is_none() {
                println!("{}", "✗ No collection selected. Use 'use <collection>' first.".red());
                return Ok(false);
            }

            let json_str = line.trim_start_matches("count").trim();
            let filters: Value = if json_str.is_empty() {
                serde_json::json!({})
            } else {
                serde_json::from_str(json_str)?
            };

            // Use QUERY message with limit=0 to get count without fetching all documents
            let msg = serde_json::json!({
                "collection": client.current_collection,
                "filters": filters,
                "limit": 0
            });

            match client.send_message(MSG_QUERY, &msg) {
                Ok(result) => {
                    if let Some(count) = result.get("count").and_then(|c| c.as_u64()) {
                        println!("{}", format!("✓ Document count: {}", count).green());
                    } else {
                        println!("{}", "✓ Count: 0".green());
                    }
                }
                Err(e) => println!("{}", format!("✗ Error: {}", e).red()),
            }
        }
        "vector_search" => {
            if client.current_collection.is_none() {
                println!("{}", "✗ No collection selected. Use 'use <collection>' first.".red());
                return Ok(false);
            }

            let args = line.trim_start_matches("vector_search").trim();
            if args.is_empty() {
                println!("{}", "✗ Vector required".red());
                println!("{}", "Usage: vector_search [0.1, 0.2, 0.3] [limit] [dimensions]".blue());
                return Ok(false);
            }

            // Parse vector
            let vector_end = args.find(']').unwrap_or(args.len()) + 1;
            let vector_str = &args[..vector_end];
            let vector: Vec<f64> = serde_json::from_str(vector_str)?;

            let rest: Vec<&str> = args[vector_end..].split_whitespace().collect();
            let limit: usize = rest.get(0).and_then(|s| s.parse().ok()).unwrap_or(10);
            let dimensions: usize = rest.get(1).and_then(|s| s.parse().ok()).unwrap_or(vector.len());

            let msg = serde_json::json!({
                "collection": client.current_collection,
                "vector": vector,
                "limit": limit,
                "dimensions": dimensions
            });

            match client.send_message(MSG_VECTOR_SEARCH, &msg) {
                Ok(result) => {
                    if let Some(results) = result.get("results").and_then(|r| r.as_array()) {
                        if results.is_empty() {
                            println!("{}", "⚠ No similar documents found".yellow());
                        } else {
                            println!("{}", format!("✓ Found {} similar document(s):", results.len()).green());
                            for (i, res) in results.iter().enumerate() {
                                let similarity = res.get("similarity")
                                    .and_then(|s| s.as_f64())
                                    .unwrap_or(0.0) * 100.0;
                                println!("\n{}", format!("[{}] {:.2}% match", i + 1, similarity).bold());
                                if let Some(doc) = res.get("document") {
                                    println!("{}", serde_json::to_string_pretty(doc)?.cyan());
                                }
                            }
                        }
                    } else {
                        println!("{}", "⚠ No similar documents found".yellow());
                    }
                }
                Err(e) => println!("{}", format!("✗ Error: {}", e).red()),
            }
        }
        _ => {
            println!("{}", format!("✗ Unknown command: {}", cmd).red());
            println!("{}", "Type 'help' to see available commands".blue());
        }
    }

    Ok(false)
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Get password
    let password = if args.password {
        rpassword::prompt_password("Password: ")?
    } else {
        "nexadb123".to_string()
    };

    print_banner();

    // Connect to NexaDB
    let mut client = match NexaClient::connect(&args.host, args.port, &args.username, &password) {
        Ok(c) => c,
        Err(e) => {
            println!("{}", format!("✗ Connection failed: {}", e).red());
            println!("{}", "Make sure NexaDB server is running:".blue());
            println!("{}", "  $ nexadb start".blue());
            std::process::exit(1);
        }
    };

    // Start REPL
    let mut rl = DefaultEditor::new()?;
    let history_file = dirs::home_dir()
        .map(|h| h.join(".nexadb_history"))
        .unwrap_or_else(|| std::path::PathBuf::from(".nexadb_history"));

    let _ = rl.load_history(&history_file);

    loop {
        let prompt = if let Some(ref col) = client.current_collection {
            format!("nexa({})> ", col).green().bold().to_string()
        } else {
            "nexa> ".green().bold().to_string()
        };

        match rl.readline(&prompt) {
            Ok(line) => {
                let _ = rl.add_history_entry(line.as_str());

                match handle_command(&mut client, &line) {
                    Ok(should_exit) => {
                        if should_exit {
                            break;
                        }
                    }
                    Err(e) => {
                        println!("{}", format!("✗ Error: {}", e).red());
                    }
                }
            }
            Err(ReadlineError::Interrupted) => {
                println!("{}", "Use 'exit' to quit".yellow());
            }
            Err(ReadlineError::Eof) => {
                println!();
                println!("{}", "Goodbye! 👋".blue());
                break;
            }
            Err(err) => {
                println!("{}", format!("Error: {:?}", err).red());
                break;
            }
        }
    }

    let _ = rl.save_history(&history_file);

    Ok(())
}
