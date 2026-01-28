import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  Send,
  Trash2,
  FileText,
  Loader2,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Target,
  Pencil,
  X,
  Plus,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { permanentNoteApi } from '../api/client';
import type { PermanentNote, PermanentNoteDevelopResponse } from '../types/note';

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

  // 분석 결과 (DevelopmentPreview에서 전달받음)
  const state = location.state as LocationState | null;
  const [analysisResult] = useState<PermanentNoteDevelopResponse | undefined>(
    state?.analysisResult
  );
  const [analysisExpanded, setAnalysisExpanded] = useState(!!state?.analysisResult);

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
      // 최소 높이 150px, 콘텐츠에 맞게 확장
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
    } catch {
      toast.error('영구 메모를 불러오는데 실패했습니다.');
      navigate('/notes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNote();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // 변경 감지
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

    // 저장되지 않은 변경사항이 있으면 먼저 저장
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

  const handleBack = () => {
    if (hasChanges || isEditing) {
      if (!window.confirm('저장하지 않은 변경사항이 있습니다. 나가시겠습니까?')) {
        return;
      }
    }
    navigate('/notes');
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
      {/* 헤더 - 모바일 최적화 */}
      <div className="flex-shrink-0 flex items-center justify-between px-2 md:px-4 py-2 md:py-3 border-b border-gray-100 gap-1">
        {/* 좌측: 뒤로가기 + 상태 */}
        <div className="flex items-center gap-1 md:gap-2 min-w-0">
          <button
            onClick={handleBack}
            className="p-1.5 md:p-2 text-gray-500 hover:text-gray-700 flex-shrink-0"
          >
            <ArrowLeft size={18} className="md:w-5 md:h-5" />
          </button>
          <span
            className={`px-1.5 md:px-2 py-0.5 rounded text-[10px] md:text-xs font-medium flex-shrink-0 ${
              isPublished
                ? 'bg-green-100 text-green-700'
                : 'bg-amber-100 text-amber-700'
            }`}
          >
            {isPublished ? '발행됨' : '편집중'}
          </span>
          {note.source_memo_ids && note.source_memo_ids.length > 0 && (
            <span className="hidden sm:flex items-center gap-1 text-[10px] md:text-xs text-gray-400 flex-shrink-0">
              <FileText size={10} className="md:w-3 md:h-3" />
              {note.source_memo_ids.length}개
            </span>
          )}
        </div>

        {/* 우측: 액션 버튼 */}
        <div className="flex items-center gap-1 md:gap-2 flex-shrink-0">
          <button
            onClick={handleDelete}
            className="p-1.5 md:p-2 text-gray-400 hover:text-red-500"
          >
            <Trash2 size={16} className="md:w-[18px] md:h-[18px]" />
          </button>
          {/* 발행된 메모: 편집/취소 버튼 */}
          {isPublished && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1 px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:border-gray-300"
            >
              <Pencil size={12} className="md:w-[14px] md:h-[14px]" />
              <span className="hidden sm:inline">편집</span>
            </button>
          )}
          {isPublished && isEditing && (
            <button
              onClick={() => {
                setTitle(note.title);
                setContent(note.content);
                setIsEditing(false);
              }}
              className="flex items-center gap-1 px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm font-medium text-gray-500 border border-gray-200 rounded-lg hover:border-gray-300"
            >
              <X size={12} className="md:w-[14px] md:h-[14px]" />
              <span className="hidden sm:inline">취소</span>
            </button>
          )}
          {/* 편집중이거나 미발행 상태: 저장 버튼 */}
          {(!isPublished || isEditing) && (
            <button
              onClick={handleSave}
              disabled={!hasChanges || saving}
              className="flex items-center gap-1 px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <Loader2 size={12} className="md:w-[14px] md:h-[14px] animate-spin" />
              ) : (
                <Save size={12} className="md:w-[14px] md:h-[14px]" />
              )}
              <span className="hidden sm:inline">저장</span>
            </button>
          )}
          {!isPublished && (
            <button
              onClick={handlePublish}
              disabled={publishing}
              className="flex items-center gap-1 px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-600 disabled:opacity-50"
            >
              {publishing ? (
                <Loader2 size={12} className="md:w-[14px] md:h-[14px] animate-spin" />
              ) : (
                <Send size={12} className="md:w-[14px] md:h-[14px]" />
              )}
              <span className="hidden sm:inline">발행</span>
            </button>
          )}
        </div>
      </div>

      {/* 편집 영역 */}
      <div className="flex-1 overflow-auto">
        <div className="p-4 md:p-6 pb-24 md:pb-6">
          <div className="w-full max-w-3xl mx-auto space-y-4">
            {/* 분석 결과 패널 */}
            {analysisResult && (
              <div className="border border-gray-200 rounded-xl overflow-hidden">
                <button
                  onClick={() => setAnalysisExpanded(!analysisExpanded)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100"
                >
                  <div className="flex items-center gap-2">
                    <Lightbulb size={16} className="text-amber-500" />
                    <span className="text-sm font-medium text-gray-700">AI 분석 결과</span>
                  </div>
                  {analysisExpanded ? (
                    <ChevronUp size={16} className="text-gray-400" />
                  ) : (
                    <ChevronDown size={16} className="text-gray-400" />
                  )}
                </button>
                {analysisExpanded && (
                  <div className="p-4 space-y-4 bg-white">
                    {/* 종합 분석 */}
                    <div>
                      <div className="flex items-center gap-1.5 mb-2">
                        <Target size={14} className="text-amber-500" />
                        <span className="text-xs font-medium text-gray-500">핵심 주장</span>
                      </div>
                      <p className="text-sm text-gray-700 bg-amber-50 p-3 rounded-lg">
                        {analysisResult.synthesis.main_argument}
                      </p>
                    </div>

                    {/* 뒷받침 포인트 */}
                    {analysisResult.synthesis.supporting_points.length > 0 && (
                      <div>
                        <span className="text-xs font-medium text-gray-500">뒷받침 포인트</span>
                        <ul className="mt-1.5 space-y-1">
                          {analysisResult.synthesis.supporting_points.map((point, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                              <span className="text-green-500 mt-0.5">+</span>
                              {point}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* 고려사항 */}
                    {analysisResult.synthesis.counter_considerations.length > 0 && (
                      <div>
                        <span className="text-xs font-medium text-gray-500">고려사항</span>
                        <ul className="mt-1.5 space-y-1">
                          {analysisResult.synthesis.counter_considerations.map((point, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                              <span className="text-orange-500 mt-0.5">!</span>
                              {point}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* 추가 탐구 질문 */}
                    {analysisResult.suggested_structure.questions_for_development.length > 0 && (
                      <div className="pt-2 border-t border-gray-100">
                        <span className="text-xs font-medium text-gray-500">추가 탐구 질문</span>
                        <ul className="mt-1.5 space-y-1">
                          {analysisResult.suggested_structure.questions_for_development.map((q, i) => (
                            <li key={i} className="text-sm text-purple-600">
                              {q}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
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
            {note.source_memo_ids && note.source_memo_ids.length > 0 && (
              <div className="pt-4 border-t border-gray-100">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <FileText size={12} />
                    <span>출처 메모 {note.source_memo_ids.length}개</span>
                  </div>
                  <button
                    onClick={() => navigate(`/notes/${id}/add-memos`)}
                    className="flex items-center gap-1 px-2 py-1 text-xs text-primary hover:bg-primary/5 rounded-lg transition-colors"
                  >
                    <Plus size={12} />
                    메모 추가
                  </button>
                </div>
              </div>
            )}

            {/* 출처 메모가 없을 때 추가 버튼 */}
            {(!note.source_memo_ids || note.source_memo_ids.length === 0) && (
              <div className="pt-4 border-t border-gray-100">
                <button
                  onClick={() => navigate(`/notes/${id}/add-memos`)}
                  className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 border border-dashed border-gray-300 rounded-lg hover:border-primary hover:text-primary transition-colors w-full justify-center"
                >
                  <Plus size={14} />
                  임시 메모 추가
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
