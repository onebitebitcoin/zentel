"""
영구 메모 (Permanent Note) API 라우터
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.permanent_note import PermanentNote
from app.models.user import User
from app.schemas.permanent_note import (
    NoteStatus,
    PermanentNoteCreate,
    PermanentNoteListItem,
    PermanentNoteListResponse,
    PermanentNoteOut,
    PermanentNoteUpdate,
)
from app.services.memo_repository import memo_repository, permanent_note_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/permanent-notes", tags=["permanent-notes"])


def get_user_note(db: Session, note_id: str, user_id: str) -> PermanentNote:
    """사용자 소유 영구 메모 조회 (없거나 소유하지 않으면 404)"""
    note = permanent_note_repository.get_user_note(db, note_id, user_id)
    if not note:
        raise HTTPException(status_code=404, detail="영구 메모를 찾을 수 없습니다.")
    return note


def note_to_list_item(note: PermanentNote) -> PermanentNoteListItem:
    """PermanentNote를 PermanentNoteListItem으로 변환"""
    return PermanentNoteListItem(
        id=note.id,
        title=note.title,
        status=NoteStatus(note.status),
        interests=note.interests,
        source_memo_count=len(note.source_memo_ids) if note.source_memo_ids else 0,
        created_at=note.created_at,
        updated_at=note.updated_at,
        published_at=note.published_at,
    )


def note_to_out(note: PermanentNote) -> PermanentNoteOut:
    """PermanentNote를 PermanentNoteOut으로 변환"""
    return PermanentNoteOut(
        id=note.id,
        title=note.title,
        content=note.content,
        status=NoteStatus(note.status),
        source_memo_ids=note.source_memo_ids or [],
        interests=note.interests,
        created_at=note.created_at,
        updated_at=note.updated_at,
        published_at=note.published_at,
    )


@router.post("", response_model=PermanentNoteOut, status_code=201)
async def create_permanent_note(
    data: PermanentNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """영구 메모 생성 (임시 메모 변환)"""
    logger.info(
        f"Creating permanent note: user_id={current_user.id}, "
        f"source_memo_count={len(data.source_memo_ids)}"
    )

    # 출처 임시 메모들 검증 및 조회
    source_memos = []
    for memo_id in data.source_memo_ids:
        memo = memo_repository.get_user_memo(db, memo_id, current_user.id)
        if not memo:
            raise HTTPException(
                status_code=404,
                detail=f"임시 메모를 찾을 수 없습니다: {memo_id}"
            )
        source_memos.append(memo)

    # 제목 생성: 첫 번째 메모의 첫 줄 (미지정 시)
    title = data.title
    if not title:
        first_memo = source_memos[0]
        first_line = first_memo.content.split("\n")[0].strip()
        title = first_line[:80] if len(first_line) > 80 else first_line

    # 내용 생성: 모든 메모 구분자로 합침 (미지정 시)
    content = data.content
    if not content:
        contents = [memo.content for memo in source_memos]
        content = "\n\n---\n\n".join(contents)

    # 관심사 병합 (중복 제거)
    all_interests: set[str] = set()
    for memo in source_memos:
        if memo.interests:
            all_interests.update(memo.interests)
    interests = list(all_interests) if all_interests else None

    # 영구 메모 생성
    db_note = PermanentNote(
        user_id=current_user.id,
        title=title,
        content=content,
        status="editing",
        source_memo_ids=data.source_memo_ids,
        interests=interests,
    )
    db_note = permanent_note_repository.create(db, db_note)

    logger.info(f"Created permanent note: id={db_note.id}")
    return note_to_out(db_note)


@router.get("", response_model=PermanentNoteListResponse)
async def list_permanent_notes(
    status: Optional[NoteStatus] = Query(default=None, description="상태 필터"),
    limit: int = Query(default=20, ge=1, le=100, description="가져올 개수"),
    offset: int = Query(default=0, ge=0, description="시작 위치"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """영구 메모 목록 조회 (최신순, 본인 메모만)"""
    logger.info(
        f"Listing permanent notes: user_id={current_user.id}, status={status}, "
        f"limit={limit}, offset={offset}"
    )

    status_value = status.value if status else None
    db_items, total = permanent_note_repository.list_user_notes(
        db, current_user.id, status_value, limit, offset
    )

    items = [note_to_list_item(note) for note in db_items]

    logger.info(f"Found {len(items)} permanent notes (total: {total})")
    return PermanentNoteListResponse(items=items, total=total)


@router.get("/{note_id}", response_model=PermanentNoteOut)
async def get_permanent_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """영구 메모 상세 조회 (본인 메모만)"""
    logger.info(f"Getting permanent note: id={note_id}, user_id={current_user.id}")

    db_note = get_user_note(db, note_id, current_user.id)

    return note_to_out(db_note)


@router.patch("/{note_id}", response_model=PermanentNoteOut)
async def update_permanent_note(
    note_id: str,
    data: PermanentNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """영구 메모 수정 (본인 메모만)"""
    logger.info(f"Updating permanent note: id={note_id}, user_id={current_user.id}")

    db_note = get_user_note(db, note_id, current_user.id)

    if data.title is not None:
        db_note.title = data.title
    if data.content is not None:
        db_note.content = data.content
    if data.interests is not None:
        db_note.interests = data.interests if data.interests else None

    # 상태 변경 처리
    if data.status is not None:
        if data.status == NoteStatus.PUBLISHED and db_note.status != "published":
            # 발행 시 published_at 설정
            db_note.published_at = datetime.now(timezone.utc).isoformat()
        db_note.status = data.status.value

    db_note.updated_at = datetime.now(timezone.utc).isoformat()
    db_note = permanent_note_repository.update(db, db_note)

    logger.info(f"Updated permanent note: id={note_id}")
    return note_to_out(db_note)


@router.delete("/{note_id}", status_code=204)
async def delete_permanent_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """영구 메모 삭제 (본인 메모만)"""
    logger.info(f"Deleting permanent note: id={note_id}, user_id={current_user.id}")

    db_note = get_user_note(db, note_id, current_user.id)
    permanent_note_repository.delete(db, db_note)

    logger.info(f"Deleted permanent note: id={note_id}")
    return None
