"""
메모 댓글 (MemoComment) Pydantic 스키마
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MemoCommentCreate(BaseModel):
    """메모 댓글 생성 스키마"""

    content: str = Field(min_length=1, max_length=2000)


class MemoCommentUpdate(BaseModel):
    """메모 댓글 수정 스키마"""

    content: Optional[str] = Field(default=None, min_length=1, max_length=2000)


class MemoCommentOut(BaseModel):
    """메모 댓글 응답 스키마"""

    id: str
    memo_id: str
    content: str
    created_at: str
    updated_at: Optional[str] = None
    is_ai_response: bool = False
    parent_comment_id: Optional[str] = None
    response_status: Optional[str] = None
    response_error: Optional[str] = None

    model_config = {"from_attributes": True}


class MemoCommentListResponse(BaseModel):
    """메모 댓글 목록 응답 스키마"""

    items: list[MemoCommentOut]
    total: int
