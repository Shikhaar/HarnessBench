import collections


def is_valid_key(key: str) -> bool:
    """Check if a key is a valid non-empty string."""
    return isinstance(key, str) and bool(key.strip())


def sanitize_payload(payload):
    """Sanitize dictionary keys, omitting private fields starting with underscore."""
    # BUG: collections.Mapping does not exist in Python 3.10+
    if isinstance(payload, collections.Mapping):
        return {k: sanitize_payload(v) for k, v in payload.items() if not k.startswith("_")}
    elif isinstance(payload, list):
        return [sanitize_payload(x) for x in payload]
    return payload
