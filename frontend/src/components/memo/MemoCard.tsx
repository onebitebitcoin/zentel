import { Pencil, Trash2 } from 'lucide-react';
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

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span
          className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${typeInfo.bgColor} ${typeInfo.color}`}
        >
          {typeInfo.label}
        </span>
        <span className="text-xs text-gray-400">
          {getRelativeTime(memo.created_at)}
        </span>
      </div>

      <p className="text-sm text-gray-700 line-clamp-3 whitespace-pre-wrap">
        {memo.content}
      </p>

      <div className="flex items-center gap-4 pt-1">
        <button
          onClick={() => onEdit(memo)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary"
        >
          <Pencil size={14} />
          <span>Edit</span>
        </button>
        <button
          onClick={() => onDelete(memo.id)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-500"
        >
          <Trash2 size={14} />
          <span>Delete</span>
        </button>
      </div>
    </div>
  );
}
