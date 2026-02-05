/**
 * 댓글 관련 훅
 */
import { useState, useCallback } from 'react';
import { commentApi } from '../api/client';
import { logger } from '../utils/logger';
import type { MemoComment, MemoCommentCreate, MemoCommentUpdate } from '../types/comment';
import type { CommentAIResponseEvent } from './useAnalysisSSE';

export function useComments(memoId: string) {
  const [comments, setComments] = useState<MemoComment[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingAIResponses, setPendingAIResponses] = useState<Set<string>>(new Set());

  const fetchComments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await commentApi.list(memoId);
      setComments(response.items);
      setTotal(response.total);
    } catch (err) {
      setError('댓글을 불러오는데 실패했습니다.');
      logger.error('Failed to fetch comments', err);
    } finally {
      setLoading(false);
    }
  }, [memoId]);

  const createComment = useCallback(
    async (data: MemoCommentCreate) => {
      const newComment = await commentApi.create(memoId, data);
      setComments((prev) => [newComment, ...prev]);
      setTotal((prev) => prev + 1);
      // @태그가 있는 댓글만 AI 응답 대기 중으로 표시 (response_status가 pending일 때)
      if (newComment.response_status === 'pending') {
        setPendingAIResponses((prev) => new Set(prev).add(newComment.id));
      }
      return newComment;
    },
    [memoId]
  );

  const updateComment = useCallback(
    async (commentId: string, data: MemoCommentUpdate) => {
      const updated = await commentApi.update(memoId, commentId, data);
      setComments((prev) =>
        prev.map((c) => (c.id === commentId ? updated : c))
      );
      return updated;
    },
    [memoId]
  );

  const deleteComment = useCallback(
    async (commentId: string) => {
      await commentApi.delete(memoId, commentId);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
      setTotal((prev) => prev - 1);
    },
    [memoId]
  );

  // SSE를 통해 AI 댓글 응답 수신 시 호출
  const handleAIResponse = useCallback(
    (event: CommentAIResponseEvent) => {
      if (event.memo_id !== memoId) return;

      // 대기 상태 해제
      setPendingAIResponses((prev) => {
        const next = new Set(prev);
        next.delete(event.parent_comment_id);
        return next;
      });

      // 댓글 목록 갱신
      fetchComments();
    },
    [memoId, fetchComments]
  );

  // 특정 댓글이 AI 응답 대기 중인지 확인
  const isWaitingForAI = useCallback(
    (commentId: string) => pendingAIResponses.has(commentId),
    [pendingAIResponses]
  );

  return {
    comments,
    total,
    loading,
    error,
    fetchComments,
    createComment,
    updateComment,
    deleteComment,
    handleAIResponse,
    isWaitingForAI,
  };
}
