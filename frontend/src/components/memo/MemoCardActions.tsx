/**
 * 메모 카드 - 하단 액션 버튼 컴포넌트
 */
import { Copy, MessageCircle, Pencil, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import toast from 'react-hot-toast';
import { getRelativeTime } from '../../utils/date';

interface MemoCardActionsProps {
  memoId: string;
  content: string;
  commentCount: number;
  createdAt: string;
  commentsExpanded: boolean;
  onToggleComments: () => void;
  onEdit: () => void;
  onDelete: (id: string) => void;
}

export function MemoCardActions({
  memoId,
  content,
  commentCount,
  createdAt,
  commentsExpanded,
  onToggleComments,
  onEdit,
  onDelete,
}: MemoCardActionsProps) {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('메모가 복사되었습니다.');
    } catch {
      toast.error('복사에 실패했습니다.');
    }
  };

  return (
    <div className="flex items-center justify-between pt-1 md:pt-2">
      <div className="flex items-center gap-4">
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary"
        >
          <Copy size={14} />
          <span>복사</span>
        </button>
        <button
          onClick={onToggleComments}
          className={`flex items-center gap-1 text-xs ${commentsExpanded ? 'text-primary' : 'text-gray-500'} hover:text-primary`}
        >
          <MessageCircle size={14} />
          <span>{commentCount || 0}</span>
          {commentsExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>
        <button
          onClick={onEdit}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary"
        >
          <Pencil size={14} />
          <span>수정</span>
        </button>
        <button
          onClick={() => onDelete(memoId)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-500"
        >
          <Trash2 size={14} />
          <span>삭제</span>
        </button>
      </div>
      <span className="hidden md:block text-xs text-primary tracking-wide">
        수정됨 {getRelativeTime(createdAt)}
      </span>
      <span className="md:hidden text-xs text-gray-400">
        {getRelativeTime(createdAt)}
      </span>
    </div>
  );
}
