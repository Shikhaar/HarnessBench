from typing import Any, Dict, List


def deduplicate_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate events preserving first seen order.

    BUG: O(N^2) search over previously collected events.
    """
    unique_events: List[Dict[str, Any]] = []
    for event in events:
        eid = event.get("id")
        if eid not in [e.get("id") for e in unique_events]:
            unique_events.append(event)
    return unique_events
