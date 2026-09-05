import time
from src.deduplicator import deduplicate_events


def test_perf_large_scale():
    # 6000 items with duplicate IDs
    items = [{"id": i % 3000, "val": i} for i in range(6000)]

    start = time.perf_counter()
    deduped = deduplicate_events(items)
    duration = time.perf_counter() - start

    assert len(deduped) == 3000
    assert deduped[0]["id"] == 0
    assert deduped[2999]["id"] == 2999
    # O(N) takes <0.02s, O(N^2) takes >0.6s
    assert duration < 0.15, f"Execution too slow: {duration:.4f}s (must be O(N))"
