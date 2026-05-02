"""Pydantic request/response models for wechat-agent."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    desktop_agent: Optional[dict] = None


class TreeResponse(BaseModel):
    pass  # dynamic structure from AT-SPI


class FindRequest(BaseModel):
    role: Optional[str] = None
    name: Optional[str] = None
    states: Optional[List[str]] = None
    text: Optional[str] = None
    app: Optional[str] = None


class ActionRequest(BaseModel):
    path: List[int]
    action: str = "click"


class TypeRequest(BaseModel):
    path: List[int]
    text: str


class ScrollRequest(BaseModel):
    path: List[int]
    direction: str = "down"
    amount: int = 3


class KeyRequest(BaseModel):
    key: str
    modifiers: Optional[List[str]] = None


class ClickRequest(BaseModel):
    x: int
    y: int
    button: int = 1
