from src.rate_limiter import TokenBucket


def test_initial_capacity():
    bucket = TokenBucket(capacity=5, refill_rate=1)
    assert bucket.tokens == 5.0
    assert bucket.consume(3) is True
    assert bucket.tokens == 2.0
