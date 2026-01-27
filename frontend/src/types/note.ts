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
}

export interface PermanentNoteListResponse {
  items: PermanentNoteListItem[];
  total: number;
}
