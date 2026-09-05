# Java Refactoring: Implement Builder Pattern on UserAccount

### Context
In `src/UserAccount.java`, user accounts are constructed via telescoping constructors with multiple positional parameters, which is error-prone and brittle.

### Objective
1. Keep fields `username`, `email`, `role`, and `enabled`.
2. Create a public static inner class `Builder` with fluent methods: `username()`, `email()`, `role()`, `enabled()`.
3. In `Builder.build()`, validate that `username` and `email` are non-null and not blank (throw `IllegalArgumentException` otherwise), and construct the `UserAccount`.
4. Expose `public static Builder builder()` on `UserAccount`.

### Style
Standard Java design pattern conventions (Gang of Four / Effective Java).

### Tone
Object-oriented, clean-code architecture.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Refactor `src/UserAccount.java` providing fluent builder mechanics.
