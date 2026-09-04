import time


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        """
        capacity: Maximum tokens the bucket can hold.
        refill_rate: Tokens added per second.
        """
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def refill(self) -> None:
        now = time.time()
        # BUG: Inverted elapsed calculation causes elapsed to be negative or 0
        elapsed = self.last_refill - now
        if elapsed > 0:
            added = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + added)
            self.last_refill = now

    def consume(self, amount: float = 1.0) -> bool:
        self.refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False
