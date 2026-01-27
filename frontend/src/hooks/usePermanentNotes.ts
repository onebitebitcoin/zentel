import { useState, useCallback, useRef } from 'react';
import { permanentNoteApi } from '../api/client';
import type {
  PermanentNote,
  PermanentNoteListItem,
  PermanentNoteCreate,
  PermanentNoteUpdate,
  NoteStatus,
} from '../types/note';

export function usePermanentNotes() {
  const [notes, setNotes] = useState<PermanentNoteListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 상세 정보 캐시
  const detailCacheRef = useRef<Map<string, PermanentNote>>(new Map());

  const fetchNotes = useCallback(
    async (status?: NoteStatus, limit = 20, offset = 0) => {
      setLoading(true);
      setError(null);
      try {
        const response = await permanentNoteApi.list({ status, limit, offset });
        if (offset === 0) {
          setNotes(response.items);
        } else {
          setNotes((prev) => [...prev, ...response.items]);
        }
        setTotal(response.total);
      } catch (err) {
        const message = err instanceof Error ? err.message : '영구 메모를 불러오는데 실패했습니다.';
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const createNote = useCallback(async (data: PermanentNoteCreate) => {
    setError(null);
    try {
      const newNote = await permanentNoteApi.create(data);
      // 캐시에 상세 정보 저장
      detailCacheRef.current.set(newNote.id, newNote);
      return newNote;
    } catch (err) {
      const message = err instanceof Error ? err.message : '영구 메모 생성에 실패했습니다.';
      setError(message);
      throw err;
    }
  }, []);

  const updateNote = useCallback(async (id: string, data: PermanentNoteUpdate) => {
    setError(null);
    try {
      const updated = await permanentNoteApi.update(id, data);
      // 목록 업데이트
      setNotes((prev) =>
        prev.map((n) =>
          n.id === id
            ? {
                ...n,
                title: updated.title,
                status: updated.status,
                interests: updated.interests,
                updated_at: updated.updated_at,
                published_at: updated.published_at,
              }
            : n
        )
      );
      // 캐시 업데이트
      detailCacheRef.current.set(id, updated);
      return updated;
    } catch (err) {
      const message = err instanceof Error ? err.message : '영구 메모 수정에 실패했습니다.';
      setError(message);
      throw err;
    }
  }, []);

  const deleteNote = useCallback(async (id: string) => {
    setError(null);
    try {
      await permanentNoteApi.delete(id);
      setNotes((prev) => prev.filter((n) => n.id !== id));
      setTotal((prev) => prev - 1);
      // 캐시에서 제거
      detailCacheRef.current.delete(id);
    } catch (err) {
      const message = err instanceof Error ? err.message : '영구 메모 삭제에 실패했습니다.';
      setError(message);
      throw err;
    }
  }, []);

  // 캐시에서 상세 정보 조회
  const getNoteDetail = useCallback((id: string): PermanentNote | undefined => {
    return detailCacheRef.current.get(id);
  }, []);

  // 상세 정보 가져오기 (캐시 확인 후 API 호출)
  const fetchNoteDetail = useCallback(async (id: string): Promise<PermanentNote | undefined> => {
    // 캐시에 있으면 반환
    const cached = detailCacheRef.current.get(id);
    if (cached) {
      return cached;
    }

    // API 호출
    try {
      const detail = await permanentNoteApi.get(id);
      detailCacheRef.current.set(id, detail);
      return detail;
    } catch (err) {
      console.error('영구 메모 상세 조회 실패:', err);
      return undefined;
    }
  }, []);

  // 캐시 초기화
  const clearDetailCache = useCallback(() => {
    detailCacheRef.current.clear();
  }, []);

  // 메모 목록 초기화
  const clearNotes = useCallback(() => {
    setNotes([]);
    setTotal(0);
  }, []);

  return {
    notes,
    total,
    loading,
    error,
    fetchNotes,
    createNote,
    updateNote,
    deleteNote,
    getNoteDetail,
    fetchNoteDetail,
    clearDetailCache,
    clearNotes,
  };
}
