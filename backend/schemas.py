"""
schemas.py — Pydantic request/response schemas for the Content Intelligence Platform.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# ─── User ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str

class UserOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ─── Tag ─────────────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    label: str

class TagOut(BaseModel):
    id: int
    content_id: int
    label: str

    class Config:
        from_attributes = True


# ─── GeneratedOutput ─────────────────────────────────────────────────────────

class OutputUpdate(BaseModel):
    text: str

class GeneratedOutputOut(BaseModel):
    id: int
    content_id: int
    output_type: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Content ─────────────────────────────────────────────────────────────────

class ContentCreate(BaseModel):
    user_id: int
    title: Optional[str] = "Untitled"
    original_text: str

class ContentOut(BaseModel):
    id: int
    user_id: int
    title: str
    original_text: str
    created_at: datetime
    outputs: List[GeneratedOutputOut] = []
    tags: List[TagOut] = []

    class Config:
        from_attributes = True

class ContentListItem(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── AI ──────────────────────────────────────────────────────────────────────

class TransformRequest(BaseModel):
    format: str  # faq | social_post | email_summary | press_release

class SaveOutputsRequest(BaseModel):
    """Batch-save multiple generated outputs for a content item."""
    outputs: List[dict]  # [{"output_type": "...", "text": "..."}]
