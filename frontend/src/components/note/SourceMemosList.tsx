import { FileText, ChevronDown, ChevronUp, Plus, X, ExternalLink, Loader2 } from 'lucide-react';
import type { SourceMemoDetail } from '../../types/note';

interface SourceMemosListProps {
  sourceMemoIds: string[];
  sourceMemos: SourceMemoDetail[];
  expanded: boolean;
  loading: boolean;
  removingMemoId: string | null;
  noteId: string;
  onToggle: () => void;
  onLoadSummary: (memo: SourceMemoDetail) => void;
  onLoadAllSummaries: () => void;
  onRemoveMemo: (memoId: string) => void;
  onAddMemos: () => void;
}

export function SourceMemosList({
  sourceMemoIds,
  sourceMemos,
  expanded,
  loading,
  removingMemoId,
  onToggle,
  onLoadSummary,
  onLoadAllSummaries,
  onRemoveMemo,
  onAddMemos,
}: SourceMemosListProps) {
  if (!sourceMemoIds || sourceMemoIds.length === 0) {
    return (
      <div className="pt-4 border-t border-gray-100">
        <button
          onClick={onAddMemos}
          className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 border border-dashed border-gray-300 rounded-lg hover:border-primary hover:text-primary transition-colors w-full justify-center"
        >
          <Plus size={14} />
          임시 메모 추가
        </button>
      </div>
    );
  }

  return (
    <div className="pt-4 border-t border-gray-100">
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100"
        >
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-gray-500" />
            <span className="text-sm font-medium text-gray-700">
              출처 메모 {sourceMemoIds.length}개
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onLoadAllSummaries();
              }}
              className="flex items-center gap-1 px-2 py-1 text-xs text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
              title="모든 출처 메모의 요약을 본문에 추가"
            >
              <FileText size={12} />
              전체 불러오기
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAddMemos();
              }}
              className="flex items-center gap-1 px-2 py-1 text-xs text-primary hover:bg-primary/10 rounded-lg transition-colors"
            >
              <Plus size={12} />
              추가
            </button>
            {loading ? (
              <Loader2 size={16} className="text-gray-400 animate-spin" />
            ) : expanded ? (
              <ChevronUp size={16} className="text-gray-400" />
            ) : (
              <ChevronDown size={16} className="text-gray-400" />
            )}
          </div>
        </button>
        {expanded && (
          <div className="p-4 space-y-3 bg-white max-h-96 overflow-y-auto overflow-x-hidden">
            {loading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 size={20} className="animate-spin text-gray-400" />
              </div>
            ) : sourceMemos.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                출처 메모가 없습니다.
              </p>
            ) : (
              sourceMemos.map((memo, index) => (
                <SourceMemoItem
                  key={memo.id}
                  memo={memo}
                  index={index}
                  removingMemoId={removingMemoId}
                  onLoadSummary={onLoadSummary}
                  onRemove={onRemoveMemo}
                />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface SourceMemoItemProps {
  memo: SourceMemoDetail;
  index: number;
  removingMemoId: string | null;
  onLoadSummary: (memo: SourceMemoDetail) => void;
  onRemove: (memoId: string) => void;
}

function SourceMemoItem({
  memo,
  index,
  removingMemoId,
  onLoadSummary,
  onRemove,
}: SourceMemoItemProps) {
  return (
    <div className="p-3 bg-gray-50 rounded-lg space-y-2 overflow-hidden min-w-0">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {memo.og_title && (
            <p className="text-xs font-medium text-gray-700 truncate mb-1">
              {memo.og_title}
            </p>
          )}
          {memo.context && (
            <p
              className="text-xs text-primary font-medium mb-1"
              style={{ wordBreak: 'break-all', overflowWrap: 'anywhere' }}
            >
              {memo.context}
            </p>
          )}
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className="text-[10px] text-gray-400">#{index + 1}</span>
          {memo.summary && (
            <button
              onClick={() => onLoadSummary(memo)}
              className="p-1 text-gray-400 hover:text-teal-600 hover:bg-teal-50 rounded transition-colors"
              title="이 메모의 요약을 본문에 추가"
            >
              <FileText size={12} />
            </button>
          )}
          <button
            onClick={() => onRemove(memo.id)}
            disabled={removingMemoId === memo.id}
            className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
            title="출처 메모 제거"
          >
            {removingMemoId === memo.id ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <X size={12} />
            )}
          </button>
        </div>
      </div>
      {/* 요약 또는 본문 */}
      <div
        className="text-sm text-gray-600 line-clamp-4"
        style={{
          wordBreak: 'break-all',
          overflowWrap: 'anywhere',
          whiteSpace: 'pre-wrap',
          overflow: 'hidden',
        }}
      >
        {memo.summary || memo.content}
      </div>
      {/* 메타 정보 */}
      <div className="flex items-center gap-2 pt-1">
        {memo.source_url && (
          <a
            href={memo.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-primary"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink size={10} />
            원본
          </a>
        )}
        {memo.interests && memo.interests.length > 0 && (
          <div className="flex gap-1 flex-wrap">
            {memo.interests.slice(0, 2).map((interest) => (
              <span
                key={interest}
                className="px-1.5 py-0.5 text-[10px] bg-primary/10 text-primary rounded"
              >
                {interest}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
