import { Pencil, Trash2, Sparkles, ExternalLink } from 'lucide-react';
import type { TempMemo } from '../../types/memo';
import { getMemoTypeInfo } from '../../types/memo';
import { getRelativeTime } from '../../utils/date';

interface MemoCardProps {
  memo: TempMemo;
  onEdit: (memo: TempMemo) => void;
  onDelete: (id: string) => void;
}

export function MemoCard({ memo, onEdit, onDelete }: MemoCardProps) {
  const typeInfo = getMemoTypeInfo(memo.memo_type);

  // 첫 줄을 제목으로 추출
  const lines = memo.content.split('\n');
  const title = lines[0].slice(0, 80);
  const body = lines.length > 1 ? lines.slice(1).join('\n').trim() : '';

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 md:p-6 space-y-3 md:space-y-4">
      {/* 타입 태그 */}
      <div className="flex items-center gap-2">
        <span
          className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium uppercase tracking-wide ${typeInfo.bgColor} ${typeInfo.color}`}
        >
          {typeInfo.label}
        </span>
      </div>

      {/* 제목 (PC에서 더 크게) */}
      <h3 className="text-sm md:text-base font-semibold text-gray-800 line-clamp-2">
        {title}
      </h3>

      {/* 본문 */}
      {body && (
        <p className="text-sm text-gray-600 line-clamp-3 md:line-clamp-4 whitespace-pre-wrap">
          {body}
        </p>
      )}

      {/* AI Context */}
      {memo.context && (
        <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg">
          <Sparkles size={14} className="text-blue-500 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-blue-700 line-clamp-2">{memo.context}</p>
        </div>
      )}

      {/* 외부 링크 */}
      {memo.source_url && (
        <a
          href={memo.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-teal-600 hover:text-teal-700 hover:underline"
        >
          <ExternalLink size={12} />
          <span className="truncate max-w-[200px]">{memo.source_url}</span>
        </a>
      )}

      {/* 메타 정보 */}
      <div className="flex items-center justify-between pt-1 md:pt-2">
        <div className="flex items-center gap-4">
          <button
            onClick={() => onEdit(memo)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary"
          >
            <Pencil size={14} />
            <span>수정</span>
          </button>
          <button
            onClick={() => onDelete(memo.id)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-500"
          >
            <Trash2 size={14} />
            <span>삭제</span>
          </button>
        </div>
        <span className="hidden md:block text-xs text-primary tracking-wide">
          수정됨 {getRelativeTime(memo.created_at)}
        </span>
        <span className="md:hidden text-xs text-gray-400">
          {getRelativeTime(memo.created_at)}
        </span>
      </div>
    </div>
  );
}
