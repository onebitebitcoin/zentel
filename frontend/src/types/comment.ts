/**
 * 댓글 관련 타입 정의
 */

export interface MemoComment {
  id: string;
  memo_id: string;
  content: string;
  created_at: string;
  updated_at: string | null;
}

export interface MemoCommentCreate {
  content: string;
}

export interface MemoCommentUpdate {
  content?: string;
}

export interface MemoCommentListResponse {
  items: MemoComment[];
  total: number;
}
