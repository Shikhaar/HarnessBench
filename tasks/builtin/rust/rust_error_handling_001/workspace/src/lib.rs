use std::error::Error;
use std::fmt;

#[derive(Debug, PartialEq, Eq)]
pub enum ConfigError {
    MissingKey(String),
    InvalidPort(u16),
    EmptyPayload,
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ConfigError::MissingKey(key) => write!(f, "Missing required key: {}", key),
            ConfigError::InvalidPort(port) => write!(f, "Invalid port number: {}", port),
            ConfigError::EmptyPayload => write!(f, "Configuration payload is empty"),
        }
    }
}

impl Error for ConfigError {}

#[derive(Debug, PartialEq, Eq)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
}

pub fn parse_server_config(raw: &str) -> Result<ServerConfig, ConfigError> {
    if raw.trim().is_empty() {
        // BUG: Inverted/wrong variant returned on empty payload
        return Err(ConfigError::MissingKey("payload".to_string()));
    }

    let mut host = None;
    let mut port = None;

    for line in raw.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        if let Some((k, v)) = trimmed.split_once('=') {
            let key = k.trim();
            let val = v.trim();
            if key == "host" {
                host = Some(val.to_string());
            } else if key == "port" {
                if let Ok(p) = val.parse::<u16>() {
                    // BUG: Does not check p >= 1024, permits privileged/invalid ports
                    port = Some(p);
                }
            }
        }
    }

    match (host, port) {
        (Some(h), Some(p)) => Ok(ServerConfig { host: h, port: p }),
        (None, _) => Err(ConfigError::MissingKey("host".to_string())),
        (_, None) => Err(ConfigError::MissingKey("port".to_string())),
    }
}
