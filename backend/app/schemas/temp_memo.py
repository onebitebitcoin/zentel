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


class AnalysisStatus(str, Enum):
    """AI 분석 상태"""

    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class HighlightItem(BaseModel):
    """하이라이트 항목"""

    type: str  # "claim" | "fact"
    text: str
    start: int
    end: int
    reason: Optional[str] = None


class TempMemoCreate(BaseModel):
    """임시 메모 생성 스키마"""

    memo_type: MemoType
    content: str = Field(min_length=1, max_length=10000)
    source_url: Optional[str] = Field(default=None, max_length=2048)


class TempMemoUpdate(BaseModel):
    """임시 메모 수정 스키마"""

    memo_type: Optional[MemoType] = None
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    interests: Optional[List[str]] = None
    rematch_interests: Optional[bool] = False  # True면 관심사 다시 매핑


class MemoCommentSummary(BaseModel):
    """메모의 최신 댓글 요약"""

    id: str
    content: str
    created_at: str


class TempMemoListItem(BaseModel):
    """목록용 스키마 (본문 데이터 제외 - lazy loading용)"""

    id: str
    memo_type: MemoType
    content: str
    context: Optional[str] = None
    interests: Optional[List[str]] = None
    source_url: Optional[str] = None
    og_title: Optional[str] = None
    og_image: Optional[str] = None
    fetch_failed: bool = False
    fetch_message: Optional[str] = None
    # AI 분석 상태
    analysis_status: AnalysisStatus = AnalysisStatus.PENDING
    analysis_error: Optional[str] = None
    # 본문 관련 (상세 정보 제외)
    original_language: Optional[str] = None
    is_summary: bool = False
    has_display_content: bool = False  # 본문 존재 여부 플래그
    created_at: str
    updated_at: Optional[str] = None
    comment_count: int = 0
    latest_comment: Optional[MemoCommentSummary] = None

    model_config = {"from_attributes": True}


class TempMemoOut(BaseModel):
    """임시 메모 응답 스키마 (상세 조회용)"""

    id: str
    memo_type: MemoType
    content: str
    context: Optional[str] = None
    interests: Optional[List[str]] = None
    source_url: Optional[str] = None
    og_title: Optional[str] = None
    og_image: Optional[str] = None
    fetch_failed: bool = False
    fetch_message: Optional[str] = None
    # AI 분석 상태
    analysis_status: AnalysisStatus = AnalysisStatus.PENDING
    analysis_error: Optional[str] = None
    # 번역 및 하이라이트
    original_language: Optional[str] = None
    translated_content: Optional[str] = None
    fetched_content: Optional[str] = None  # 스크래핑된 원본 컨텐츠 (URL 메모용)
    display_content: Optional[str] = None  # 최종 표시용 콘텐츠 (번역/정리/단락화 완료)
    is_summary: bool = False  # True면 요약 번역 (긴 글이라 전체 번역 대신 요약)
    highlights: Optional[List[HighlightItem]] = None  # display_content에 맵핑되는 하이라이트
    created_at: str
    updated_at: Optional[str] = None
    comment_count: int = 0
    latest_comment: Optional[MemoCommentSummary] = None

    model_config = {"from_attributes": True}


class TempMemoListResponse(BaseModel):
    """임시 메모 목록 응답 스키마"""

    items: List[TempMemoListItem]
    total: int
    next_offset: Optional[int] = None


class AdminMemoDebugItem(BaseModel):
    """Admin 디버그용 메모 항목 (user_id 포함)"""

    id: str
    user_id: str
    username: str
    memo_type: MemoType
    content_preview: str  # 내용 미리보기 (50자)
    created_at: str


class AdminMemoDebugResponse(BaseModel):
    """Admin 디버그용 메모 목록 응답"""

    items: List[AdminMemoDebugItem]
    total: int
    user_counts: dict  # user_id별 메모 수
