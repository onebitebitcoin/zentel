import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, SlidersHorizontal } from 'lucide-react';
import toast from 'react-hot-toast';
import { MemoCard } from '../components/memo/MemoCard';
import rottenIcon from '../assets/images/rotten.png';
import { useTempMemos } from '../hooks/useTempMemos';
import { useAnalysisSSE } from '../hooks/useAnalysisSSE';
import type { MemoType, MemoTypeInfo } from '../types/memo';
import { MEMO_TYPES } from '../types/memo';

type FilterType = 'ALL' | MemoType;

export function Inbox() {
  const navigate = useNavigate();
  const { memos, total, loading, error, fetchMemos, deleteMemo, refreshMemo, getMemoDetail, fetchMemoDetail, clearDetailCache } = useTempMemos();
  const [filter, setFilter] = useState<FilterType>('ALL');
  const [offset, setOffset] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const limit = 10;

  // SSE 훅 먼저 초기화
  const { analysisLogs, clearLogs } = useAnalysisSSE(
    useCallback(
      async (memoId: string, status: string) => {
        console.log('[Inbox] Analysis complete:', memoId, status);
        // 해당 메모 새로고침
        await refreshMemo(memoId);
        if (status === 'completed') {
          toast.success('AI 분석이 완료되었습니다.');
        } else if (status === 'failed') {
          toast.error('AI 분석에 실패했습니다.');
        }
      },
      [refreshMemo]
    )
  );

  // 분석 완료 시 로그 정리를 위한 effect
  useEffect(() => {
    // 분석이 완료된 메모의 로그 정리
    memos.forEach((memo) => {
      if (memo.analysis_status === 'completed' || memo.analysis_status === 'failed') {
        if (analysisLogs[memo.id]) {
          clearLogs(memo.id);
        }
      }
    });
  }, [memos, analysisLogs, clearLogs]);

  useEffect(() => {
    const type = filter === 'ALL' ? undefined : filter;
    setOffset(0);
    clearDetailCache(); // 필터 변경 시 캐시 초기화
    fetchMemos(type, limit, 0);
  }, [filter, fetchMemos, clearDetailCache]);

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  const handleEdit = (memoId: string) => {
    navigate(`/memo/${memoId}`);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;

    try {
      await deleteMemo(id);
      toast.success('메모가 삭제되었습니다.');
    } catch {
      toast.error('삭제에 실패했습니다.');
    }
  };

  const handleCommentChange = async (memoId: string) => {
    await refreshMemo(memoId);
  };

  const handleReanalyze = async (memoId: string) => {
    await refreshMemo(memoId);
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
          <h1 className="flex items-center gap-2 text-xl font-semibold text-gray-800">
            <img src={rottenIcon} alt="임시 메모 목록" className="w-8 h-8" />
            임시 메모 목록
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
                onEdit={() => handleEdit(memo.id)}
                onDelete={handleDelete}
                onCommentChange={() => handleCommentChange(memo.id)}
                onReanalyze={handleReanalyze}
                analysisLogs={analysisLogs[memo.id]}
                cachedDetail={getMemoDetail(memo.id)}
                onFetchDetail={fetchMemoDetail}
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
    </div>
  );
}
