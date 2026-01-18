import axios from 'axios';
import type {
  TempMemo,
  TempMemoCreate,
  TempMemoListResponse,
  TempMemoUpdate,
  MemoType,
} from '../types/memo';
import type {
  MemoComment,
  MemoCommentCreate,
  MemoCommentUpdate,
  MemoCommentListResponse,
} from '../types/comment';
import { tokenStorage } from '../utils/token';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request 인터셉터: Authorization 헤더 추가 및 trailing slash 제거
api.interceptors.request.use((config) => {
  // Trailing slash 제거
  if (config.url && config.url.endsWith('/')) {
    config.url = config.url.slice(0, -1);
  }

  // Authorization 헤더 추가
  const token = tokenStorage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Response 인터셉터: 401 에러 처리
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 401 에러이고 재시도하지 않은 경우
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Refresh Token으로 토큰 갱신 시도
      const refreshToken = tokenStorage.getRefreshToken();
      if (refreshToken) {
        try {
          const response = await axios.post(
            `${API_BASE_URL}/auth/refresh`,
            { refresh_token: refreshToken },
            { withCredentials: true }
          );

          const { access_token } = response.data;
          tokenStorage.setAccessToken(access_token);

          // 원래 요청 재시도
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch {
          // 토큰 갱신 실패 - 로그아웃 처리
          tokenStorage.clearTokens();
          window.location.href = '/login';
        }
      } else {
        // Refresh Token 없음 - 로그인 페이지로 이동
        tokenStorage.clearTokens();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

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
