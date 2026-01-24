export type MemoType =
  | 'EXTERNAL_SOURCE'
  | 'NEW_IDEA'
  | 'NEW_GOAL'
  | 'EVOLVED_THOUGHT'
  | 'CURIOSITY'
  | 'UNRESOLVED_PROBLEM'
  | 'EMOTION';

export type AnalysisStatus = 'pending' | 'analyzing' | 'completed' | 'failed';

export interface HighlightItem {
  type: 'claim' | 'fact';
  text: string;
  start: number;
  end: number;
  reason?: string;
}

export interface MemoCommentSummary {
  id: string;
  content: string;
  created_at: string;
}

export interface TempMemo {
  id: string;
  memo_type: MemoType;
  content: string;
  context: string | null;
  interests: string[] | null;
  source_url: string | null;
  og_title: string | null;
  og_image: string | null;
  fetch_failed: boolean;
  fetch_message: string | null;
  analysis_status: AnalysisStatus;
  analysis_error: string | null;
  original_language: string | null;
  translated_content: string | null;
  is_summary: boolean;  // 요약 번역 여부
  highlights: HighlightItem[] | null;
  created_at: string;
  updated_at: string | null;
  comment_count: number;
  latest_comment: MemoCommentSummary | null;
}

export interface TempMemoCreate {
  memo_type: MemoType;
  content: string;
  source_url?: string;
}

export interface TempMemoUpdate {
  memo_type?: MemoType;
  content?: string;
  interests?: string[];
  rematch_interests?: boolean;
}

export interface TempMemoListResponse {
  items: TempMemo[];
  total: number;
  next_offset: number | null;
}

export interface MemoTypeInfo {
  type: MemoType;
  label: string;
  color: string;
  bgColor: string;
  icon: string;
}

export const MEMO_TYPES: MemoTypeInfo[] = [
  {
    type: 'EXTERNAL_SOURCE',
    label: '외부 자료',
    color: 'text-teal-700',
    bgColor: 'bg-teal-100',
    icon: 'Sprout',
  },
  {
    type: 'NEW_IDEA',
    label: '새로운 아이디어',
    color: 'text-amber-700',
    bgColor: 'bg-amber-100',
    icon: 'Lightbulb',
  },
  {
    type: 'NEW_GOAL',
    label: '새로운 목표',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    icon: 'Target',
  },
  {
    type: 'EVOLVED_THOUGHT',
    label: '발전된 생각',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    icon: 'TrendingUp',
  },
  {
    type: 'CURIOSITY',
    label: '호기심과 궁금증',
    color: 'text-purple-700',
    bgColor: 'bg-purple-100',
    icon: 'HelpCircle',
  },
  {
    type: 'UNRESOLVED_PROBLEM',
    label: '해결되지 않은 문제',
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    icon: 'AlertTriangle',
  },
  {
    type: 'EMOTION',
    label: '감정',
    color: 'text-pink-700',
    bgColor: 'bg-pink-100',
    icon: 'Heart',
  },
];

export const getMemoTypeInfo = (type: MemoType): MemoTypeInfo => {
  return MEMO_TYPES.find((t) => t.type === type) || MEMO_TYPES[0];
};
