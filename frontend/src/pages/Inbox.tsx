import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, SlidersHorizontal, CheckSquare, X, ArrowUpRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { MemoCard } from '../components/memo/MemoCard';
import rottenIcon from '../assets/images/rotten.png';
import { useTempMemos } from '../hooks/useTempMemos';
import { useAnalysisSSE } from '../hooks/useAnalysisSSE';
import type { MemoType, MemoTypeInfo } from '../types/memo';
import { MEMO_TYPES } from '../types/memo';

type FilterType = 'ALL' | MemoType;

const SCROLL_POSITION_KEY = 'inbox-scroll-position';

export function Inbox() {
  const navigate = useNavigate();
  const { memos, total, loading, error, fetchMemos, deleteMemo, refreshMemo, clearMemos } = useTempMemos();
  const [filter, setFilter] = useState<FilterType>('ALL');
  const [offset, setOffset] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const limit = 20;
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // 선택 모드 상태
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

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
    clearMemos(); // 필터 변경 시 메모 목록 초기화 (로딩 스피너 표시용)
    fetchMemos(type, limit, 0);
  }, [filter, fetchMemos, clearMemos]);

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  // 스크롤 위치 복원
  useEffect(() => {
    const savedPosition = sessionStorage.getItem(SCROLL_POSITION_KEY);
    if (savedPosition && scrollContainerRef.current && memos.length > 0) {
      // 메모가 로드된 후 스크롤 위치 복원
      setTimeout(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollTop = parseInt(savedPosition, 10);
        }
      }, 0);
    }
  }, [memos]);

  // 페이지 언마운트 시 스크롤 위치 저장
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current;
    return () => {
      if (scrollContainer) {
        sessionStorage.setItem(
          SCROLL_POSITION_KEY,
          scrollContainer.scrollTop.toString()
        );
      }
    };
  }, []);

  const handleEdit = (memoId: string) => {
    // 편집 페이지로 이동하기 전 스크롤 위치 저장
    if (scrollContainerRef.current) {
      sessionStorage.setItem(
        SCROLL_POSITION_KEY,
        scrollContainerRef.current.scrollTop.toString()
      );
    }
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

  // 선택 모드 토글
  const handleToggleSelectionMode = () => {
    if (selectionMode) {
      // 선택 모드 종료 시 상태 초기화
      setSelectedIds(new Set());
    }
    setSelectionMode(!selectionMode);
  };

  // 메모 선택 토글
  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // 전체 선택/해제
  const handleSelectAll = () => {
    if (selectedIds.size === memos.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(memos.map((m) => m.id)));
    }
  };

  // 발전시키기 (분석 페이지로 이동)
  const handleDevelopNote = () => {
    if (selectedIds.size === 0) {
      toast.error('메모를 선택해주세요.');
      return;
    }

    // 선택 모드 종료 및 분석 페이지로 이동
    const sourceMemoIds = Array.from(selectedIds);
    setSelectionMode(false);
    setSelectedIds(new Set());
    navigate('/notes/develop', { state: { sourceMemoIds } });
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
      {/* 선택 모드 상단 바 */}
      {selectionMode && (
        <div className="flex items-center justify-between px-4 py-3 bg-primary text-white">
          <div className="flex items-center gap-3">
            <button
              onClick={handleToggleSelectionMode}
              className="p-1 hover:bg-white/20 rounded"
            >
              <X size={20} />
            </button>
            <span className="text-sm font-medium">
              {selectedIds.size}개 선택됨
            </span>
            <button
              onClick={handleSelectAll}
              className="text-xs underline hover:no-underline"
            >
              {selectedIds.size === memos.length ? '전체 해제' : '전체 선택'}
            </button>
          </div>
          <button
            onClick={handleDevelopNote}
            disabled={selectedIds.size === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white text-primary rounded-lg text-sm font-medium disabled:opacity-50"
          >
            <ArrowUpRight size={16} />
            발전시키기
          </button>
        </div>
      )}

      {/* PC: 상단 헤더 */}
      {!selectionMode && (
        <div className="hidden md:flex items-center justify-between px-6 py-5 bg-white border-b border-gray-100">
          <div className="flex items-center gap-3">
            <h1 className="flex items-center gap-2 text-xl font-semibold text-gray-800">
              <img src={rottenIcon} alt="임시 메모 목록" className="w-10 h-10" />
              임시 메모 목록
            </h1>
            <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs font-medium rounded">
              총 {total}개
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleToggleSelectionMode}
              className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:border-primary hover:text-primary transition-colors"
            >
              <CheckSquare size={16} />
              선택
            </button>
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
      )}

      {/* 모바일: 필터 탭 + 선택 버튼 */}
      {!selectionMode && (
        <div className="md:hidden bg-white border-b border-gray-100">
          <div className="flex items-center px-2 py-2 gap-2">
            <div className="flex-1 flex overflow-x-auto gap-2 scrollbar-hide">
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
            <button
              onClick={handleToggleSelectionMode}
              className="flex-shrink-0 p-2 text-gray-500 hover:text-primary"
            >
              <CheckSquare size={20} />
            </button>
          </div>
        </div>
      )}

      {/* 메모 목록 */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-auto px-4 md:px-6 py-4 pb-24 md:pb-6 space-y-3 md:space-y-4"
      >
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
                selectionMode={selectionMode}
                isSelected={selectedIds.has(memo.id)}
                onToggleSelect={handleToggleSelect}
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
