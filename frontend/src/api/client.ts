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
import type {
  PermanentNote,
  PermanentNoteCreate,
  PermanentNoteDevelopRequest,
  PermanentNoteDevelopResponse,
  PermanentNoteListResponse,
  PermanentNoteUpdate,
  NoteStatus,
  SourceMemosResponse,
} from '../types/note';
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
  list: async (
    params?: {
      type?: MemoType;
      limit?: number;
      offset?: number;
    },
    signal?: AbortSignal
  ): Promise<TempMemoListResponse> => {
    const response = await api.get<TempMemoListResponse>('/temp-memos', {
      params,
      signal,
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
  reanalyze: async (id: string, force?: boolean): Promise<TempMemo> => {
    const response = await api.post<TempMemo>(`/temp-memos/${id}/reanalyze`, null, {
      params: force ? { force: true } : undefined,
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

export const permanentNoteApi = {
  /**
   * 영구 메모 생성
   */
  create: async (data: PermanentNoteCreate): Promise<PermanentNote> => {
    const response = await api.post<PermanentNote>('/permanent-notes', data);
    return response.data;
  },

  /**
   * 영구 메모 목록 조회
   */
  list: async (params?: {
    status?: NoteStatus;
    limit?: number;
    offset?: number;
  }): Promise<PermanentNoteListResponse> => {
    const response = await api.get<PermanentNoteListResponse>('/permanent-notes', {
      params,
    });
    return response.data;
  },

  /**
   * 영구 메모 상세 조회
   */
  get: async (id: string): Promise<PermanentNote> => {
    const response = await api.get<PermanentNote>(`/permanent-notes/${id}`);
    return response.data;
  },

  /**
   * 영구 메모 수정
   */
  update: async (id: string, data: PermanentNoteUpdate): Promise<PermanentNote> => {
    const response = await api.patch<PermanentNote>(`/permanent-notes/${id}`, data);
    return response.data;
  },

  /**
   * 영구 메모 삭제
   */
  delete: async (id: string): Promise<void> => {
    await api.delete(`/permanent-notes/${id}`);
  },

  /**
   * 영구 메모 재분석
   */
  reanalyze: async (id: string): Promise<PermanentNote> => {
    const response = await api.post<PermanentNote>(`/permanent-notes/${id}/reanalyze`);
    return response.data;
  },

  /**
   * 영구 메모 발전 분석 (LLM)
   */
  develop: async (data: PermanentNoteDevelopRequest): Promise<PermanentNoteDevelopResponse> => {
    const response = await api.post<PermanentNoteDevelopResponse>(
      '/permanent-notes/develop',
      data
    );
    return response.data;
  },

  /**
   * 출처 임시 메모 목록 조회
   */
  getSourceMemos: async (noteId: string): Promise<SourceMemosResponse> => {
    const response = await api.get<SourceMemosResponse>(
      `/permanent-notes/${noteId}/source-memos`
    );
    return response.data;
  },
};
