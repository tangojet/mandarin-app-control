"""Pydantic response models for goofish-agent."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class Author(BaseModel):
    name: str
    id: str = ""
    avatar: Optional[str] = None
    signature: Optional[str] = None
    ip_location: Optional[str] = None


class Comment(BaseModel):
    user: str
    text: str
    likes: int = 0
    time: str = ""
    ip_location: Optional[str] = None
    sub_comment_count: int = 0


class GoofishItem(BaseModel):
    platform: str = "goofish"
    title: str
    author: Author
    content: str
    stats: Dict[str, int]
    images: List[str] = []
    video_url: Optional[str] = None
    comments: List[Comment] = []
    url: str
    fetched_at: str
