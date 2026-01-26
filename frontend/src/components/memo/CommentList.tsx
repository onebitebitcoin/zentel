import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { useComments } from '../../hooks/useComments';
import { useAnalysisSSE, CommentAIResponseEvent } from '../../hooks/useAnalysisSSE';
import { useAuth } from '../../hooks/useAuth';
import { CommentInput } from './CommentInput';
import { CommentItem } from './CommentItem';

interface CommentListProps {
  memoId: string;
  onCommentChange?: () => void;
}

export function CommentList({ memoId, onCommentChange }: CommentListProps) {
  const {
    comments,
    loading,
    fetchComments,
    createComment,
    updateComment,
    deleteComment,
    handleAIResponse,
    isWaitingForAI,
  } = useComments(memoId);

  const { user } = useAuth();
  const personas = user?.ai_personas || [];

  const [submitting, setSubmitting] = useState(false);

  // SSE 연결 (AI 댓글 응답 수신)
  useAnalysisSSE(
    () => {},
    (event: CommentAIResponseEvent) => {
      if (event.memo_id === memoId) {
        handleAIResponse(event);
        if (event.status === 'completed') {
          toast.success('AI가 답변을 작성했습니다.');
        }
      }
    }
  );

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  const handleSubmit = async (content: string) => {
    setSubmitting(true);
    try {
      await createComment({ content });
      toast.success('댓글이 추가되었습니다.');
      onCommentChange?.();
    } catch {
      toast.error('댓글 추가에 실패했습니다.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (commentId: string, content: string) => {
    try {
      await updateComment(commentId, { content });
      toast.success('댓글이 수정되었습니다.');
    } catch {
      toast.error('댓글 수정에 실패했습니다.');
    }
  };

  const handleDelete = async (commentId: string) => {
    if (!window.confirm('댓글을 삭제하시겠습니까?')) return;

    try {
      await deleteComment(commentId);
      toast.success('댓글이 삭제되었습니다.');
      onCommentChange?.();
    } catch {
      toast.error('댓글 삭제에 실패했습니다.');
    }
  };

  return (
    <div className="space-y-4">
      {/* 댓글 입력 */}
      <CommentInput
        personas={personas}
        submitting={submitting}
        onSubmit={handleSubmit}
      />

      {/* 댓글 목록 */}
      {loading ? (
        <div className="flex items-center justify-center py-4">
          <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : comments.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-4">
          아직 댓글이 없습니다.
        </p>
      ) : (
        <div className="space-y-3">
          {comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              isWaiting={isWaitingForAI(comment.id)}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
