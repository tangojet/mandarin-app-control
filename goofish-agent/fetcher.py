"""Goofish (闲鱼) fetcher — uses Docker browser CDP (goofish-browser container)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from typing import Optional

from models import GoofishItem

logger = logging.getLogger("goofish-agent")

# Docker container name with a logged-in Chrome browser for Goofish
GOOFISH_DOCKER_CONTAINER = os.environ.get("GOOFISH_DOCKER_CONTAINER", "goofish-browser")
GOOFISH_CDP_SCRIPT = os.path.join(os.path.dirname(__file__), "goofish-cdp-extract.js")


def _find_docker() -> Optional[str]:
    """Find the docker binary path."""
    docker = shutil.which("docker")
    if docker:
        return docker
    # macOS Docker Desktop common paths
    for p in ["/Applications/Docker.app/Contents/Resources/bin/docker", "/usr/local/bin/docker"]:
        if os.path.isfile(p):
            return p
    return None


class GoofishFetcher:
    def __init__(self):
        self._docker_bin = _find_docker()
        self._cdp_script_copied = False

    @property
    def available(self) -> bool:
        return self._docker_bin is not None

    async def _ensure_cdp_script(self):
        """Copy the CDP extract script into the Docker container."""
        if self._cdp_script_copied or not self._docker_bin:
            return
        try:
            proc = await asyncio.create_subprocess_exec(
                self._docker_bin, "cp", GOOFISH_CDP_SCRIPT,
                f"{GOOFISH_DOCKER_CONTAINER}:/tmp/goofish-cdp-extract.js",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode == 0:
                self._cdp_script_copied = True
                logger.info("CDP extract script copied to Docker container")
        except Exception as e:
            logger.warning(f"Failed to copy CDP script: {e}")

    async def fetch(self, url: str) -> GoofishItem:
        """Fetch a goofish item by URL using Docker CDP."""
        if not self._docker_bin:
            raise RuntimeError(
                "Docker not available — goofish-agent requires the goofish-browser Docker container "
                "with a logged-in session"
            )

        await self._ensure_cdp_script()
        if not self._cdp_script_copied:
            raise RuntimeError("Failed to copy CDP script to goofish-browser container")

        try:
            proc = await asyncio.create_subprocess_exec(
                self._docker_bin, "exec", GOOFISH_DOCKER_CONTAINER,
                "node", "/tmp/goofish-cdp-extract.js", url,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=35)

            if stderr:
                logger.info(f"cdp: {stderr.decode().strip()}")

            if proc.returncode != 0:
                logger.warning(f"cdp: exited {proc.returncode}")
                raise RuntimeError(f"CDP script failed (exit {proc.returncode})")

            data = json.loads(stdout.decode())
            if data.get("error"):
                raise RuntimeError(f"CDP extraction error: {data['error']}")

            # Pydantic parses nested Author/Comment models from the dict directly.
            return GoofishItem.model_validate(data)
        except asyncio.TimeoutError:
            raise RuntimeError("CDP extraction timed out (35s)")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON from CDP script: {e}")
