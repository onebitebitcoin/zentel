import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { permanentNoteApi } from '../api/client';
import { NoteEditHeader, AnalysisPanel, SourceMemosList } from '../components/note';
import type { PermanentNote, PermanentNoteDevelopResponse, SourceMemoDetail } from '../types/note';

interface LocationState {
  analysisResult?: PermanentNoteDevelopResponse;
}

export function NoteEdit() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams<{ id: string }>();
  const [note, setNote] = useState<PermanentNote | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);

  // 편집 상태
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // 분석 결과 (DevelopmentPreview에서 전달받거나 DB에서 로드)
  const state = location.state as LocationState | null;
  const [analysisResult, setAnalysisResult] = useState<PermanentNoteDevelopResponse | undefined>(
    state?.analysisResult
  );
  const [analysisExpanded, setAnalysisExpanded] = useState(!!state?.analysisResult);
  const [reanalyzing, setReanalyzing] = useState(false);

  // 출처 메모 관련 상태
  const [sourceMemos, setSourceMemos] = useState<SourceMemoDetail[]>([]);
  const [sourceMemosExpanded, setSourceMemosExpanded] = useState(false);
  const [sourceMemosLoading, setSourceMemosLoading] = useState(false);
  const [sourceMemosLoaded, setSourceMemosLoaded] = useState(false);
  const [removingMemoId, setRemovingMemoId] = useState<string | null>(null);

  // 제목 textarea 자동 높이 조절
  const titleRef = useRef<HTMLTextAreaElement>(null);
  const adjustTitleHeight = useCallback(() => {
    const textarea = titleRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, []);

  // 본문 textarea 자동 높이 조절
  const contentRef = useRef<HTMLTextAreaElement>(null);
  const adjustContentHeight = useCallback(() => {
    const textarea = contentRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const minHeight = 150;
      textarea.style.height = `${Math.max(minHeight, textarea.scrollHeight)}px`;
    }
  }, []);

  useEffect(() => {
    adjustTitleHeight();
  }, [title, adjustTitleHeight]);

  useEffect(() => {
    adjustContentHeight();
  }, [content, adjustContentHeight, isEditing]);

  const fetchNote = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await permanentNoteApi.get(id);
      setNote(data);
      setTitle(data.title);
      setContent(data.content);
      if (data.analysis_result && !analysisResult) {
        setAnalysisResult(data.analysis_result);
        setAnalysisExpanded(true);
      }
    } catch {
      toast.error('영구 메모를 불러오는데 실패했습니다.');
      navigate('/notes');
    } finally {
      setLoading(false);
    }
  };

  const fetchSourceMemos = async () => {
    if (!id || sourceMemosLoaded) return;
    setSourceMemosLoading(true);
    try {
      const response = await permanentNoteApi.getSourceMemos(id);
      setSourceMemos(response.items);
      setSourceMemosLoaded(true);
    } catch {
      toast.error('출처 메모를 불러오는데 실패했습니다.');
    } finally {
      setSourceMemosLoading(false);
    }
  };

  const handleSourceMemosToggle = () => {
    if (!sourceMemosExpanded && !sourceMemosLoaded) {
      fetchSourceMemos();
    }
    setSourceMemosExpanded(!sourceMemosExpanded);
  };

  const handleRemoveSourceMemo = async (memoId: string) => {
    if (!id || !note) return;
    if (!window.confirm('이 출처 메모를 제거하시겠습니까?')) return;

    setRemovingMemoId(memoId);
    try {
      const updated = await permanentNoteApi.update(id, {
        remove_source_memo_ids: [memoId],
      });
      setNote(updated);
      setSourceMemos((prev) => prev.filter((m) => m.id !== memoId));
      toast.success('출처 메모가 제거되었습니다.');
    } catch {
      toast.error('출처 메모 제거에 실패했습니다.');
    } finally {
      setRemovingMemoId(null);
    }
  };

  const handleLoadSummary = (memo: SourceMemoDetail) => {
    if (!memo.summary) {
      toast.error('이 메모에는 요약이 없습니다.');
      return;
    }
    const summaryText = `\n\n### 출처: ${memo.context || memo.og_title || '제목 없음'}\n\n${memo.summary}\n`;
    setContent((prev) => prev + summaryText);
    setIsEditing(true);
    toast.success('요약이 추가되었습니다.');
  };

  const handleLoadAllSummaries = () => {
    if (sourceMemos.length === 0) {
      toast.error('출처 메모가 없습니다.');
      return;
    }
    const memosWithSummary = sourceMemos.filter((m) => m.summary);
    if (memosWithSummary.length === 0) {
      toast.error('요약이 있는 출처 메모가 없습니다.');
      return;
    }
    let allSummaries = '\n\n';
    memosWithSummary.forEach((memo, index) => {
      const title = memo.context || memo.og_title || `출처 #${index + 1}`;
      allSummaries += `### ${title}\n\n${memo.summary}\n\n`;
    });
    setContent((prev) => prev + allSummaries);
    setIsEditing(true);
    toast.success(`${memosWithSummary.length}개 메모의 요약이 추가되었습니다.`);
  };

  useEffect(() => {
    fetchNote();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!note) return;
    setHasChanges(title !== note.title || content !== note.content);
  }, [title, content, note]);

  const handleSave = async () => {
    if (!id || !hasChanges) return;
    setSaving(true);
    try {
      const updated = await permanentNoteApi.update(id, { title, content });
      setNote(updated);
      setHasChanges(false);
      setIsEditing(false);
      toast.success('저장되었습니다.');
    } catch {
      toast.error('저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = async () => {
    if (!id) return;
    if (hasChanges) {
      setSaving(true);
      try {
        await permanentNoteApi.update(id, { title, content });
        setHasChanges(false);
      } catch {
        toast.error('저장에 실패했습니다.');
        setSaving(false);
        return;
      } finally {
        setSaving(false);
      }
    }
    setPublishing(true);
    try {
      const updated = await permanentNoteApi.update(id, { status: 'published' });
      setNote(updated);
      toast.success('발행되었습니다.');
    } catch {
      toast.error('발행에 실패했습니다.');
    } finally {
      setPublishing(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    if (!window.confirm('정말 삭제하시겠습니까?')) return;
    try {
      await permanentNoteApi.delete(id);
      toast.success('삭제되었습니다.');
      navigate('/notes');
    } catch {
      toast.error('삭제에 실패했습니다.');
    }
  };

  const handleReanalyze = async () => {
    if (!id || reanalyzing) return;
    setReanalyzing(true);
    try {
      const updated = await permanentNoteApi.reanalyze(id);
      setNote(updated);
      if (updated.analysis_result) {
        setAnalysisResult(updated.analysis_result);
        setAnalysisExpanded(true);
      }
      toast.success('재분석이 완료되었습니다.');
    } catch {
      toast.error('재분석에 실패했습니다.');
    } finally {
      setReanalyzing(false);
    }
  };

  const handleBack = async () => {
    if (hasChanges || isEditing) {
      const shouldSave = window.confirm(
        '저장하지 않은 변경사항이 있습니다.\n\n저장하고 나가시겠습니까?\n\n확인: 저장 후 나가기\n취소: 저장 안하고 선택'
      );
      if (shouldSave) {
        if (!id) return;
        setSaving(true);
        try {
          await permanentNoteApi.update(id, { title, content });
          toast.success('저장되었습니다.');
          navigate('/notes');
        } catch {
          toast.error('저장에 실패했습니다.');
        } finally {
          setSaving(false);
        }
        return;
      } else {
        const confirmLeave = window.confirm(
          '저장하지 않고 나가시겠습니까?\n\n변경사항이 모두 삭제됩니다.'
        );
        if (!confirmLeave) {
          return;
        }
      }
    }
    navigate('/notes');
  };

  const handleCancelEditing = () => {
    if (note) {
      setTitle(note.title);
      setContent(note.content);
    }
    setIsEditing(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!note) {
    return null;
  }

  const isPublished = note.status === 'published';

  return (
    <div className="flex flex-col h-full bg-white overflow-hidden">
      <NoteEditHeader
        isPublished={isPublished}
        isEditing={isEditing}
        hasChanges={hasChanges}
        saving={saving}
        publishing={publishing}
        sourceMemoCount={note.source_memo_ids?.length || 0}
        onBack={handleBack}
        onSave={handleSave}
        onPublish={handlePublish}
        onDelete={handleDelete}
        onStartEditing={() => setIsEditing(true)}
        onCancelEditing={handleCancelEditing}
      />

      {/* 편집 영역 */}
      <div className="flex-1 overflow-auto">
        <div className="p-4 md:p-6 pb-24 md:pb-6">
          <div className="w-full max-w-3xl mx-auto space-y-4">
            {/* 분석 결과 패널 */}
            {analysisResult && (
              <AnalysisPanel
                analysisResult={analysisResult}
                expanded={analysisExpanded}
                reanalyzing={reanalyzing}
                hasSourceMemos={!!(note?.source_memo_ids && note.source_memo_ids.length > 0)}
                onToggle={() => setAnalysisExpanded(!analysisExpanded)}
                onReanalyze={handleReanalyze}
              />
            )}

            {/* 제목 */}
            {isPublished && !isEditing ? (
              <h1 className="text-lg md:text-2xl font-bold text-gray-800">
                {note.title}
              </h1>
            ) : (
              <textarea
                ref={titleRef}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="제목을 입력하세요"
                rows={1}
                className="w-full text-lg md:text-2xl font-bold text-gray-800 placeholder-gray-300 border-0 focus:outline-none focus:ring-0 resize-none overflow-hidden"
              />
            )}

            {/* 관심사 태그 */}
            {note.interests && note.interests.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {note.interests.map((interest) => (
                  <span
                    key={interest}
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary"
                  >
                    {interest}
                  </span>
                ))}
              </div>
            )}

            {/* 본문 */}
            {isPublished && !isEditing ? (
              <div className="text-sm md:text-base text-gray-700 leading-relaxed whitespace-pre-wrap">
                {note.content}
              </div>
            ) : (
              <textarea
                ref={contentRef}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="내용을 입력하세요..."
                className="w-full text-sm md:text-base text-gray-700 placeholder-gray-300 border-0 focus:outline-none focus:ring-0 resize-none leading-relaxed"
              />
            )}

            {/* 출처 메모 섹션 */}
            <SourceMemosList
              sourceMemoIds={note.source_memo_ids || []}
              sourceMemos={sourceMemos}
              expanded={sourceMemosExpanded}
              loading={sourceMemosLoading}
              removingMemoId={removingMemoId}
              noteId={id || ''}
              onToggle={handleSourceMemosToggle}
              onLoadSummary={handleLoadSummary}
              onLoadAllSummaries={handleLoadAllSummaries}
              onRemoveMemo={handleRemoveSourceMemo}
              onAddMemos={() => navigate(`/notes/${id}/add-memos`)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
