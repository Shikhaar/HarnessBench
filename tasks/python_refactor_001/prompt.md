# Refactoring Task: Extract Configuration Module

Currently, `src/client.py` handles API client logic and raw configuration fields directly.

### Goal:
Refactor the codebase to extract a formal `ClientConfig` class into `src/config.py` and update `src/client.py` to use it.

### Specifications:
1. In `src/config.py`, create a class `ClientConfig`:
   - `__init__(self, api_key: str, base_url: str = "https://api.example.com", timeout: int = 30)`
   - Validate that `api_key` is a non-empty string. If empty or None, raise `ValueError("api_key cannot be empty")`.
   - Validate that `base_url` starts with `http://` or `https://`. If not, raise `ValueError("Invalid base_url scheme")`.
2. In `src/client.py`, update `ApiClient`:
   - `__init__(self, api_key: str | None = None, base_url: str = "https://api.example.com", timeout: int = 30, config: ClientConfig | None = None)`
   - If `config` is passed, use it. Otherwise, instantiate `self.config = ClientConfig(api_key=api_key, base_url=base_url, timeout=timeout)`.
   - Provide `@property` for `api_key`, `base_url`, and `timeout` that delegate to `self.config`.
   - Implement `get_endpoint(self, path: str) -> str` that joins `self.base_url.rstrip("/")` with `path.lstrip("/")`.
3. Preserve backward compatibility for existing `ApiClient("my-key")` usage.
