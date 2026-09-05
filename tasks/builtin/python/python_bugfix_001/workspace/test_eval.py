import time
from src.rate_limiter import TokenBucket


def test_token_bucket_refill():
    bucket = TokenBucket(capacity=10.0, refill_rate=2.0)
    # Drain all tokens
    assert bucket.consume(10.0) is True
    assert bucket.tokens == 0.0

    # Simulate passing of 3 seconds
    bucket.last_refill = time.time() - 3.0
    bucket.refill()

    # Should have refilled ~6 tokens
    assert bucket.tokens >= 5.9
    assert bucket.consume(5.0) is True


def test_refill_caps_at_capacity():
    bucket = TokenBucket(capacity=5.0, refill_rate=10.0)
    bucket.last_refill = time.time() - 10.0
    bucket.refill()
    assert bucket.tokens == 5.0
