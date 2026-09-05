use rust_error_handling_001::{parse_server_config, ServerConfig};

#[test]
fn test_baseline_valid_config() {
    let raw = "host = 127.0.0.1\nport = 8080";
    let cfg = parse_server_config(raw).expect("Expected valid config to parse successfully");
    assert_eq!(
        cfg,
        ServerConfig {
            host: "127.0.0.1".to_string(),
            port: 8080
        }
    );
}
