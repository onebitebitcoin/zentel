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


# ===== 영구 메모 발전 (LLM 분석) 관련 스키마 =====


class MemoAnalysis(BaseModel):
    """개별 메모 분석 결과"""

    memo_index: int = Field(..., description="메모 인덱스 (1부터 시작)")
    core_content: str = Field(..., description="핵심 내용 (1-2문장)")
    key_evidence: List[str] = Field(default_factory=list, description="핵심 근거 목록")


class Synthesis(BaseModel):
    """종합 분석 결과"""

    main_argument: str = Field(..., description="발전시킬 핵심 주장")
    supporting_points: List[str] = Field(default_factory=list, description="뒷받침 포인트")
    counter_considerations: List[str] = Field(
        default_factory=list, description="반론/한계점"
    )


class SuggestedStructure(BaseModel):
    """제안 구조"""

    title: str = Field(..., description="제안 제목")
    thesis: str = Field(..., description="핵심 주장")
    body_outline: List[str] = Field(default_factory=list, description="본문 골격")
    questions_for_development: List[str] = Field(
        default_factory=list, description="추가 탐구 질문"
    )


class SourceMemoInfo(BaseModel):
    """출처 메모 정보"""

    id: str
    content: str
    context: Optional[str] = None


class PermanentNoteDevelopRequest(BaseModel):
    """영구 메모 발전 요청 스키마"""

    source_memo_ids: List[str] = Field(..., min_length=1)


class PermanentNoteDevelopResponse(BaseModel):
    """영구 메모 발전 응답 스키마"""

    memo_analyses: List[MemoAnalysis]
    synthesis: Synthesis
    suggested_structure: SuggestedStructure
    source_memos: List[SourceMemoInfo]
