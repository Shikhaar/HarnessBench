# API Serializer Bug: Handle Null Values and Arrays

### Context
In `src/serializer.js`, `serializeApiResponse()` recursively transforms payload keys from `snake_case` to `camelCase`. The routine crashes on `null` attributes (`TypeError: Cannot read properties of null`) and does not traverse array elements.

### Objective
1. Ensure `serializeApiResponse(data)` gracefully returns `data` untouched if it is `null` or non-object primitive.
2. Recursively serialize every item if `data` is an Array.
3. Recursively serialize key-value pairs if `data` is a plain Object.

### Style
Clean, modern JavaScript / TypeScript patterns with zero third-party dependencies.

### Tone
Defensive, precise, and edge-case aware.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Edit `src/serializer.js` ensuring correct casing conversions while preserving data integrity.
