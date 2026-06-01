"""Shared FastAPI app factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI


def load_env() -> None:
    """Load variables from a local .env file if python-dotenv is installed.

    Call this at the top of an agent's main.py, before any module-level
    os.environ reads, so direct `python main.py` runs pick up .env too.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def create_app(title: str, lifespan=None) -> FastAPI:
    """Create a FastAPI instance with standardized logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    return FastAPI(title=title, lifespan=lifespan)
