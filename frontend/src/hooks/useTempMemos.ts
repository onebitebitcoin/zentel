import { useState, useCallback, useRef } from 'react';
import { tempMemoApi } from '../api/client';
import { getErrorMessage } from '../utils/error';
import type {
  TempMemo,
  TempMemoListItem,
  TempMemoCreate,
  TempMemoUpdate,
  MemoType,
} from '../types/memo';

export function useTempMemos() {
  const [memos, setMemos] = useState<TempMemoListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 상세 정보 캐시 (본문 데이터)
  const detailCacheRef = useRef<Map<string, TempMemo>>(new Map());

  const fetchMemos = useCallback(
    async (type?: MemoType, limit = 10, offset = 0) => {
      setLoading(true);
      setError(null);
      try {
        const response = await tempMemoApi.list({ type, limit, offset });
        if (offset === 0) {
          setMemos(response.items);
        } else {
          setMemos((prev) => [...prev, ...response.items]);
        }
        setTotal(response.total);
      } catch (err) {
        const message = getErrorMessage(err, '메모를 불러오는데 실패했습니다.');
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const createMemo = useCallback(async (data: TempMemoCreate) => {
    setError(null);
    try {
      const newMemo = await tempMemoApi.create(data);
      setMemos((prev) => [newMemo, ...prev]);
      setTotal((prev) => prev + 1);
      return newMemo;
    } catch (err) {
      const message = getErrorMessage(err, '메모 저장에 실패했습니다.');
      setError(message);
      throw err;
    }
  }, []);

  const updateMemo = useCallback(async (id: string, data: TempMemoUpdate) => {
    setError(null);
    try {
      const updated = await tempMemoApi.update(id, data);
      setMemos((prev) => prev.map((m) => (m.id === id ? updated : m)));
      return updated;
    } catch (err) {
      const message = getErrorMessage(err, '메모 수정에 실패했습니다.');
      setError(message);
      throw err;
    }
  }, []);

  const deleteMemo = useCallback(async (id: string) => {
    setError(null);
    try {
      await tempMemoApi.delete(id);
      setMemos((prev) => prev.filter((m) => m.id !== id));
      setTotal((prev) => prev - 1);
    } catch (err) {
      const message = getErrorMessage(err, '메모 삭제에 실패했습니다.');
      setError(message);
      throw err;
    }
  }, []);

  const refreshMemo = useCallback(async (id: string) => {
    try {
      const updated = await tempMemoApi.get(id);
      // 캐시에도 저장
      detailCacheRef.current.set(id, updated);
      // 목록 상태 업데이트 - 완전히 새 객체로 교체하여 React 리렌더링 보장
      setMemos((prev) =>
        prev.map((m) =>
          m.id === id
            ? {
                id: updated.id,
                memo_type: updated.memo_type,
                content: updated.content,
                context: updated.context,
                summary: updated.summary,
                interests: updated.interests,
                source_url: updated.source_url,
                og_title: updated.og_title,
                og_image: updated.og_image,
                fetch_failed: updated.fetch_failed,
                fetch_message: updated.fetch_message,
                analysis_status: updated.analysis_status,
                analysis_error: updated.analysis_error,
                original_language: updated.original_language,
                is_summary: updated.is_summary,
                has_display_content: Boolean(updated.display_content),
                translated_content: updated.translated_content,
                display_content: updated.display_content,
                highlights: updated.highlights,
                created_at: updated.created_at,
                updated_at: updated.updated_at,
                comment_count: updated.comment_count,
                latest_comment: updated.latest_comment,
              }
            : m
        )
      );
      return updated;
    } catch (err) {
      console.error('메모 새로고침 실패:', err);
      return undefined;
    }
  }, []);

  // 캐시에서 상세 정보 조회
  const getMemoDetail = useCallback((id: string): TempMemo | undefined => {
    return detailCacheRef.current.get(id);
  }, []);

  // 상세 정보 가져오기 (캐시 확인 후 API 호출)
  const fetchMemoDetail = useCallback(async (id: string): Promise<TempMemo | undefined> => {
    // 캐시에 있으면 반환
    const cached = detailCacheRef.current.get(id);
    if (cached) {
      return cached;
    }

    // API 호출
    try {
      const detail = await tempMemoApi.get(id);
      detailCacheRef.current.set(id, detail);
      return detail;
    } catch (err) {
      console.error('메모 상세 조회 실패:', err);
      return undefined;
    }
  }, []);

  // 캐시 초기화 (필터 변경 등에 사용)
  const clearDetailCache = useCallback(() => {
    detailCacheRef.current.clear();
  }, []);

  // 메모 목록 초기화 (필터 변경 시 사용)
  const clearMemos = useCallback(() => {
    setMemos([]);
    setTotal(0);
  }, []);

  return {
    memos,
    total,
    loading,
    error,
    fetchMemos,
    createMemo,
    updateMemo,
    deleteMemo,
    refreshMemo,
    getMemoDetail,
    fetchMemoDetail,
    clearDetailCache,
    clearMemos,
  };
}
