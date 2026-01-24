import { useState, useEffect } from 'react';
import { Send, Trash2, Pencil, X, Check, Bot, User, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { useComments } from '../../hooks/useComments';
import { useAnalysisSSE, CommentAIResponseEvent } from '../../hooks/useAnalysisSSE';
import { getRelativeTime } from '../../utils/date';

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

  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  // SSE 연결 (AI 댓글 응답 수신)
  useAnalysisSSE(
    () => {}, // 분석 완료 이벤트는 여기서 사용하지 않음
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

  const handleSubmit = async () => {
    if (!newComment.trim() || submitting) return;

    setSubmitting(true);
    try {
      await createComment({ content: newComment.trim() });
      setNewComment('');
      toast.success('댓글이 추가되었습니다.');
      onCommentChange?.();
    } catch {
      toast.error('댓글 추가에 실패했습니다.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (commentId: string) => {
    if (!editContent.trim()) return;

    try {
      await updateComment(commentId, { content: editContent.trim() });
      setEditingId(null);
      setEditContent('');
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

  const startEdit = (commentId: string, content: string) => {
    setEditingId(commentId);
    setEditContent(content);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditContent('');
  };

  return (
    <div className="space-y-4">
      {/* 댓글 입력 */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder="의견을 남겨보세요..."
          className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary"
        />
        <button
          onClick={handleSubmit}
          disabled={!newComment.trim() || submitting}
          className="px-3 py-2 text-white bg-primary rounded-lg hover:bg-primary-600 disabled:opacity-50"
        >
          <Send size={16} />
        </button>
      </div>

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
          {comments.map((comment) => {
            const isAI = comment.is_ai_response;
            const isWaiting = isWaitingForAI(comment.id);

            return (
              <div
                key={comment.id}
                className={`p-3 rounded-lg ${
                  isAI ? 'bg-blue-50 border border-blue-100' : 'bg-gray-50'
                }`}
              >
                {editingId === comment.id ? (
                  <div className="space-y-2">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full p-2 text-sm border border-gray-200 rounded-lg resize-none focus:outline-none focus:border-primary"
                      rows={2}
                    />
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={cancelEdit}
                        className="p-1.5 text-gray-400 hover:text-gray-600"
                      >
                        <X size={16} />
                      </button>
                      <button
                        onClick={() => handleUpdate(comment.id)}
                        className="p-1.5 text-primary hover:text-primary-600"
                      >
                        <Check size={16} />
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start gap-2">
                      <div
                        className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                          isAI ? 'bg-blue-100 text-blue-600' : 'bg-gray-200 text-gray-500'
                        }`}
                      >
                        {isAI ? <Bot size={14} /> : <User size={14} />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {comment.content}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-2 pl-8">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">
                          {isAI ? 'AI' : ''} {getRelativeTime(comment.created_at)}
                        </span>
                        {isWaiting && (
                          <span className="flex items-center gap-1 text-xs text-blue-500">
                            <Loader2 size={12} className="animate-spin" />
                            AI 응답 대기 중
                          </span>
                        )}
                      </div>
                      {!isAI && (
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => startEdit(comment.id, comment.content)}
                            className="p-1 text-gray-400 hover:text-primary"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(comment.id)}
                            className="p-1 text-gray-400 hover:text-red-500"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
