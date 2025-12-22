//! License Generator Tool
//!
//! Usage: pfv-license-generate --licensee "Dr. Pablo" --email "pablo@clinic.com" \
//!        --type single --domains "petfriendlyvet.com" --days 365

use chrono::{Duration, Utc};
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use std::fs;

#[derive(Debug, Serialize, Deserialize)]
pub struct LicenseInfo {
    pub licensee: String,
    pub email: String,
    pub license_type: String,
    pub issued_at: String,
    pub expires_at: String,
    pub domains: Vec<String>,
    pub features: Vec<String>,
    pub max_users: Option<u32>,
}

#[derive(Debug, Serialize)]
struct LicenseFile {
    version: u8,
    payload: String,
    signature: String,
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    // Simple arg parsing
    let licensee = get_arg(&args, "--licensee").unwrap_or("Demo User".to_string());
    let email = get_arg(&args, "--email").unwrap_or("demo@example.com".to_string());
    let license_type = get_arg(&args, "--type").unwrap_or("trial".to_string());
    let domains_str = get_arg(&args, "--domains").unwrap_or("localhost".to_string());
    let days: i64 = get_arg(&args, "--days")
        .and_then(|s| s.parse().ok())
        .unwrap_or(30);
    let output = get_arg(&args, "--output").unwrap_or("license.key".to_string());

    let domains: Vec<String> = domains_str.split(',').map(|s| s.trim().to_string()).collect();

    let now = Utc::now();
    let expires = now + Duration::days(days);

    let info = LicenseInfo {
        licensee,
        email,
        license_type: license_type.clone(),
        issued_at: now.to_rfc3339(),
        expires_at: expires.to_rfc3339(),
        domains,
        features: get_features_for_type(&license_type),
        max_users: get_max_users_for_type(&license_type),
    };

    // Serialize payload
    let payload_json = serde_json::to_vec(&info).unwrap();
    let payload_b64 = base64::Engine::encode(
        &base64::engine::general_purpose::STANDARD,
        &payload_json
    );

    // Generate signature
    let signature = compute_signature(&payload_json);

    let license_file = LicenseFile {
        version: 1,
        payload: payload_b64,
        signature,
    };

    let output_json = serde_json::to_string_pretty(&license_file).unwrap();

    fs::write(&output, &output_json).expect("Failed to write license file");

    println!("License generated: {}", output);
    println!();
    println!("License Info:");
    println!("  Licensee: {}", info.licensee);
    println!("  Email: {}", info.email);
    println!("  Type: {}", info.license_type);
    println!("  Expires: {}", info.expires_at);
    println!("  Domains: {:?}", info.domains);
    println!("  Features: {:?}", info.features);
}

fn get_arg(args: &[String], flag: &str) -> Option<String> {
    args.iter()
        .position(|a| a == flag)
        .and_then(|i| args.get(i + 1))
        .map(|s| s.clone())
}

fn compute_signature(payload: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(payload);
    hasher.update(b"pfv-license-salt-2025");
    hex::encode(hasher.finalize())
}

fn get_features_for_type(license_type: &str) -> Vec<String> {
    match license_type {
        "trial" => vec!["basic".to_string()],
        "single" => vec!["basic".to_string(), "appointments".to_string(), "ecommerce".to_string()],
        "multi" => vec!["basic".to_string(), "appointments".to_string(), "ecommerce".to_string(), "multi_location".to_string()],
        "enterprise" => vec!["all".to_string()],
        "developer" => vec!["all".to_string(), "dev_mode".to_string()],
        _ => vec!["basic".to_string()],
    }
}

fn get_max_users_for_type(license_type: &str) -> Option<u32> {
    match license_type {
        "trial" => Some(1),
        "single" => Some(5),
        "multi" => Some(20),
        "enterprise" => None, // Unlimited
        "developer" => Some(2),
        _ => Some(1),
    }
}
