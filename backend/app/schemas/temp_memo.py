"""
임시 메모 (Temporary Memo) Pydantic 스키마
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MemoType(str, Enum):
    """메모 타입 (7종)"""

    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"
    NEW_IDEA = "NEW_IDEA"
    NEW_GOAL = "NEW_GOAL"
    EVOLVED_THOUGHT = "EVOLVED_THOUGHT"
    CURIOSITY = "CURIOSITY"
    UNRESOLVED_PROBLEM = "UNRESOLVED_PROBLEM"
    EMOTION = "EMOTION"


class TempMemoCreate(BaseModel):
    """임시 메모 생성 스키마"""

    memo_type: MemoType
    content: str = Field(min_length=1, max_length=10000)
    source_url: Optional[str] = Field(default=None, max_length=2048)


class TempMemoUpdate(BaseModel):
    """임시 메모 수정 스키마"""

    memo_type: Optional[MemoType] = None
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)


class MemoCommentSummary(BaseModel):
    """메모의 최신 댓글 요약"""

    id: str
    content: str
    created_at: str


class TempMemoOut(BaseModel):
    """임시 메모 응답 스키마"""

    id: str
    memo_type: MemoType
    content: str
    context: Optional[str] = None
    facts: Optional[List[str]] = None
    source_url: Optional[str] = None
    og_title: Optional[str] = None
    og_image: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    comment_count: int = 0
    latest_comment: Optional[MemoCommentSummary] = None

    model_config = {"from_attributes": True}


class TempMemoListResponse(BaseModel):
    """임시 메모 목록 응답 스키마"""

    items: List[TempMemoOut]
    total: int
    next_offset: Optional[int] = None
