import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, FileText, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';
import { usePermanentNotes } from '../hooks/usePermanentNotes';
import type { NoteStatus, PermanentNoteListItem } from '../types/note';
import { getRelativeTime } from '../utils/date';

type FilterType = 'ALL' | NoteStatus;

interface NoteCardProps {
  note: PermanentNoteListItem;
  onClick: () => void;
}

function NoteCard({ note, onClick }: NoteCardProps) {
  const isPublished = note.status === 'published';

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white rounded-xl border border-gray-100 p-4 md:p-5 space-y-2 hover:border-gray-200 transition-colors"
    >
      {/* 상태 + 출처 수 */}
      <div className="flex items-center justify-between">
        <span
          className={`px-2 py-0.5 rounded text-xs font-medium ${
            isPublished
              ? 'bg-green-100 text-green-700'
              : 'bg-amber-100 text-amber-700'
          }`}
        >
          {isPublished ? '발행됨' : '편집중'}
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-400">
          <FileText size={12} />
          출처 {note.source_memo_count}개
        </span>
      </div>

      {/* 제목 */}
      <h3 className="text-sm md:text-base font-semibold text-gray-800 line-clamp-2">
        {note.title}
      </h3>

      {/* 관심사 태그 */}
      {note.interests && note.interests.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {note.interests.slice(0, 3).map((interest) => (
            <span
              key={interest}
              className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-primary/10 text-primary"
            >
              {interest}
            </span>
          ))}
          {note.interests.length > 3 && (
            <span className="text-[10px] text-gray-400">
              +{note.interests.length - 3}
            </span>
          )}
        </div>
      )}

      {/* 날짜 */}
      <div className="flex items-center gap-1 text-xs text-gray-400">
        <Calendar size={12} />
        <span>{getRelativeTime(note.updated_at || note.created_at)}</span>
        {note.published_at && (
          <span className="text-green-500">
            (발행: {getRelativeTime(note.published_at)})
          </span>
        )}
      </div>
    </button>
  );
}

export function Notes() {
  const navigate = useNavigate();
  const { notes, total, loading, error, fetchNotes, clearNotes } = usePermanentNotes();
  const [filter, setFilter] = useState<FilterType>('ALL');
  const [offset, setOffset] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const limit = 20;

  useEffect(() => {
    const status = filter === 'ALL' ? undefined : filter;
    setOffset(0);
    clearNotes();
    fetchNotes(status, limit, 0);
  }, [filter, fetchNotes, clearNotes]);

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  const handleLoadMore = async () => {
    if (loading || loadingMore) return;
    const nextOffset = offset + limit;
    if (nextOffset >= total) return;

    setLoadingMore(true);
    try {
      const status = filter === 'ALL' ? undefined : filter;
      await fetchNotes(status, limit, nextOffset);
      setOffset(nextOffset);
    } finally {
      setLoadingMore(false);
    }
  };

  const hasMore = notes.length < total;

  const filters: { value: FilterType; label: string }[] = [
    { value: 'ALL', label: '전체' },
    { value: 'editing', label: '편집중' },
    { value: 'published', label: '발행됨' },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* PC: 상단 헤더 */}
      <div className="hidden md:flex items-center justify-between px-6 py-5 bg-white border-b border-gray-100">
        <div className="flex items-center gap-3">
          <h1 className="flex items-center gap-2 text-xl font-semibold text-gray-800">
            <BookOpen size={24} className="text-primary" />
            영구 메모
          </h1>
          <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs font-medium rounded">
            총 {total}개
          </span>
        </div>
        <div className="flex items-center gap-2">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                filter === f.value
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* 모바일: 필터 탭 */}
      <div className="md:hidden bg-white border-b border-gray-100">
        <div className="flex px-2 py-2 gap-2">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`flex-1 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                filter === f.value
                  ? 'bg-primary text-white'
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
        {loading && notes.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : notes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-400">
            <BookOpen size={48} className="mb-3 opacity-50" />
            <p>영구 메모가 없습니다.</p>
            <p className="text-sm mt-1">임시 메모에서 발전시켜 보세요.</p>
          </div>
        ) : (
          <>
            {notes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                onClick={() => navigate(`/notes/${note.id}`)}
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
