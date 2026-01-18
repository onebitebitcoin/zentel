import { useState } from 'react';
import { X, Check, Sparkles, ExternalLink } from 'lucide-react';
import type { TempMemo, MemoType } from '../../types/memo';
import { MemoTypeChips } from './MemoTypeChips';
import { formatDateTime } from '../../utils/date';

interface MemoDetailProps {
  memo: TempMemo;
  onClose: () => void;
  onSave: (id: string, data: { memo_type?: MemoType; content?: string }) => void;
}

export function MemoDetail({ memo, onClose, onSave }: MemoDetailProps) {
  const [memoType, setMemoType] = useState<MemoType>(memo.memo_type);
  const [content, setContent] = useState(memo.content);
  const [saving, setSaving] = useState(false);

  const hasChanges = memoType !== memo.memo_type || content !== memo.content;

  const handleSave = async () => {
    if (!hasChanges || saving) return;

    setSaving(true);
    try {
      const updates: { memo_type?: MemoType; content?: string } = {};
      if (memoType !== memo.memo_type) updates.memo_type = memoType;
      if (content !== memo.content) updates.content = content;

      await onSave(memo.id, updates);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="relative w-full max-w-lg bg-white rounded-t-2xl sm:rounded-2xl max-h-[90vh] overflow-auto">
        <div className="sticky top-0 flex items-center justify-between px-4 py-3 border-b bg-white">
          <button onClick={onClose} className="p-2 text-gray-500">
            <X size={20} />
          </button>
          <span className="text-sm font-medium">메모 수정</span>
          <button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className={`p-2 ${hasChanges ? 'text-primary' : 'text-gray-300'}`}
          >
            <Check size={20} />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <MemoTypeChips selectedType={memoType} onSelect={setMemoType} />

          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full h-48 p-4 text-base text-gray-800 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary/30"
          />

          {/* Context */}
          {memo.context && (
            <div className="p-4 bg-gray-50 rounded-xl space-y-1">
              <div className="flex items-center gap-2">
                <Sparkles size={14} className="text-gray-500" />
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Context</span>
              </div>
              <p className="text-sm text-gray-700">{memo.context}</p>
            </div>
          )}

          {/* 외부 링크 프리뷰 */}
          {memo.source_url && (
            <a
              href={memo.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-xl overflow-hidden border border-gray-200 hover:border-gray-300 transition-colors"
            >
              {memo.og_image ? (
                <div className="flex flex-col">
                  <div className="w-full h-32 bg-gray-100">
                    <img
                      src={memo.og_image}
                      alt=""
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  </div>
                  <div className="p-3">
                    <p className="text-sm font-medium text-gray-800 line-clamp-2">
                      {memo.og_title || memo.source_url}
                    </p>
                    <p className="text-xs text-gray-400 truncate mt-1">
                      {new URL(memo.source_url).hostname}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3 p-3">
                  <ExternalLink size={18} className="text-teal-600 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-teal-600 truncate">
                      {memo.og_title || memo.source_url}
                    </p>
                  </div>
                </div>
              )}
            </a>
          )}

          <div className="text-xs text-gray-400">
            <p>생성: {formatDateTime(memo.created_at)}</p>
            {memo.updated_at && <p>수정: {formatDateTime(memo.updated_at)}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
