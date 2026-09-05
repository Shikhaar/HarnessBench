# Refactoring: Extract Retry Strategy Module

### Context
In `src/dispatcher.js`, action dispatching and exponential/linear retry logic are tightly coupled in the same class, complicating testing and reusability.

### Objective
1. Create a dedicated module `src/retry.js` exporting `executeWithRetry(fn, { maxRetries = 3, delayMs = 10 } = {})`.
2. Ensure `executeWithRetry` catches failures and retries up to `maxRetries` times before rethrowing the final error.
3. Refactor `Dispatcher.dispatch(action)` in `src/dispatcher.js` to delegate invocation to `executeWithRetry`.

### Style
Modular CommonJS/ES module design adhering to the Single Responsibility Principle.

### Tone
Architectural, modular, and refactoring-focused.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Add `src/retry.js` and update `src/dispatcher.js` maintaining all existing dispatch contracts.
