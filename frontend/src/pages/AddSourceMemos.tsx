import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Check, Loader2, Plus, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { MemoCard } from '../components/memo/MemoCard';
import { useTempMemos } from '../hooks/useTempMemos';
import { permanentNoteApi } from '../api/client';
import type { PermanentNote } from '../types/note';

export function AddSourceMemos() {
  const navigate = useNavigate();
  const { id: noteId } = useParams<{ id: string }>();
  const { memos, total, loading, error, fetchMemos, clearMemos } = useTempMemos();

  const [note, setNote] = useState<PermanentNote | null>(null);
  const [noteLoading, setNoteLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [adding, setAdding] = useState(false);
  const [offset, setOffset] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const limit = 20;

  // 영구 메모 정보 로드
  useEffect(() => {
    if (!noteId) return;

    const fetchNote = async () => {
      setNoteLoading(true);
      try {
        const data = await permanentNoteApi.get(noteId);
        setNote(data);
      } catch {
        toast.error('영구 메모를 불러오는데 실패했습니다.');
        navigate('/notes');
      } finally {
        setNoteLoading(false);
      }
    };

    fetchNote();
  }, [noteId, navigate]);

  // 임시 메모 목록 로드
  useEffect(() => {
    setOffset(0);
    clearMemos();
    fetchMemos(undefined, limit, 0);
  }, [fetchMemos, clearMemos]);

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  // 메모 선택 토글
  const handleToggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  // 전체 선택/해제 (이미 추가된 메모 제외)
  const handleSelectAll = useCallback(() => {
    if (!note) return;
    const existingIds = new Set(note.source_memo_ids || []);
    const selectableMemos = memos.filter((m) => !existingIds.has(m.id));

    if (selectedIds.size === selectableMemos.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(selectableMemos.map((m) => m.id)));
    }
  }, [memos, note, selectedIds.size]);

  // 더보기
  const handleLoadMore = async () => {
    if (loading || loadingMore) return;
    const nextOffset = offset + limit;
    if (nextOffset >= total) return;

    setLoadingMore(true);
    try {
      await fetchMemos(undefined, limit, nextOffset);
      setOffset(nextOffset);
    } finally {
      setLoadingMore(false);
    }
  };

  // 추가하기
  const handleAdd = async () => {
    if (!noteId || selectedIds.size === 0) return;

    setAdding(true);
    try {
      await permanentNoteApi.update(noteId, {
        add_source_memo_ids: Array.from(selectedIds),
      });
      toast.success(`${selectedIds.size}개의 메모가 추가되었습니다.`);
      navigate(`/notes/${noteId}`);
    } catch {
      toast.error('메모 추가에 실패했습니다.');
    } finally {
      setAdding(false);
    }
  };

  // 취소
  const handleCancel = () => {
    navigate(`/notes/${noteId}`);
  };

  const hasMore = memos.length < total;
  const existingIds = new Set(note?.source_memo_ids || []);
  const selectableMemos = memos.filter((m) => !existingIds.has(m.id));

  if (noteLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-2 md:px-4 py-2 md:py-3 border-b border-gray-100 bg-primary text-white">
        <div className="flex items-center gap-2 md:gap-3">
          <button
            onClick={handleCancel}
            className="p-1.5 hover:bg-white/20 rounded"
          >
            <X size={20} />
          </button>
          <span className="text-sm font-medium">
            {selectedIds.size}개 선택됨
          </span>
          {selectableMemos.length > 0 && (
            <button
              onClick={handleSelectAll}
              className="text-xs underline hover:no-underline"
            >
              {selectedIds.size === selectableMemos.length ? '전체 해제' : '전체 선택'}
            </button>
          )}
        </div>
        <button
          onClick={handleAdd}
          disabled={selectedIds.size === 0 || adding}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white text-primary rounded-lg text-sm font-medium disabled:opacity-50"
        >
          {adding ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Plus size={16} />
          )}
          추가하기
        </button>
      </div>

      {/* 안내 메시지 */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
        <p className="text-sm text-gray-600">
          <span className="font-medium">{note?.title}</span>에 추가할 임시 메모를 선택하세요.
        </p>
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
            {memos.map((memo) => {
              const isAlreadyAdded = existingIds.has(memo.id);
              const isSelected = selectedIds.has(memo.id);

              return (
                <div key={memo.id} className="relative">
                  {/* 이미 추가된 메모 오버레이 */}
                  {isAlreadyAdded && (
                    <div className="absolute inset-0 bg-white/60 z-10 rounded-xl flex items-center justify-center">
                      <span className="flex items-center gap-1.5 px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                        <Check size={14} />
                        이미 추가됨
                      </span>
                    </div>
                  )}
                  <MemoCard
                    memo={memo}
                    onEdit={() => {}}
                    onDelete={() => {}}
                    onCommentChange={() => {}}
                    onReanalyze={() => {}}
                    selectionMode={true}
                    isSelected={isSelected}
                    onToggleSelect={isAlreadyAdded ? undefined : handleToggleSelect}
                  />
                </div>
              );
            })}
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
