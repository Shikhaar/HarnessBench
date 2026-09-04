# Bug Fix: Token Bucket Rate Limiter Refill

There is a bug in `src/rate_limiter.py` in the `TokenBucket` class.

When tokens are consumed and time elapses, the `refill()` logic fails to add new tokens back into the bucket because the elapsed time subtraction is inverted (`self.last_refill - now` instead of `now - self.last_refill`).

### Requirements:
1. Fix the calculation in `src/rate_limiter.py` so that `now - self.last_refill` is used to compute elapsed time.
2. Ensure `tokens` is capped at `self.capacity` and never exceeds it.
3. Update `self.last_refill` to `now`.
4. Do not alter other files or create unnecessary files.
