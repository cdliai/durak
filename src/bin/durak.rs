/// Durak CLI - Turkish NLP Toolkit Command-Line Interface
/// 
/// Standalone CLI for Turkish text processing operations:
/// - Tokenization with Turkish morphology support
/// - Unicode-aware normalization (İ/ı, I/i handling)
/// - JSON output for scripting and pipelines
/// - Stdin support for Unix-style text processing
///
/// Examples:
///   durak tokenize "Merhaba dünya!"
///   durak normalize "İSTANBUL'a gittik"
///   echo "Ankara'da kaldım" | durak tokenize
///   durak tokenize --json "Test" > output.json

use clap::{Parser, Subcommand};
use serde_json::json;
use std::io::{self, Read};

// Import core functionality (shared with Python bindings)
#[path = "../core.rs"]
mod core;

#[derive(Parser)]
#[command(name = "durak")]
#[command(version = env!("CARGO_PKG_VERSION"))]
#[command(about = "Durak - Turkish NLP Toolkit CLI", long_about = None)]
#[command(author = "Durak Team")]
struct Cli {
    /// Output in JSON format
    #[arg(short, long, global = true)]
    json: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Tokenize Turkish text with morphology awareness
    /// 
    /// Preserves Turkish-specific features:
    /// - Apostrophes (İstanbul'a, Ankara'da)
    /// - Clitics and suffixes
    /// - Numbers with Turkish decimal separators
    /// - URLs and emoticons
    ///
    /// Examples:
    ///   durak tokenize "Merhaba dünya!"
    ///   echo "İstanbul'a gittim" | durak tokenize
    ///   durak tokenize --json "Test metni" > tokens.json
    Tokenize {
        /// Text to tokenize (omit to read from stdin)
        text: Option<String>,

        /// Include character offsets in output
        #[arg(short, long)]
        offsets: bool,
    },

    /// Normalize Turkish text (Unicode-aware lowercasing)
    /// 
    /// Correctly handles Turkish-specific characters:
    /// - İ → i (Turkish dotted I)
    /// - I → ı (Turkish dotless i)
    /// - Other characters: standard Unicode lowercasing
    ///
    /// Examples:
    ///   durak normalize "İSTANBUL"  # → "istanbul"
    ///   durak normalize "TÜRKÇE"    # → "türkçe"
    ///   echo "İZMİR" | durak normalize
    Normalize {
        /// Text to normalize (omit to read from stdin)
        text: Option<String>,
    },

    /// Show version and build information
    /// 
    /// Displays:
    /// - Durak version
    /// - Package name
    /// - Build date (if available)
    ///
    /// Example:
    ///   durak version --json
    Version,
}

/// Read text from stdin if available
fn read_stdin() -> io::Result<String> {
    if atty::is(atty::Stream::Stdin) {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "No text provided. Provide text as argument or pipe via stdin.",
        ));
    }

    let mut buffer = String::new();
    io::stdin().read_to_string(&mut buffer)?;
    Ok(buffer.trim_end().to_string())
}

/// Get text from argument or stdin
fn get_text(text_arg: Option<String>) -> Result<String, String> {
    match text_arg {
        Some(text) => Ok(text),
        None => read_stdin().map_err(|e| format!("Failed to read stdin: {}", e)),
    }
}

fn main() {
    let cli = Cli::parse();

    let result: Result<(), String> = match cli.command {
        Commands::Tokenize { text, offsets } => {
            let input = match get_text(text) {
                Ok(t) => t,
                Err(e) => {
                    eprintln!("Error: {}", e);
                    std::process::exit(1);
                }
            };

            if offsets {
                let tokens = core::tokenize_with_offsets(&input);
                if cli.json {
                    let output = json!({
                        "tokens": tokens.iter().map(|(token, start, end)| {
                            json!({
                                "text": token,
                                "start": start,
                                "end": end
                            })
                        }).collect::<Vec<_>>()
                    });
                    println!("{}", serde_json::to_string_pretty(&output).unwrap());
                } else {
                    for (token, start, end) in tokens {
                        println!("{}\t{}\t{}", token, start, end);
                    }
                }
            } else {
                let tokens = core::tokenize(&input);
                if cli.json {
                    let output = json!({ "tokens": tokens });
                    println!("{}", serde_json::to_string_pretty(&output).unwrap());
                } else {
                    for token in tokens {
                        println!("{}", token);
                    }
                }
            }
            Ok(())
        }

        Commands::Normalize { text } => {
            let input = match get_text(text) {
                Ok(t) => t,
                Err(e) => {
                    eprintln!("Error: {}", e);
                    std::process::exit(1);
                }
            };

            let normalized = core::fast_normalize(&input);
            if cli.json {
                let output = json!({
                    "original": input,
                    "normalized": normalized
                });
                println!("{}", serde_json::to_string_pretty(&output).unwrap());
            } else {
                println!("{}", normalized);
            }
            Ok(())
        }

        Commands::Version => {
            let info = core::get_build_info();
            if cli.json {
                println!("{}", serde_json::to_string_pretty(&info).unwrap());
            } else {
                println!("Durak v{}", env!("CARGO_PKG_VERSION"));
                if let Some(build_date) = info.get("build_date") {
                    println!("Build Date: {}", build_date);
                }
                println!("Package: {}", info.get("package_name").unwrap_or(&"unknown".to_string()));
            }
            Ok(())
        }
    };

    if let Err(e) = result {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }
}
