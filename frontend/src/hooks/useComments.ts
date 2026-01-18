/**
 * 댓글 관련 훅
 */
import { useState, useCallback } from 'react';
import { commentApi } from '../api/client';
import type { MemoComment, MemoCommentCreate, MemoCommentUpdate } from '../types/comment';

export function useComments(memoId: string) {
  const [comments, setComments] = useState<MemoComment[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchComments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await commentApi.list(memoId);
      setComments(response.items);
      setTotal(response.total);
    } catch (err) {
      setError('댓글을 불러오는데 실패했습니다.');
      console.error('Failed to fetch comments:', err);
    } finally {
      setLoading(false);
    }
  }, [memoId]);

  const createComment = useCallback(
    async (data: MemoCommentCreate) => {
      const newComment = await commentApi.create(memoId, data);
      setComments((prev) => [newComment, ...prev]);
      setTotal((prev) => prev + 1);
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

  return {
    comments,
    total,
    loading,
    error,
    fetchComments,
    createComment,
    updateComment,
    deleteComment,
  };
}
