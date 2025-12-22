//! South City Computer License Validator
//!
//! Reusable license validator for all South City Computer software products.
//! Called by Django/Python applications at startup to verify valid commercial license.
//!
//! This component is designed to be used across multiple projects - not project-specific.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use std::fs;
use std::process::exit;

/// License information returned on successful validation
#[derive(Debug, Serialize, Deserialize)]
pub struct LicenseInfo {
    pub licensee: String,
    pub email: String,
    pub license_type: LicenseType,
    pub issued_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub domains: Vec<String>,
    pub features: Vec<String>,
    pub max_users: Option<u32>,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum LicenseType {
    Trial,
    Single,      // Single clinic
    Multi,       // Multiple locations
    Enterprise,  // Unlimited
    Developer,   // For development/testing
}

/// License file structure (encrypted in production)
#[derive(Debug, Deserialize)]
struct LicenseFile {
    version: u8,
    payload: String,    // Base64 encoded, signed payload
    signature: String,  // Ed25519 signature
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    let license_path = args.get(1)
        .map(|s| s.as_str())
        .unwrap_or("license.key");

    let check_domain = args.get(2).map(|s| s.as_str());

    match validate_license(license_path, check_domain) {
        Ok(info) => {
            // Output JSON for Django to parse
            println!("{}", serde_json::to_string_pretty(&info).unwrap());
            exit(0);
        }
        Err(e) => {
            eprintln!("LICENSE ERROR: {}", e);
            eprintln!();
            eprintln!("This software requires a valid commercial license.");
            eprintln!("Contact: nestor@southcitycomputer.com");
            eprintln!("Web: https://southcitycomputer.com");
            exit(1);
        }
    }
}

fn validate_license(path: &str, check_domain: Option<&str>) -> Result<LicenseInfo, String> {
    // Read license file
    let content = fs::read_to_string(path)
        .map_err(|e| format!("Cannot read license file '{}': {}", path, e))?;

    // Parse license file
    let license_file: LicenseFile = serde_json::from_str(&content)
        .map_err(|e| format!("Invalid license file format: {}", e))?;

    // Check version
    if license_file.version != 1 {
        return Err(format!("Unsupported license version: {}", license_file.version));
    }

    // Decode payload
    let payload_bytes = base64::Engine::decode(
        &base64::engine::general_purpose::STANDARD,
        &license_file.payload
    ).map_err(|e| format!("Invalid license payload: {}", e))?;

    // Verify signature (simplified - in production use Ed25519)
    let expected_sig = compute_signature(&payload_bytes);
    if license_file.signature != expected_sig {
        return Err("Invalid license signature".to_string());
    }

    // Parse license info
    let info: LicenseInfo = serde_json::from_slice(&payload_bytes)
        .map_err(|e| format!("Invalid license data: {}", e))?;

    // Check expiration
    if info.expires_at < Utc::now() {
        return Err(format!(
            "License expired on {}",
            info.expires_at.format("%Y-%m-%d")
        ));
    }

    // Check domain if provided
    if let Some(domain) = check_domain {
        if !info.domains.is_empty() && !info.domains.contains(&domain.to_string()) {
            return Err(format!(
                "License not valid for domain '{}'. Licensed domains: {:?}",
                domain, info.domains
            ));
        }
    }

    Ok(info)
}

/// Compute signature for verification
/// In production, this would verify against a public key
fn compute_signature(payload: &[u8]) -> String {
    // This is a simplified signature check
    // In production, use Ed25519 with embedded public key
    let mut hasher = Sha256::new();
    hasher.update(payload);
    hasher.update(b"scc-license-salt-2025"); // Secret salt
    hex::encode(hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_license_type_serialization() {
        let license_type = LicenseType::Single;
        let json = serde_json::to_string(&license_type).unwrap();
        assert_eq!(json, "\"single\"");
    }
}
