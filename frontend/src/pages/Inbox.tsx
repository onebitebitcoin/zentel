import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { MemoCard } from '../components/memo/MemoCard';
import { MemoDetail } from '../components/memo/MemoDetail';
import { useTempMemos } from '../hooks/useTempMemos';
import type { MemoType, TempMemo, MemoTypeInfo } from '../types/memo';
import { MEMO_TYPES } from '../types/memo';

type FilterType = 'ALL' | MemoType;

export function Inbox() {
  const { memos, loading, fetchMemos, updateMemo, deleteMemo } = useTempMemos();
  const [filter, setFilter] = useState<FilterType>('ALL');
  const [editingMemo, setEditingMemo] = useState<TempMemo | null>(null);

  useEffect(() => {
    const type = filter === 'ALL' ? undefined : filter;
    fetchMemos(type);
  }, [filter, fetchMemos]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;

    try {
      await deleteMemo(id);
      toast.success('메모가 삭제되었습니다.');
    } catch {
      toast.error('삭제에 실패했습니다.');
    }
  };

  const handleSave = async (
    id: string,
    data: { memo_type?: MemoType; content?: string }
  ) => {
    try {
      await updateMemo(id, data);
      toast.success('메모가 수정되었습니다.');
    } catch {
      toast.error('수정에 실패했습니다.');
    }
  };

  const filters: { value: FilterType; label: string; info?: MemoTypeInfo }[] = [
    { value: 'ALL', label: '전체' },
    ...MEMO_TYPES.map((info) => ({
      value: info.type as FilterType,
      label: info.label,
      info,
    })),
  ];

  return (
    <div className="flex flex-col h-full">
      {/* 필터 탭 */}
      <div className="sticky top-14 z-10 bg-white border-b border-gray-100">
        <div className="flex overflow-x-auto px-2 py-2 gap-2 scrollbar-hide">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`flex-shrink-0 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                filter === f.value
                  ? f.info
                    ? `${f.info.bgColor} ${f.info.color}`
                    : 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* 메모 목록 */}
      <div className="flex-1 overflow-auto px-4 py-4 pb-24 space-y-3">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : memos.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-400">
            <p>저장된 메모가 없습니다.</p>
          </div>
        ) : (
          memos.map((memo) => (
            <MemoCard
              key={memo.id}
              memo={memo}
              onEdit={setEditingMemo}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>

      {/* 메모 상세/수정 모달 */}
      {editingMemo && (
        <MemoDetail
          memo={editingMemo}
          onClose={() => setEditingMemo(null)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
