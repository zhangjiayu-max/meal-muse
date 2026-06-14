"""MCP Server 通用 HTTP 客户端"""
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MCPClient:
    """通用 MCP HTTP 客户端，封装请求、超时、错误处理"""

    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        """GET 请求"""
        client = await self._get_client()
        url = f"{self.base_url}{path}"
        if self.api_key:
            params = params or {}
            params["apiKey"] = self.api_key
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.warning(f"MCP request failed: {url} — {e}")
            return {"error": str(e)}

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.close()
