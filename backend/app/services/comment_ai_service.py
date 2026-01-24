"""
댓글 AI 응답 생성 서비스

사용자가 메모에 댓글을 달면 LLM이 비동기로 답변 댓글을 자동 생성합니다.
- 질문 → 메모 내용 바탕으로 답변
- 주장/의견 → 동의(70%) 또는 반론(30%)
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.memo_comment import MemoComment
from app.models.temp_memo import TempMemo
from app.services.llm_service import get_openai_client, LLMError
from app.config import settings

logger = logging.getLogger(__name__)


async def generate_ai_response(
    comment_id: str,
    db: Session,
) -> Optional[MemoComment]:
    """
    사용자 댓글에 대한 AI 응답 생성

    Args:
        comment_id: 사용자 댓글 ID
        db: 데이터베이스 세션

    Returns:
        생성된 AI 댓글 또는 None
    """
    logger.info(f"[CommentAI] AI 응답 생성 시작: comment_id={comment_id}")

    # 1. 원본 댓글 조회
    user_comment = db.query(MemoComment).filter(MemoComment.id == comment_id).first()
    if not user_comment:
        logger.error(f"[CommentAI] 댓글을 찾을 수 없음: comment_id={comment_id}")
        return None

    # AI 댓글에는 응답하지 않음
    if user_comment.is_ai_response:
        logger.info(f"[CommentAI] AI 댓글에는 응답하지 않음: comment_id={comment_id}")
        return None

    # 2. 메모 조회
    memo = db.query(TempMemo).filter(TempMemo.id == user_comment.memo_id).first()
    if not memo:
        logger.error(f"[CommentAI] 메모를 찾을 수 없음: memo_id={user_comment.memo_id}")
        _update_comment_status(user_comment, db, "failed", "메모를 찾을 수 없습니다")
        return None

    # 응답 상태 업데이트
    _update_comment_status(user_comment, db, "generating")

    try:
        # 3. LLM 호출
        ai_content = await _call_llm(
            user_comment=user_comment.content,
            memo_context=memo.context,
            memo_content=memo.display_content or memo.content,
        )

        # 4. AI 댓글 저장
        ai_comment = MemoComment(
            memo_id=user_comment.memo_id,
            content=ai_content,
            is_ai_response=True,
            parent_comment_id=comment_id,
        )
        db.add(ai_comment)

        # 원본 댓글 상태 업데이트
        _update_comment_status(user_comment, db, "completed")

        db.commit()
        db.refresh(ai_comment)

        logger.info(f"[CommentAI] AI 응답 생성 완료: ai_comment_id={ai_comment.id}")
        return ai_comment

    except LLMError as e:
        error_msg = str(e)
        logger.error(f"[CommentAI] LLM 에러: {error_msg}")
        _update_comment_status(user_comment, db, "failed", error_msg)
        db.commit()
        return None

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[CommentAI] 예상치 못한 에러: {error_msg}", exc_info=True)
        _update_comment_status(user_comment, db, "failed", error_msg)
        db.commit()
        return None


def _update_comment_status(
    comment: MemoComment,
    db: Session,
    status: str,
    error: Optional[str] = None,
) -> None:
    """댓글 응답 상태 업데이트"""
    comment.response_status = status
    comment.response_error = error
    comment.updated_at = datetime.now(timezone.utc).isoformat()


async def _call_llm(
    user_comment: str,
    memo_context: Optional[str],
    memo_content: Optional[str],
) -> str:
    """
    LLM 호출하여 AI 응답 생성

    Args:
        user_comment: 사용자 댓글 내용
        memo_context: 메모의 context (요약)
        memo_content: 메모 본문

    Returns:
        AI 응답 텍스트

    Raises:
        LLMError: API 키 미설정, 빈 응답, 호출 실패 시
    """
    client = get_openai_client()
    if not client:
        error_msg = "OpenAI API 키가 설정되지 않았습니다"
        logger.error(f"[CommentAI] {error_msg}")
        raise LLMError(error_msg)

    # 동의/반론 비율 결정 (70% 동의, 30% 반론)
    should_agree = random.random() < 0.7

    response_style = (
        "동의하고 보충 설명을 추가"
        if should_agree
        else "정중하게 다른 관점을 제시"
    )

    # 메모 컨텍스트 구성
    memo_info = ""
    if memo_context:
        memo_info += f"메모 요약: {memo_context}\n\n"
    if memo_content:
        # 본문은 너무 길면 자름
        content_preview = memo_content[:2000] if len(memo_content) > 2000 else memo_content
        memo_info += f"메모 본문:\n{content_preview}"

    if not memo_info:
        memo_info = "(메모 내용 없음)"

    try:
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            instructions=(
                "당신은 메모에 대해 함께 생각하는 AI 파트너입니다.\n\n"
                "역할:\n"
                "- 사용자의 댓글이 질문이면 → 메모 내용을 바탕으로 답변\n"
                f"- 사용자의 댓글이 의견/주장이면 → {response_style}\n\n"
                "규칙:\n"
                "- 2-3문장으로 간결하게 응답\n"
                "- 한국어로 응답\n"
                "- 마지막에 사고를 확장할 수 있는 질문 하나 추가\n"
                "- 마크다운 형식 없이 순수 텍스트로만 응답\n"
                "- 친근하지만 존중하는 어조 유지"
            ),
            input=(
                f"[메모 정보]\n{memo_info}\n\n"
                f"[사용자 댓글]\n{user_comment}\n\n"
                "위 댓글에 적절히 응답해주세요."
            ),
            max_output_tokens=500,
        )

        result = response.output_text
        if result:
            result = result.strip()
            logger.info(f"[CommentAI] LLM 응답 생성: {len(result)}자")
            return result

        # 빈 응답
        error_msg = "LLM이 빈 응답을 반환했습니다"
        logger.error(f"[CommentAI] {error_msg}")
        raise LLMError(error_msg)

    except LLMError:
        raise
    except Exception as e:
        error_msg = f"LLM 호출 실패: {e}"
        logger.error(f"[CommentAI] {error_msg}", exc_info=True)
        raise LLMError(error_msg) from e
