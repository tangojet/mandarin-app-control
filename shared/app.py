"""Shared FastAPI app factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI


def create_app(title: str) -> FastAPI:
    """Create a FastAPI instance with standardized logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    return FastAPI(title=title)
