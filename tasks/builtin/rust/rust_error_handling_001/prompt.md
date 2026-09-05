# Rust Error Handling: Robust Server Config Result Propagation

### Context
In `src/lib.rs`, `parse_server_config(raw: &str)` parses simple key-value configuration strings (e.g. `"host=127.0.0.1\nport=8080"`). Currently, it panics on malformed input or returns incorrect error variants instead of propagating well-typed `Result<ServerConfig, ConfigError>`.

### Objective
1. In `src/lib.rs`, ensure `ConfigError` has the following enum variants:
   - `MissingKey(String)`
   - `InvalidPort(u16)`
   - `EmptyPayload`
2. Implement `parse_server_config(raw: &str) -> Result<ServerConfig, ConfigError>`:
   - Return `Err(ConfigError::EmptyPayload)` if the trimmed raw string is empty.
   - Parse lines formatted as `key=value`.
   - If `host` is missing or empty, return `Err(ConfigError::MissingKey("host".to_string()))`.
   - If `port` is missing, return `Err(ConfigError::MissingKey("port".to_string()))`.
   - If `port` is `< 1024` or cannot be parsed as a `u16`, return `Err(ConfigError::InvalidPort(val))`.
   - If valid, return `Ok(ServerConfig { host, port })`.
3. Do not panic or use `unwrap()` on untrusted input.

### Style
Idiomatic Rust standard library error handling implementing `std::fmt::Display` and `std::error::Error` for `ConfigError`.

### Tone
Systems-level, safety-critical, and contract-driven.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Apply necessary modifications directly to `src/lib.rs`. Ensure all unit and evaluation tests pass without regression.
