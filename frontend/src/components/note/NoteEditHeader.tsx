import { ArrowLeft, Save, Send, Trash2, Pencil, X, Loader2 } from 'lucide-react';

interface NoteEditHeaderProps {
  isPublished: boolean;
  isEditing: boolean;
  hasChanges: boolean;
  saving: boolean;
  publishing: boolean;
  sourceMemoCount: number;
  onBack: () => void;
  onSave: () => void;
  onPublish: () => void;
  onDelete: () => void;
  onStartEditing: () => void;
  onCancelEditing: () => void;
}

export function NoteEditHeader({
  isPublished,
  isEditing,
  hasChanges,
  saving,
  publishing,
  sourceMemoCount,
  onBack,
  onSave,
  onPublish,
  onDelete,
  onStartEditing,
  onCancelEditing,
}: NoteEditHeaderProps) {
  return (
    <div className="flex-shrink-0 flex items-center justify-between px-2 md:px-4 py-2 md:py-3 border-b border-gray-100 gap-1">
      {/* 좌측: 뒤로가기 + 상태 */}
      <div className="flex items-center gap-1 md:gap-2 min-w-0">
        <button
          onClick={onBack}
          className="p-1.5 md:p-2 text-gray-500 hover:text-gray-700 flex-shrink-0"
        >
          <ArrowLeft size={18} className="md:w-5 md:h-5" />
        </button>
        <span
          className={`px-1.5 md:px-2 py-0.5 rounded text-[10px] md:text-xs font-medium flex-shrink-0 ${
            isPublished
              ? 'bg-green-100 text-green-700'
              : 'bg-amber-100 text-amber-700'
          }`}
        >
          {isPublished ? '발행됨' : '편집중'}
        </span>
        {sourceMemoCount > 0 && (
          <span className="hidden sm:flex items-center gap-1 text-[10px] md:text-xs text-gray-400 flex-shrink-0">
            {sourceMemoCount}개
          </span>
        )}
      </div>

      {/* 우측: 액션 버튼 */}
      <div className="flex items-center gap-1 md:gap-2 flex-shrink-0">
        <button
          onClick={onDelete}
          className="p-1.5 md:p-2 text-gray-400 hover:text-red-500"
        >
          <Trash2 size={16} className="md:w-[18px] md:h-[18px]" />
        </button>
        {/* 발행된 메모: 편집/취소 버튼 */}
        {isPublished && !isEditing && (
          <button
            onClick={onStartEditing}
            className="flex items-center gap-1 px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:border-gray-300"
          >
            <Pencil size={12} className="md:w-[14px] md:h-[14px]" />
            <span className="hidden sm:inline">편집</span>
          </button>
        )}
        {isPublished && isEditing && (
          <button
            onClick={onCancelEditing}
            className="flex items-center gap-1 px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm font-medium text-gray-500 border border-gray-200 rounded-lg hover:border-gray-300"
          >
            <X size={12} className="md:w-[14px] md:h-[14px]" />
            <span className="hidden sm:inline">취소</span>
          </button>
        )}
        {/* 편집중이거나 미발행 상태: 저장 버튼 */}
        {(!isPublished || isEditing) && (
          <button
            onClick={onSave}
            disabled={!hasChanges || saving}
            className="flex items-center gap-1 px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? (
              <Loader2 size={12} className="md:w-[14px] md:h-[14px] animate-spin" />
            ) : (
              <Save size={12} className="md:w-[14px] md:h-[14px]" />
            )}
            <span className="hidden sm:inline">저장</span>
          </button>
        )}
        {!isPublished && (
          <button
            onClick={onPublish}
            disabled={publishing}
            className="flex items-center gap-1 px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-600 disabled:opacity-50"
          >
            {publishing ? (
              <Loader2 size={12} className="md:w-[14px] md:h-[14px] animate-spin" />
            ) : (
              <Send size={12} className="md:w-[14px] md:h-[14px]" />
            )}
            <span className="hidden sm:inline">발행</span>
          </button>
        )}
      </div>
    </div>
  );
}
