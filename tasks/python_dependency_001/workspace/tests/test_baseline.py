from src.sanitizer import is_valid_key


def test_baseline_key_validation():
    assert is_valid_key("user_id") is True
    assert is_valid_key("") is False
