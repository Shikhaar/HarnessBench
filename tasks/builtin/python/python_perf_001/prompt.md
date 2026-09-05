# Performance Optimization: Event Deduplication

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
