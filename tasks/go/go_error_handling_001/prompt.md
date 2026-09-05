# Go Error Handling: Implement Custom API Error with Unwrap and Sentinels

### Context
In `src/errors.go`, errors are returned as plain untyped strings, preventing callers from inspecting root causes or using standard `errors.Is()` checks.

### Objective
1. Define sentinel error variables:
   - `var ErrNotFound = errors.New("resource not found")`
   - `var ErrUnauthorized = errors.New("unauthorized")`
2. Implement struct `ApiError` with fields: `Code int`, `Message string`, `Err error`.
3. Implement `Error() string` formatting code, message, and wrapped error when present.
4. Implement `Unwrap() error` returning `e.Err` to satisfy Go 1.13+ error wrapping.

### Style
Idiomatic Go error handling following standard library conventions.

### Tone
Definitive, API-contract driven.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Update `src/errors.go` to adhere to Go standard error unwrap protocols.
