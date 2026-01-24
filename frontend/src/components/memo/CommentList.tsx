import { useState, useEffect, useRef } from 'react';
import { Send, Trash2, Pencil, X, Check, Bot, User, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { useComments } from '../../hooks/useComments';
import { useAnalysisSSE, CommentAIResponseEvent } from '../../hooks/useAnalysisSSE';
import { useAuth } from '../../hooks/useAuth';
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

  const { user } = useAuth();
  const personas = user?.ai_personas || [];

  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  // 페르소나 자동완성 상태
  const [showPersonaDropdown, setShowPersonaDropdown] = useState(false);
  const [personaFilter, setPersonaFilter] = useState('');
  const [selectedPersonaIndex, setSelectedPersonaIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 필터링된 페르소나 목록
  const filteredPersonas = personas.filter((p) =>
    p.name.toLowerCase().includes(personaFilter.toLowerCase())
  );

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

  // 댓글 입력 변경 핸들러
  const handleCommentChange = (value: string) => {
    setNewComment(value);

    // @ 입력 감지
    const lastAtIndex = value.lastIndexOf('@');
    if (lastAtIndex !== -1 && personas.length > 0) {
      const afterAt = value.slice(lastAtIndex + 1);
      // @ 뒤에 공백이 없으면 자동완성 표시
      if (!afterAt.includes(' ')) {
        setPersonaFilter(afterAt);
        setShowPersonaDropdown(true);
        setSelectedPersonaIndex(0);
        return;
      }
    }
    setShowPersonaDropdown(false);
  };

  // 페르소나 선택 핸들러
  const handleSelectPersona = (personaName: string) => {
    const lastAtIndex = newComment.lastIndexOf('@');
    if (lastAtIndex !== -1) {
      const before = newComment.slice(0, lastAtIndex);
      setNewComment(`${before}@${personaName} `);
    }
    setShowPersonaDropdown(false);
    inputRef.current?.focus();
  };

  // 키보드 네비게이션
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (showPersonaDropdown && filteredPersonas.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedPersonaIndex((prev) =>
          prev < filteredPersonas.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedPersonaIndex((prev) =>
          prev > 0 ? prev - 1 : filteredPersonas.length - 1
        );
      } else if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        handleSelectPersona(filteredPersonas[selectedPersonaIndex].name);
      } else if (e.key === 'Escape') {
        setShowPersonaDropdown(false);
      }
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowPersonaDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="space-y-4">
      {/* 댓글 입력 */}
      <div className="relative flex gap-2">
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={newComment}
            onChange={(e) => handleCommentChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={personas.length > 0 ? "@페르소나로 AI 호출..." : "의견을 남겨보세요..."}
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary"
          />

          {/* 페르소나 자동완성 드롭다운 */}
          {showPersonaDropdown && filteredPersonas.length > 0 && (
            <div
              ref={dropdownRef}
              className="absolute left-0 right-0 bottom-full mb-1 bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden z-10"
            >
              {filteredPersonas.map((persona, index) => (
                <button
                  key={persona.name}
                  onClick={() => handleSelectPersona(persona.name)}
                  className={`w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-gray-50 ${
                    index === selectedPersonaIndex ? 'bg-gray-100' : ''
                  }`}
                >
                  <div
                    className="w-5 h-5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: persona.color || '#6366F1' }}
                  />
                  <div className="flex-1 min-w-0">
                    <span
                      className="text-sm font-medium"
                      style={{ color: persona.color || '#6366F1' }}
                    >
                      @{persona.name}
                    </span>
                    {persona.description && (
                      <p className="text-xs text-gray-400 truncate">
                        {persona.description}
                      </p>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
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
            const personaColor = comment.ai_persona_color || '#3B82F6';

            return (
              <div
                key={comment.id}
                className={`p-3 rounded-lg ${
                  isAI ? 'border' : 'bg-gray-50'
                }`}
                style={isAI ? {
                  backgroundColor: `${personaColor}10`,
                  borderColor: `${personaColor}30`
                } : undefined}
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
                          !isAI ? 'bg-gray-200 text-gray-500' : ''
                        }`}
                        style={isAI ? {
                          backgroundColor: `${personaColor}20`,
                          color: personaColor
                        } : undefined}
                      >
                        {isAI ? <Bot size={14} /> : <User size={14} />}
                      </div>
                      <div className="flex-1 min-w-0">
                        {isAI && comment.ai_persona_name && (
                          <p
                            className="text-xs font-bold mb-1"
                            style={{ color: personaColor }}
                          >
                            @{comment.ai_persona_name}
                          </p>
                        )}
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
                      <div className="flex items-center gap-1">
                        {!isAI && (
                          <button
                            onClick={() => startEdit(comment.id, comment.content)}
                            className="p-1 text-gray-400 hover:text-primary"
                          >
                            <Pencil size={14} />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(comment.id)}
                          className="p-1 text-gray-400 hover:text-red-500"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
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
