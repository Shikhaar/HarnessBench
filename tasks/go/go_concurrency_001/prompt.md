# Go Concurrency: Fix Read-After-Write Race Condition in Sharded Cache

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
