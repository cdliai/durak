fn main() {
    // Capture the Rust version at build time
    let rustc_version = std::env::var("RUSTC_VERSION")
        .or_else(|_| rustc_version())
        .unwrap_or_else(|_| "unknown".to_string());
    
    println!("cargo:rustc-env=RUSTC_VERSION={}", rustc_version);
    println!("cargo:rerun-if-changed=build.rs");
}

fn rustc_version() -> Result<String, Box<dyn std::error::Error>> {
    let output = std::process::Command::new("rustc")
        .arg("--version")
        .output()?;
    
    let version_str = String::from_utf8(output.stdout)?;
    
    // Extract just the version number (e.g., "1.92.0" from "rustc 1.92.0 (...")
    if let Some(version) = version_str.split_whitespace().nth(1) {
        Ok(version.to_string())
    } else {
        Ok(version_str.trim().to_string())
    }
}
