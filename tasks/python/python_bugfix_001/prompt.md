# Bug Fix: Token Bucket Rate Limiter Refill

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
