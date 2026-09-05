"""Script to format all benchmark prompts using the COSTAR prompt engineering framework."""

from pathlib import Path

PROMPTS = {
    "tasks/python/python_bugfix_001/prompt.md": """# Bug Fix: Token Bucket Rate Limiter Refill

### Context
In `src/rate_limiter.py`, the `TokenBucket` class implements rate-limiting. When tokens are consumed and time passes, `refill()` attempts to compute the elapsed duration. However, the time delta calculation is inverted (`self.last_refill - now`), producing negative or zero elapsed time and halting token replenishment.

### Objective
1. Correct the elapsed time computation to `now - self.last_refill`.
2. Cap `self.tokens` at `self.capacity`.
3. Update `self.last_refill` to `now`.

### Style
Idiomatic Python 3, adhering to existing class attributes, type annotations, and minimal code churn.

### Tone
Technical, unambiguous, and focused on defect resolution.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Apply necessary edits directly to `src/rate_limiter.py`. Do not create unnecessary artifacts, logs, or modify tests. All existing and evaluation tests must pass cleanly.
""",

    "tasks/python/python_perf_001/prompt.md": """# Performance Optimization: Event Deduplication

### Context
In `src/deduplicator.py`, the `deduplicate_events()` function processes streaming event batches. It currently verifies membership using `if event['id'] not in [e['id'] for e in unique_events]`, which scans the output list on every iteration (O(N^2) complexity). Under heavy traffic, this causes timeouts.

### Objective
1. Optimize `deduplicate_events(events: list[dict]) -> list[dict]` to run in O(N) linear time.
2. Preserve the first-occurrence order of each distinct event ID.
3. Keep pure Python implementation without introducing external dependencies.

### Style
Idiomatic Python using standard library data structures (e.g., `set`).

### Tone
Direct, performance-critical, and precise.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Update `src/deduplicator.py`. Ensure minimal memory overhead and zero regression on order preservation.
""",

    "tasks/python/python_async_001/prompt.md": """# Async Concurrency: Batch Pipeline Error Isolation

### Context
In `src/pipeline.py`, `execute_batch()` dispatches concurrent asynchronous operations using standard `asyncio.gather(*tasks)`. A single failure abruptly aborts the entire gather call, discarding results of successfully completed concurrent tasks.

### Objective
1. Update `execute_batch(coros: list)` in `src/pipeline.py` using `asyncio.gather(*coros, return_exceptions=True)`.
2. Partition the results into two distinct lists:
   - `successes`: values that completed without exceptions
   - `failures`: exception instances encountered
3. Return a dictionary `{"successes": successes, "failures": failures}`.

### Style
Modern asynchronous Python 3 with clean list partitioning.

### Tone
Technical, concurrent-systems focused.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Modify `src/pipeline.py` to isolate coroutine failures without leaving lingering unawaited tasks.
""",

    "tasks/typescript/typescript_api_001/prompt.md": """# API Serializer Bug: Handle Null Values and Arrays

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
""",

    "tasks/typescript/typescript_refactor_001/prompt.md": """# Refactoring: Extract Retry Strategy Module

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
""",

    "tasks/typescript/typescript_dependency_001/prompt.md": """# Configuration Loader: Resilient JSON Parsing

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
""",

    "tasks/go/go_concurrency_001/prompt.md": """# Go Concurrency: Fix Read-After-Write Race Condition in Sharded Cache

### Context
In `src/cache.go`, the `ShardedCache` implementation stores key-value pairs across bucket shards. It currently performs unsafe concurrent map access without synchronization, triggering race detector panics under concurrent read/write loads.

### Objective
1. Add a `sync.RWMutex` (or `sync.Mutex`) to each bucket shard in `src/cache.go`.
2. Protect all reads (`Get`) with a read lock (`RLock` / `RUnlock`).
3. Protect all writes (`Set`) with a write lock (`Lock` / `Unlock`).

### Style
Idiomatic Go concurrency patterns using deferred lock releases (`defer b.mu.RUnlock()`).

### Tone
Thread-safe, strict concurrency safety.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Modify `src/cache.go` to eliminate data races under concurrent workloads.
""",

    "tasks/go/go_error_handling_001/prompt.md": """# Go Error Handling: Implement Custom API Error with Unwrap and Sentinels

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
""",

    "tasks/go/go_perf_001/prompt.md": """# Go Performance: Optimize Stream Accumulator Buffer Reallocation

### Context
In `src/buffer.go`, `StreamAccumulator` accumulates byte chunks. It currently allocates fresh slices on every `Reset()` call and appends chunks naively, causing heavy GC pressure and heap fragmentation.

### Objective
1. Refactor `StreamAccumulator` in `src/buffer.go` to use `bytes.Buffer`.
2. Implement `Write(chunk []byte) (int, error)` streaming directly into the buffer.
3. Implement `Bytes() []byte` returning `b.buf.Bytes()`.
4. Implement `Reset()` invoking `b.buf.Reset()` to clear contents without discarding underlying allocated capacity.

### Style
Idiomatic Go memory-efficient I/O patterns.

### Tone
Performance-oriented, memory-allocation sensitive.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Modify `src/buffer.go` to minimize heap allocations and maximize throughput.
""",

    "tasks/java/java_dependency_001/prompt.md": """# Maven Dependency Conflict: Exclude Transitive slf4j-log4j12

### Context
In `pom.xml`, the dependency `com.example.legacy:legacy-connector` pulls in a transitive logging binding `org.slf4j:slf4j-log4j12`, creating a classpath conflict with modern `ch.qos.logback:logback-classic`.

### Objective
1. In `pom.xml`, add an `<exclusions>` element to the `legacy-connector` dependency.
2. Exclude group `org.slf4j` and artifact `slf4j-log4j12`.
3. Preserve both `legacy-connector` and `logback-classic` dependencies intact.

### Style
Standard Maven XML schema format with proper indentation.

### Tone
Precise, configuration and build-system oriented.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Update `pom.xml` with the appropriate exclusion declaration.
""",

    "tasks/java/java_refactor_001/prompt.md": """# Java Refactoring: Implement Builder Pattern on UserAccount

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
""",

    "tasks/java/java_multi_module_001/prompt.md": """# Java Multi-Module Contract: Synchronize PaymentRequest Call

### Context
In this multi-module repository, module `payment-api` updated `PaymentRequest` constructor to `(String orderId, double amount, String token)` with getter `getToken()`. Module `order-service` in `order-service/src/OrderService.java` still uses obsolete arguments and deprecated getter `getPaymentToken()`.

### Objective
1. Update `processOrder()` in `order-service/src/OrderService.java` to invoke `new PaymentRequest(orderId, amount, token)`.
2. Update `process()` to call `req.getToken()` instead of `req.getPaymentToken()`.
3. Do not modify `payment-api`.

### Style
Idiomatic Java cross-module communication adhering to published interface contracts.

### Tone
Contract-driven, multi-module dependency alignment.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Update `order-service/src/OrderService.java` to restore compilation and compatibility.
"""
}


def apply_prompts():
    for rel_path, content in PROMPTS.items():
        target = Path(rel_path)
        if target.exists():
            target.write_text(content.strip() + "\n", encoding="utf-8")
            print(f"Applied COSTAR prompt: {rel_path}")


if __name__ == "__main__":
    apply_prompts()
