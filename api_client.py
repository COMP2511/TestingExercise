import os

import requests
from dotenv import load_dotenv

# The server address is configuration, not code. It comes from .env or the environment,
# so moving the server never means editing a source file.
load_dotenv()

DEFAULT_BASE_URL = "http://127.0.0.1:5000"


class ApiError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class ToolsClient:
    def __init__(self, base_url=None):
        configured = base_url or os.environ.get("TOOLS_API_BASE") or DEFAULT_BASE_URL
        self.base_url = configured.rstrip("/")

    def _request(self, method, path, **kwargs):
        response = requests.request(
            method, f"{self.base_url}{path}", timeout=10, **kwargs
        )
        if response.status_code >= 400:
            body = response.json() if response.content else {}
            message = body.get("error", response.text or "request failed")
            raise ApiError(response.status_code, message)
        return response.json()

    def health(self):
        return self._request("GET", "/api")

    def list_tools(self, name=None):
        params = {"name": name} if name else None
        return self._request("GET", "/api/v2/tools", params=params)["data"]

    def get_tool(self, tool_id):
        return self._request("GET", f"/api/v2/tools/{tool_id}")["data"]

    def create_tool(self, name, quantity, price, idempotency_key):
        return self._request(
            "POST",
            "/api/v2/tools",
            json={"name": name, "quantity": quantity, "price": price},
            headers={"Idempotency-Key": idempotency_key},
        )["data"]
