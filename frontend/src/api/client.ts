import type {
  TempMemo,
  TempMemoCreate,
  TempMemoListResponse,
  TempMemoUpdate,
  MemoType,
  AdminMemoDebugResponse,
} from '../types/memo';
import type {
  MemoComment,
  MemoCommentCreate,
  MemoCommentUpdate,
  MemoCommentListResponse,
} from '../types/comment';
import { api } from './axios';

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

  /**
   * 메모 재분석 요청
   */
  reanalyze: async (id: string): Promise<TempMemo> => {
    const response = await api.post<TempMemo>(`/temp-memos/${id}/reanalyze`);
    return response.data;
  },

  /**
   * Admin: 메모 디버그 정보 조회
   */
  adminDebug: async (limit = 50): Promise<AdminMemoDebugResponse> => {
    const response = await api.get<AdminMemoDebugResponse>('/temp-memos/admin/debug', {
      params: { limit },
    });
    return response.data;
  },
};

export const commentApi = {
  /**
   * 댓글 생성
   */
  create: async (memoId: string, data: MemoCommentCreate): Promise<MemoComment> => {
    const response = await api.post<MemoComment>(`/temp-memos/${memoId}/comments`, data);
    return response.data;
  },

  /**
   * 댓글 목록 조회
   */
  list: async (memoId: string): Promise<MemoCommentListResponse> => {
    const response = await api.get<MemoCommentListResponse>(`/temp-memos/${memoId}/comments`);
    return response.data;
  },

  /**
   * 댓글 수정
   */
  update: async (
    memoId: string,
    commentId: string,
    data: MemoCommentUpdate
  ): Promise<MemoComment> => {
    const response = await api.patch<MemoComment>(
      `/temp-memos/${memoId}/comments/${commentId}`,
      data
    );
    return response.data;
  },

  /**
   * 댓글 삭제
   */
  delete: async (memoId: string, commentId: string): Promise<void> => {
    await api.delete(`/temp-memos/${memoId}/comments/${commentId}`);
  },
};
