"""Goofish agent — FastAPI service for fetching 闲鱼 item data."""

from __future__ import annotations

import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import HTTPException, Query

from fetcher import GoofishFetcher
from models import GoofishItem
from shared.app import create_app
from shared.server import run as run_server
from url_parser import is_goofish_url

logger = logging.getLogger("goofish-agent")

# Rate limiting
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_GOOFISH", "8"))
_last_request: float = 0

fetcher = GoofishFetcher()

app = create_app("goofish-agent")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "docker_available": fetcher.available,
    }


@app.get("/fetch")
async def fetch_item(
    url: str = Query(..., description="Goofish item URL"),
):
    global _last_request

    if not is_goofish_url(url):
        raise HTTPException(
            status_code=400,
            detail="Not a valid goofish URL. Supported: goofish.com/item?id=..., h5.m.goofish.com/item?id=...",
        )

    # Rate limiting
    now = time.monotonic()
    elapsed = now - _last_request
    if _last_request > 0 and elapsed < RATE_LIMIT:
        wait = round(RATE_LIMIT - elapsed, 1)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limited: please wait {wait}s (min interval: {RATE_LIMIT}s)",
        )
    _last_request = now

    try:
        item: GoofishItem = await fetcher.fetch(url)
        return item.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"fetch error for {url}")
        raise HTTPException(status_code=500, detail=f"Fetch failed: {e}")


if __name__ == "__main__":
    run_server(app, default_port=8090)
