import { useState, useCallback } from 'react';
import { tempMemoApi } from '../api/client';
import type {
  TempMemo,
  TempMemoCreate,
  TempMemoUpdate,
  MemoType,
} from '../types/memo';

export function useTempMemos() {
  const [memos, setMemos] = useState<TempMemo[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        const message = err instanceof Error ? err.message : '메모를 불러오는데 실패했습니다.';
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
      const message = err instanceof Error ? err.message : '메모 저장에 실패했습니다.';
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
      const message = err instanceof Error ? err.message : '메모 수정에 실패했습니다.';
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
      const message = err instanceof Error ? err.message : '메모 삭제에 실패했습니다.';
      setError(message);
      throw err;
    }
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
  };
}
