/**
 * 댓글 관련 타입 정의
 */

export interface MemoComment {
  id: string;
  memo_id: string;
  content: string;
  created_at: string;
  updated_at: string | null;
  is_ai_response: boolean;
  parent_comment_id: string | null;
  response_status: 'pending' | 'generating' | 'completed' | 'failed' | null;
  response_error: string | null;
  ai_persona_name: string | null;
  ai_persona_color: string | null;
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
