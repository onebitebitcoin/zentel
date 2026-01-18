import axios from 'axios';
import type {
  TempMemo,
  TempMemoCreate,
  TempMemoListResponse,
  TempMemoUpdate,
  MemoType,
} from '../types/memo';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Trailing slash 제거 인터셉터
api.interceptors.request.use((config) => {
  if (config.url && config.url.endsWith('/')) {
    config.url = config.url.slice(0, -1);
  }
  return config;
});

export const tempMemoApi = {
  /**
   * 임시 메모 생성
   */
  create: async (data: TempMemoCreate): Promise<TempMemo> => {
    const response = await api.post<TempMemo>('/temp-memos', data);
    return response.data;
  },

  /**
   * 임시 메모 목록 조회
   */
  list: async (params?: {
    type?: MemoType;
    limit?: number;
    offset?: number;
  }): Promise<TempMemoListResponse> => {
    const response = await api.get<TempMemoListResponse>('/temp-memos', {
      params,
    });
    return response.data;
  },

  /**
   * 임시 메모 상세 조회
   */
  get: async (id: string): Promise<TempMemo> => {
    const response = await api.get<TempMemo>(`/temp-memos/${id}`);
    return response.data;
  },

  /**
   * 임시 메모 수정
   */
  update: async (id: string, data: TempMemoUpdate): Promise<TempMemo> => {
    const response = await api.patch<TempMemo>(`/temp-memos/${id}`, data);
    return response.data;
  },

  /**
   * 임시 메모 삭제
   */
  delete: async (id: string): Promise<void> => {
    await api.delete(`/temp-memos/${id}`);
  },
};
