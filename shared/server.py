"""Shared uvicorn server runner."""

from __future__ import annotations

import os


def run(app, default_port: int) -> None:
    """Run the app with uvicorn, reading PORT from env."""
    import uvicorn

    port = int(os.environ.get("PORT", str(default_port)))
    uvicorn.run(app, host="0.0.0.0", port=port)
