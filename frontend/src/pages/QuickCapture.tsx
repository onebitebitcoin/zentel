import { useState, useEffect } from 'react';
import { Check } from 'lucide-react';
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
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    localStorage.setItem(LAST_TYPE_KEY, memoType);
  }, [memoType]);

  const handleSave = async () => {
    if (!content.trim() || saving) return;

    setSaving(true);
    try {
      await createMemo({ memo_type: memoType, content: content.trim() });
      toast.success('임시 메모가 저장되었습니다.');
      setContent('');
    } catch {
      toast.error('저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const canSave = content.trim().length > 0 && !saving;

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto px-4 py-4 space-y-6 pb-24">
        <MemoInput value={content} onChange={setContent} />
        <MemoTypeChips selectedType={memoType} onSelect={setMemoType} />
      </div>

      <div className="fixed bottom-16 left-0 right-0 px-4 pb-4 bg-gradient-to-t from-gray-50 to-transparent pt-8 safe-bottom">
        <button
          onClick={handleSave}
          disabled={!canSave}
          className={`w-full flex items-center justify-center gap-2 py-4 rounded-xl font-semibold text-white transition-all ${
            canSave
              ? 'bg-primary hover:bg-primary-600 active:scale-[0.98]'
              : 'bg-gray-300'
          }`}
        >
          <Check size={20} />
          <span>SAVE NOTE</span>
        </button>
      </div>
    </div>
  );
}
