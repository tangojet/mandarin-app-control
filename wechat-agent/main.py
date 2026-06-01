"""WeChat agent — FastAPI service for automating WeChat via desktop container AT-SPI."""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.app import create_app, load_env
from shared.server import run as run_server

load_env()  # load .env before any module-level os.environ reads below

from fastapi import HTTPException, Query, Request
from fastapi.responses import Response

from desktop_client import DesktopClient
from models import HealthResponse, TreeResponse, FindRequest, ActionRequest, TypeRequest, ScrollRequest, KeyRequest, ClickRequest

logger = logging.getLogger("wechat-agent")

client = DesktopClient()

WECHAT_APP_NAME = os.environ.get("WECHAT_APP_NAME", "wechat")


@asynccontextmanager
async def lifespan(app):
    await client.startup()
    try:
        yield
    finally:
        await client.aclose()


app = create_app("wechat-agent", lifespan=lifespan)


@app.get("/health")
async def health():
    info = await client.health()
    return {
        "status": "ok" if info else "error",
        "desktop_agent": info,
    }


@app.get("/apps")
async def list_apps():
    """List all AT-SPI-visible applications in the desktop container."""
    return await client.apps()


@app.get("/tree")
async def get_tree(
    app: str = Query(default=None, description="App name filter (default: wechat)"),
    max_depth: int = Query(default=6, description="Max tree depth (-1 for unlimited)"),
):
    """Get accessibility tree, filtered to WeChat by default."""
    app_name = app if app is not None else WECHAT_APP_NAME
    return await client.tree(app_name=app_name, max_depth=max_depth)


@app.post("/find")
async def find_elements(req: FindRequest):
    """Find elements matching criteria, scoped to WeChat by default."""
    app_name = req.app if req.app is not None else WECHAT_APP_NAME
    return await client.find(
        role=req.role,
        name=req.name,
        states=req.states,
        text=req.text,
        app_name=app_name,
    )


@app.post("/action")
async def do_action(req: ActionRequest):
    """Execute an AT-SPI action on an element by path."""
    return await client.action(path=req.path, action=req.action)


@app.post("/type")
async def type_text(req: TypeRequest):
    """Type text into an element."""
    return await client.type_text(path=req.path, text=req.text)


@app.post("/text")
async def get_text(req: Request):
    """Read text content of an element."""
    data = await req.json()
    return await client.get_text(path=data["path"])


@app.post("/scroll")
async def scroll(req: ScrollRequest):
    """Scroll an element."""
    return await client.scroll(
        path=req.path, direction=req.direction, amount=req.amount,
    )


@app.post("/key")
async def send_key(req: KeyRequest):
    """Send a key event via xdotool."""
    return await client.send_key(key=req.key, modifiers=req.modifiers)


@app.post("/click")
async def click_at(req: ClickRequest):
    """Click at absolute screen coordinates."""
    return await client.click_at(x=req.x, y=req.y, button=req.button)


@app.get("/screenshot")
async def screenshot(
    bounds: str = Query(default=None, description="Crop region as 'x,y,width,height'"),
    quality: int = Query(default=75, description="JPEG quality 1-100"),
):
    """Take a screenshot of the desktop container."""
    data = await client.screenshot(bounds=bounds, quality=quality)
    return Response(content=data, media_type="image/jpeg")


if __name__ == "__main__":
    run_server(app, default_port=8091)
