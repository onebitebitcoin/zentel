import { useState, useEffect } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import toast from 'react-hot-toast';
import { MemoCard } from '../components/memo/MemoCard';
import { MemoDetail } from '../components/memo/MemoDetail';
import { useTempMemos } from '../hooks/useTempMemos';
import type { MemoType, TempMemo, MemoTypeInfo } from '../types/memo';
import { MEMO_TYPES } from '../types/memo';

type FilterType = 'ALL' | MemoType;

export function Inbox() {
  const { memos, total, loading, error, fetchMemos, updateMemo, deleteMemo } = useTempMemos();
  const [filter, setFilter] = useState<FilterType>('ALL');
  const [editingMemo, setEditingMemo] = useState<TempMemo | null>(null);
  const [offset, setOffset] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const limit = 10;

  useEffect(() => {
    const type = filter === 'ALL' ? undefined : filter;
    setOffset(0);
    fetchMemos(type, limit, 0);
  }, [filter, fetchMemos]);

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

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

  const handleLoadMore = async () => {
    if (loading || loadingMore) return;
    const nextOffset = offset + limit;
    if (nextOffset >= total) return;

    setLoadingMore(true);
    try {
      const type = filter === 'ALL' ? undefined : filter;
      await fetchMemos(type, limit, nextOffset);
      setOffset(nextOffset);
    } finally {
      setLoadingMore(false);
    }
  };

  const hasMore = memos.length < total;

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
      {/* PC: 상단 헤더 */}
      <div className="hidden md:flex items-center justify-between px-6 py-5 bg-white border-b border-gray-100">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-gray-800">
            임시 메모
          </h1>
          <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs font-medium rounded">
            총 {total}개
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              placeholder="메모 검색..."
              className="w-64 pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-primary"
              disabled
            />
          </div>
          <button
            disabled
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-400"
          >
            <SlidersHorizontal size={16} />
            필터
          </button>
        </div>
      </div>

      {/* 모바일: 필터 탭 */}
      <div className="md:hidden bg-white border-b border-gray-100">
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
      <div className="flex-1 overflow-auto px-4 md:px-6 py-4 pb-24 md:pb-6 space-y-3 md:space-y-4">
        {loading && memos.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : memos.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-400">
            <p>저장된 메모가 없습니다.</p>
          </div>
        ) : (
          <>
            {memos.map((memo) => (
              <MemoCard
                key={memo.id}
                memo={memo}
                onEdit={setEditingMemo}
                onDelete={handleDelete}
              />
            ))}
            {hasMore && (
              <button
                type="button"
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="w-full py-3 text-sm font-medium text-primary border border-gray-200 rounded-xl bg-white hover:border-primary/40 disabled:opacity-50"
              >
                {loadingMore ? '불러오는 중...' : '더보기'}
              </button>
            )}
          </>
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
