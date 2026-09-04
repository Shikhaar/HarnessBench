from src.client import ApiClient


def test_baseline_client_creation():
    client = ApiClient(api_key="baseline-token")
    assert client.api_key == "baseline-token"
    assert client.get_endpoint("/users") == "https://api.example.com/users"
