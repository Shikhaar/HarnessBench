class ApiClient:
    """Legacy un-refactored client."""

    def __init__(self, api_key: str, base_url: str = "https://api.example.com", timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def get_endpoint(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
