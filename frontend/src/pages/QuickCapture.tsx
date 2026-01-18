import { useState, useEffect } from 'react';
import { Check, Loader2, Link as LinkIcon } from 'lucide-react';
import toast from 'react-hot-toast';
import { MemoTypeChips } from '../components/memo/MemoTypeChips';
import { MemoInput } from '../components/memo/MemoInput';
import { useTempMemos } from '../hooks/useTempMemos';
import type { MemoType } from '../types/memo';

const LAST_TYPE_KEY = 'zentel_last_memo_type';

export function QuickCapture() {
  const { createMemo } = useTempMemos();
  const [memoType, setMemoType] = useState<MemoType>(() => {
    const saved = localStorage.getItem(LAST_TYPE_KEY);
    return (saved as MemoType) || 'NEW_IDEA';
  });
  const [content, setContent] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    localStorage.setItem(LAST_TYPE_KEY, memoType);
  }, [memoType]);

  const handleSave = async () => {
    if (!content.trim() || saving) return;

    setSaving(true);
    try {
      const payload: { memo_type: MemoType; content: string; source_url?: string } = {
        memo_type: memoType,
        content: content.trim(),
      };

      if (memoType === 'EXTERNAL_SOURCE' && sourceUrl.trim()) {
        payload.source_url = sourceUrl.trim();
      }

      await createMemo(payload);
      toast.success('임시 메모가 저장되었습니다.');
      setContent('');
      setSourceUrl('');
    } catch {
      toast.error('저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const canSave = content.trim().length > 0 && !saving;
  const isExternalSource = memoType === 'EXTERNAL_SOURCE';

  return (
    <div className="flex flex-col h-full">
      {/* PC: 상단 헤더 */}
      <div className="hidden md:flex items-center px-6 py-5 bg-white border-b border-gray-100">
        <h1 className="text-xl font-semibold text-gray-800">
          새 메모 작성
        </h1>
      </div>

      <div className="flex-1 overflow-auto px-4 md:px-6 py-4 md:py-6 space-y-6 pb-24 md:pb-6">
        <div className="md:max-w-2xl md:mx-auto space-y-6">
          <MemoInput value={content} onChange={setContent} />

          {/* 외부 자료 타입일 때 URL 입력 */}
          {isExternalSource && (
            <div className="relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                <LinkIcon size={18} />
              </div>
              <input
                type="url"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="URL을 입력하세요 (선택)"
                className="w-full pl-11 pr-4 py-3 text-base bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
          )}

          <MemoTypeChips selectedType={memoType} onSelect={setMemoType} />

          {/* PC: 저장 버튼 (인라인) */}
          <div className="hidden md:block">
            <button
              onClick={handleSave}
              disabled={!canSave}
              className={`w-full flex items-center justify-center gap-2 py-4 rounded-xl font-semibold text-white transition-all ${
                canSave
                  ? 'bg-primary hover:bg-primary-600 active:scale-[0.98]'
                  : 'bg-gray-300'
              }`}
            >
              {saving ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  <span>AI 분석 중...</span>
                </>
              ) : (
                <>
                  <Check size={20} />
                  <span>저장하기</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 모바일: 저장 버튼 (고정) */}
      <div className="md:hidden fixed bottom-16 left-0 right-0 px-4 pb-4 bg-gradient-to-t from-gray-50 to-transparent pt-8 safe-bottom">
        <button
          onClick={handleSave}
          disabled={!canSave}
          className={`w-full flex items-center justify-center gap-2 py-4 rounded-xl font-semibold text-white transition-all ${
            canSave
              ? 'bg-primary hover:bg-primary-600 active:scale-[0.98]'
              : 'bg-gray-300'
          }`}
        >
          {saving ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              <span>AI 분석 중...</span>
            </>
          ) : (
            <>
              <Check size={20} />
              <span>저장하기</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
