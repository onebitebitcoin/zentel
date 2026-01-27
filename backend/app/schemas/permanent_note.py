"""
영구 메모 (Permanent Note) Pydantic 스키마
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class NoteStatus(str, Enum):
    """영구 메모 상태"""

    EDITING = "editing"
    PUBLISHED = "published"


class PermanentNoteCreate(BaseModel):
    """영구 메모 생성 스키마"""

    source_memo_ids: List[str] = Field(..., min_length=1)
    title: Optional[str] = Field(default=None, max_length=512)
    content: Optional[str] = Field(default=None, max_length=50000)


class PermanentNoteUpdate(BaseModel):
    """영구 메모 수정 스키마"""

    title: Optional[str] = Field(default=None, max_length=512)
    content: Optional[str] = Field(default=None, max_length=50000)
    interests: Optional[List[str]] = None
    status: Optional[NoteStatus] = None


class PermanentNoteListItem(BaseModel):
    """목록용 스키마 (content 제외)"""

    id: str
    title: str
    status: NoteStatus
    interests: Optional[List[str]] = None
    source_memo_count: int
    created_at: str
    updated_at: Optional[str] = None
    published_at: Optional[str] = None

    model_config = {"from_attributes": True}


class PermanentNoteOut(BaseModel):
    """영구 메모 응답 스키마 (상세 조회용)"""

    id: str
    title: str
    content: str
    status: NoteStatus
    source_memo_ids: List[str]
    interests: Optional[List[str]] = None
    created_at: str
    updated_at: Optional[str] = None
    published_at: Optional[str] = None

    model_config = {"from_attributes": True}


class PermanentNoteListResponse(BaseModel):
    """영구 메모 목록 응답 스키마"""

    items: List[PermanentNoteListItem]
    total: int
