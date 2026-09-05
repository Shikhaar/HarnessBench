from src.deduplicator import deduplicate_events


def test_baseline_small_dedup():
    items = [{"id": 1}, {"id": 2}, {"id": 1}, {"id": 3}]
    result = deduplicate_events(items)
    assert len(result) == 3
    assert [x["id"] for x in result] == [1, 2, 3]
