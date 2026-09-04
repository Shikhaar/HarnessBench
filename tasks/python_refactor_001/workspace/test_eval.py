import pytest
from src.client import ApiClient
from src.config import ClientConfig


def test_client_config_validation():
    with pytest.raises(ValueError, match="api_key"):
        ClientConfig(api_key="")

    with pytest.raises(ValueError, match="scheme"):
        ClientConfig(api_key="valid-key", base_url="ftp://invalid.com")

    cfg = ClientConfig(api_key="secret", base_url="https://test.api", timeout=15)
    assert cfg.api_key == "secret"
    assert cfg.base_url == "https://test.api"
    assert cfg.timeout == 15


def test_api_client_integration():
    # Direct construction
    client1 = ApiClient(api_key="key-123", base_url="http://local.dev")
    assert client1.api_key == "key-123"
    assert client1.base_url == "http://local.dev"
    assert client1.get_endpoint("/v1/items") == "http://local.dev/v1/items"

    # Construction via ClientConfig
    cfg = ClientConfig(api_key="key-config", base_url="https://api.gateway.com", timeout=60)
    client2 = ApiClient(config=cfg)
    assert client2.api_key == "key-config"
    assert client2.timeout == 60
    assert client2.get_endpoint("health") == "https://api.gateway.com/health"
