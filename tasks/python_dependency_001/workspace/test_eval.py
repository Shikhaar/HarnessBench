from src.sanitizer import sanitize_payload


def test_sanitize_nested_dict():
    data = {
        "user_id": 42,
        "_secret_hash": "abcdef",
        "profile": {
            "name": "Alice",
            "_internal_flag": True,
        },
        "tags": ["admin", "dev"],
    }
    cleaned = sanitize_payload(data)
    assert "_secret_hash" not in cleaned
    assert cleaned["user_id"] == 42
    assert "_internal_flag" not in cleaned["profile"]
    assert cleaned["profile"]["name"] == "Alice"
    assert cleaned["tags"] == ["admin", "dev"]
