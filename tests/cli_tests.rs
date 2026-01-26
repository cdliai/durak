/// Integration tests for Durak CLI
/// 
/// Tests cover:
/// - Basic tokenization and normalization
/// - Turkish character handling (İ/ı, I/i)
/// - JSON output format
/// - Stdin input processing
/// - Edge cases and error handling

use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn test_cli_version() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.arg("version");
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("Durak v"));
}

#[test]
fn test_cli_version_json() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["version", "--json"]);
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("durak_version"))
        .stdout(predicate::str::contains("package_name"));
}

#[test]
fn test_tokenize_simple() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize", "Merhaba dünya!"]);
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("Merhaba"))
        .stdout(predicate::str::contains("dünya"))
        .stdout(predicate::str::contains("!"));
}

#[test]
fn test_tokenize_turkish_apostrophe() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize", "İstanbul'a gittik."]);
    
    let output = cmd.assert().success();
    let stdout = std::str::from_utf8(&output.get_output().stdout).unwrap();
    
    // Should preserve apostrophe in İstanbul'a
    assert!(stdout.contains("İstanbul'a") || stdout.lines().any(|l| l == "İstanbul'a"));
    assert!(stdout.contains("gittik") || stdout.lines().any(|l| l == "gittik"));
}

#[test]
fn test_tokenize_json_output() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize", "--json", "Test metni"]);
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("\"tokens\""))
        .stdout(predicate::str::contains("["))
        .stdout(predicate::str::contains("]"));
}

#[test]
fn test_tokenize_with_offsets() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize", "--offsets", "Merhaba dünya"]);
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("Merhaba"))
        .stdout(predicate::str::contains("\t")); // Tab-separated offsets
}

#[test]
fn test_tokenize_with_offsets_json() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize", "--offsets", "--json", "Test"]);
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("\"start\""))
        .stdout(predicate::str::contains("\"end\""))
        .stdout(predicate::str::contains("\"text\""));
}

#[test]
fn test_normalize_basic() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["normalize", "MERHABA"]);
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("merhaba"));
}

#[test]
fn test_normalize_turkish_i() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["normalize", "İSTANBUL"]);
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("istanbul")); // İ → i
}

#[test]
fn test_normalize_turkish_dotless_i() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["normalize", "IŞIK"]);
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("ışık")); // I → ı
}

#[test]
fn test_normalize_json_output() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["normalize", "--json", "TÜRKÇE"]);
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("\"original\""))
        .stdout(predicate::str::contains("\"normalized\""))
        .stdout(predicate::str::contains("türkçe"));
}

#[test]
fn test_tokenize_empty_input() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize", ""]);
    
    // Should handle empty input gracefully
    cmd.assert().success();
}

#[test]
fn test_normalize_mixed_turkish_chars() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["normalize", "İzmir'de IĞDIR'a GİDİYORUM"]);
    
    let output = cmd.assert().success();
    let stdout = std::str::from_utf8(&output.get_output().stdout).unwrap();
    
    // İ → i, I → ı, others lowercase
    assert!(stdout.contains("izmir"));
    assert!(stdout.contains("ığdır") || stdout.contains("ığdır"));
    assert!(stdout.contains("gidiyorum"));
}

#[test]
fn test_tokenize_complex_sentence() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize", "Ankara'da 2023 yılında çok güzel bir konferans vardı."]);
    
    let output = cmd.assert().success();
    let stdout = std::str::from_utf8(&output.get_output().stdout).unwrap();
    
    // Should preserve apostrophes and handle numbers
    assert!(stdout.contains("Ankara'da") || stdout.lines().any(|l| l == "Ankara'da"));
    assert!(stdout.contains("2023") || stdout.lines().any(|l| l == "2023"));
    assert!(stdout.contains("konferans") || stdout.lines().any(|l| l == "konferans"));
}

#[test]
fn test_help_command() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.arg("--help");
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("Durak"))
        .stdout(predicate::str::contains("tokenize"))
        .stdout(predicate::str::contains("normalize"));
}

#[test]
fn test_tokenize_stdin() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize"]);
    cmd.write_stdin("Merhaba dünya!");
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("Merhaba"))
        .stdout(predicate::str::contains("dünya"));
}

#[test]
fn test_normalize_stdin() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["normalize"]);
    cmd.write_stdin("İSTANBUL");
    
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("istanbul"));
}

#[test]
fn test_tokenize_url_preservation() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize", "Check https://example.com for more info"]);
    
    let output = cmd.assert().success();
    let stdout = std::str::from_utf8(&output.get_output().stdout).unwrap();
    
    // URLs should be tokenized as single tokens
    assert!(stdout.contains("https://example.com") || stdout.lines().any(|l| l.contains("https://example.com")));
}

#[test]
fn test_tokenize_emoticon_preservation() {
    let mut cmd = Command::cargo_bin("durak").unwrap();
    cmd.args(&["tokenize", "Merhaba :) nasılsın?"]);
    
    let output = cmd.assert().success();
    let stdout = std::str::from_utf8(&output.get_output().stdout).unwrap();
    
    // Emoticons should be preserved
    assert!(stdout.contains(":)") || stdout.lines().any(|l| l == ":)"));
}
