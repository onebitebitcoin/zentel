import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Send, Trash2, FileText, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { permanentNoteApi } from '../api/client';
import type { PermanentNote } from '../types/note';

export function NoteEdit() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [note, setNote] = useState<PermanentNote | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);

  // 편집 상태
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (!id) return;

    const fetchNote = async () => {
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

    fetchNote();
  }, [id, navigate]);

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
    if (hasChanges) {
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
    <div className="flex flex-col h-full bg-white">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <button
            onClick={handleBack}
            className="p-2 -ml-2 text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft size={20} />
          </button>
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                isPublished
                  ? 'bg-green-100 text-green-700'
                  : 'bg-amber-100 text-amber-700'
              }`}
            >
              {isPublished ? '발행됨' : '편집중'}
            </span>
            {note.source_memo_ids && (
              <span className="flex items-center gap-1 text-xs text-gray-400">
                <FileText size={12} />
                출처 {note.source_memo_ids.length}개
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDelete}
            className="p-2 text-gray-400 hover:text-red-500"
          >
            <Trash2 size={18} />
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Save size={14} />
            )}
            저장
          </button>
          {!isPublished && (
            <button
              onClick={handlePublish}
              disabled={publishing}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary-600 disabled:opacity-50"
            >
              {publishing ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Send size={14} />
              )}
              발행
            </button>
          )}
        </div>
      </div>

      {/* 편집 영역 */}
      <div className="flex-1 overflow-auto p-4 md:p-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {/* 제목 */}
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="제목을 입력하세요"
            className="w-full text-xl md:text-2xl font-bold text-gray-800 placeholder-gray-300 border-0 focus:outline-none focus:ring-0"
          />

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
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="내용을 입력하세요..."
            className="w-full min-h-[400px] text-base text-gray-700 placeholder-gray-300 border-0 focus:outline-none focus:ring-0 resize-none leading-relaxed"
          />
        </div>
      </div>
    </div>
  );
}
