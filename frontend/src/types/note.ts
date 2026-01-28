export type NoteStatus = 'editing' | 'published';

export interface PermanentNoteListItem {
  id: string;
  title: string;
  status: NoteStatus;
  interests: string[] | null;
  source_memo_count: number;
  created_at: string;
  updated_at: string | null;
  published_at: string | null;
}

export interface PermanentNote extends PermanentNoteListItem {
  content: string;
  source_memo_ids: string[];
}

export interface PermanentNoteCreate {
  source_memo_ids: string[];
  title?: string;
  content?: string;
}

export interface PermanentNoteUpdate {
  title?: string;
  content?: string;
  interests?: string[];
  status?: NoteStatus;
  add_source_memo_ids?: string[];
}

export interface PermanentNoteListResponse {
  items: PermanentNoteListItem[];
  total: number;
}

// ===== 영구 메모 발전 (LLM 분석) 관련 타입 =====

export interface MemoAnalysis {
  memo_index: number;
  core_content: string;
  key_evidence: string[];
}

export interface Synthesis {
  main_argument: string;
  supporting_points: string[];
  counter_considerations: string[];
}

export interface SuggestedStructure {
  title: string;
  thesis: string;
  body_outline: string[];
  questions_for_development: string[];
}

export interface SourceMemoInfo {
  id: string;
  content: string;
  context: string | null;
}

export interface PermanentNoteDevelopRequest {
  source_memo_ids: string[];
}

export interface PermanentNoteDevelopResponse {
  memo_analyses: MemoAnalysis[];
  synthesis: Synthesis;
  suggested_structure: SuggestedStructure;
  source_memos: SourceMemoInfo[];
}
