/**
 * 개별 댓글 컴포넌트
 */
import { useState } from 'react';
import { Trash2, Pencil, X, Check, Bot, User, Loader2 } from 'lucide-react';
import type { MemoComment } from '../../types/comment';
import { getRelativeTime } from '../../utils/date';

interface CommentItemProps {
  comment: MemoComment;
  isWaiting: boolean;
  onUpdate: (id: string, content: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function CommentItem({ comment, isWaiting, onUpdate, onDelete }: CommentItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');

  const isAI = comment.is_ai_response;
  const personaColor = comment.ai_persona_color || '#3B82F6';

  const startEdit = () => {
    setIsEditing(true);
    setEditContent(comment.content);
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setEditContent('');
  };

  const handleUpdate = async () => {
    if (!editContent.trim()) return;
    await onUpdate(comment.id, editContent.trim());
    setIsEditing(false);
    setEditContent('');
  };

  return (
    <div
      className={`p-3 rounded-lg ${isAI ? 'border' : 'bg-gray-50'}`}
      style={isAI ? {
        backgroundColor: `${personaColor}10`,
        borderColor: `${personaColor}30`
      } : undefined}
    >
      {isEditing ? (
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
              onClick={handleUpdate}
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
                  onClick={startEdit}
                  className="p-1 text-gray-400 hover:text-primary"
                >
                  <Pencil size={14} />
                </button>
              )}
              <button
                onClick={() => onDelete(comment.id)}
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
}
