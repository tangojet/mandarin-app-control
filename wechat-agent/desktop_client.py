"""HTTP client for the AT-SPI desktop agent running inside the Docker container."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("wechat-agent")

# AT-SPI agent endpoint inside the desktop container
DESKTOP_AGENT_URL = os.environ.get("DESKTOP_AGENT_URL", "http://localhost:55007")
REQUEST_TIMEOUT = int(os.environ.get("DESKTOP_REQUEST_TIMEOUT", "15"))


class DesktopClient:
    """Async HTTP client for the AT-SPI desktop automation agent."""

    def __init__(self):
        self._base_url = DESKTOP_AGENT_URL.rstrip("/")
        self._timeout = REQUEST_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    async def startup(self) -> None:
        """Open the shared HTTP client (call on app startup)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout,
            )

    async def aclose(self) -> None:
        """Close the shared HTTP client (call on app shutdown)."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def _http(self) -> httpx.AsyncClient:
        # Lazily open the client so calls before startup() still work.
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout,
            )
        return self._client

    async def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        resp = await self._http.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _get_raw(self, path: str, params: Optional[Dict] = None) -> bytes:
        resp = await self._http.get(path, params=params)
        resp.raise_for_status()
        return resp.content

    async def _post(self, path: str, data: Dict) -> Any:
        resp = await self._http.post(path, json=data)
        resp.raise_for_status()
        return resp.json()

    # ── High-level API ────────────────────────────────────────────────────

    async def health(self) -> Optional[Dict]:
        try:
            return await self._get("/health")
        except Exception as e:
            logger.warning(f"Desktop agent health check failed: {e}")
            return None

    async def apps(self) -> List[Dict]:
        return await self._get("/apps")

    async def tree(self, app_name: Optional[str] = None, max_depth: int = 6) -> Any:
        params = {"max_depth": str(max_depth)}
        if app_name:
            params["app"] = app_name
        return await self._get("/tree", params=params)

    async def find(
        self,
        role: Optional[str] = None,
        name: Optional[str] = None,
        states: Optional[List[str]] = None,
        text: Optional[str] = None,
        app_name: Optional[str] = None,
    ) -> List[Dict]:
        body: Dict = {}
        if role:
            body["role"] = role
        if name:
            body["name"] = name
        if states:
            body["states"] = states
        if text:
            body["text"] = text
        if app_name:
            body["app"] = app_name
        return await self._post("/find", body)

    async def action(self, path: List[int], action: str = "click") -> Dict:
        return await self._post("/action", {"path": path, "action": action})

    async def type_text(self, path: List[int], text: str) -> Dict:
        return await self._post("/type", {"path": path, "text": text})

    async def get_text(self, path: List[int]) -> Dict:
        return await self._post("/text", {"path": path})

    async def scroll(
        self, path: List[int], direction: str = "down", amount: int = 3,
    ) -> Dict:
        return await self._post("/scroll", {
            "path": path, "direction": direction, "amount": amount,
        })

    async def send_key(self, key: str, modifiers: Optional[List[str]] = None) -> Dict:
        body: Dict = {"key": key}
        if modifiers:
            body["modifiers"] = modifiers
        return await self._post("/key", body)

    async def click_at(self, x: int, y: int, button: int = 1) -> Dict:
        return await self._post("/click", {"x": x, "y": y, "button": button})

    async def screenshot(
        self, bounds: Optional[str] = None, quality: int = 75,
    ) -> bytes:
        params: Dict = {"quality": str(quality)}
        if bounds:
            params["bounds"] = bounds
        return await self._get_raw("/screenshot", params=params)
