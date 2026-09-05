# Configuration Loader: Resilient JSON Parsing

### Context
In `src/env_loader.js`, `loadConfig()` parses raw configuration files. Real-world configuration files often include single-line comments (`// ...`) or trailing commas (`{ "key": 1, }`), which cause `JSON.parse` to crash.

### Objective
1. Pre-process incoming configuration text to strip single-line comments (`//`).
2. Remove trailing commas immediately preceding closing braces `}` or brackets `]`.
3. Safely parse JSON and provide defaults: `port: parsed.port ?? 3000`, `debug: parsed.debug ?? false`.
4. If parsing fails on malformed input, fallback to default `{ port: 3000, debug: false }`.

### Style
Robust parsing logic utilizing standard regular expressions.

### Tone
Resilient, fault-tolerant engineering.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Update `src/env_loader.js` without requiring external npm packages.
