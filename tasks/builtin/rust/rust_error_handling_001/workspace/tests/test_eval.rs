use rust_error_handling_001::{parse_server_config, ConfigError};

#[test]
fn test_eval_empty_payload() {
    let res = parse_server_config("   ");
    assert_eq!(res, Err(ConfigError::EmptyPayload));
}

#[test]
fn test_eval_invalid_port_range() {
    let res = parse_server_config("host = 0.0.0.0\nport = 80");
    assert_eq!(res, Err(ConfigError::InvalidPort(80)));
}

#[test]
fn test_eval_missing_host() {
    let res = parse_server_config("port = 9000");
    assert_eq!(res, Err(ConfigError::MissingKey("host".to_string())));
}
