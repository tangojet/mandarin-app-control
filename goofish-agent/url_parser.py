"""Goofish URL detection and item ID extraction."""

from __future__ import annotations

import re
from typing import Optional

# Goofish (闲鱼) URL patterns
GOOFISH_PATTERNS = [
    # Item page: goofish.com/item?id={itemId}
    re.compile(r"https?://(?:www\.)?goofish\.com/item\?(?:[^#]*&)?id=(\d+)"),
    # Mobile: h5.m.goofish.com/item?id={itemId}
    re.compile(r"https?://h5\.m\.goofish\.com/item\?(?:[^#]*&)?id=(\d+)"),
    # Legacy idle.taobao URLs
    re.compile(r"https?://market\.m\.taobao\.com/app/idleFish-F2e/.*[?&]id=(\d+)"),
]


def is_goofish_url(url: str) -> bool:
    """Return True if URL is a recognized goofish item URL."""
    return any(pat.search(url) for pat in GOOFISH_PATTERNS)


def extract_item_id(url: str) -> Optional[str]:
    """Extract item ID from a goofish.com URL."""
    for pat in GOOFISH_PATTERNS:
        m = pat.search(url)
        if m:
            return m.group(1)
    return None
