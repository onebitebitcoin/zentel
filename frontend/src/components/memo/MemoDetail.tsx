import { useState } from 'react';
import { X, Check, ExternalLink, Copy, RefreshCw, Plus } from 'lucide-react';
import toast from 'react-hot-toast';
import type { TempMemo, MemoType, TempMemoUpdate } from '../../types/memo';
import { MemoTypeChips } from './MemoTypeChips';
import { formatDateTime } from '../../utils/date';
import { useAuth } from '../../contexts/AuthContext';

interface MemoDetailProps {
  memo: TempMemo;
  onClose: () => void;
  onSave: (id: string, data: TempMemoUpdate) => void;
}

export function MemoDetail({ memo, onClose, onSave }: MemoDetailProps) {
  const { user } = useAuth();
  const [memoType, setMemoType] = useState<MemoType>(memo.memo_type);
  const [content, setContent] = useState(memo.content);
  const [interests, setInterests] = useState<string[]>(memo.interests || []);
  const [saving, setSaving] = useState(false);
  const [rematching, setRematching] = useState(false);
  const [factsExpanded, setFactsExpanded] = useState(false);
  const [showInterestPicker, setShowInterestPicker] = useState(false);

  const userInterests = user?.interests || [];
  const availableInterests = userInterests.filter((i) => !interests.includes(i));

  const hasChanges =
    memoType !== memo.memo_type ||
    content !== memo.content ||
    JSON.stringify(interests) !== JSON.stringify(memo.interests || []);

  const maxFactLength = 200;
  const facts = memo.facts?.slice(0, 3) ?? [];
  const hasTruncatedFacts = facts.some((fact) => fact.length > maxFactLength);
  const visibleFacts = factsExpanded
    ? facts
    : facts.map((fact) =>
        fact.length > maxFactLength ? `${fact.slice(0, maxFactLength)}...` : fact,
      );

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('메모가 복사되었습니다.');
    } catch {
      toast.error('복사에 실패했습니다.');
    }
  };

  const handleSave = async () => {
    if (!hasChanges || saving) return;

    setSaving(true);
    try {
      const updates: TempMemoUpdate = {};
      if (memoType !== memo.memo_type) updates.memo_type = memoType;
      if (content !== memo.content) updates.content = content;
      if (JSON.stringify(interests) !== JSON.stringify(memo.interests || [])) {
        updates.interests = interests;
      }

      await onSave(memo.id, updates);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  const handleRematch = async () => {
    if (rematching || !userInterests.length) return;

    setRematching(true);
    try {
      await onSave(memo.id, { rematch_interests: true });
      toast.success('관심사가 다시 매핑되었습니다.');
      onClose();
    } catch {
      toast.error('관심사 매핑에 실패했습니다.');
    } finally {
      setRematching(false);
    }
  };

  const handleRemoveInterest = (interest: string) => {
    setInterests((prev) => prev.filter((i) => i !== interest));
  };

  const handleAddInterest = (interest: string) => {
    setInterests((prev) => [...prev, interest]);
    setShowInterestPicker(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="relative w-full max-w-lg bg-white rounded-t-2xl sm:rounded-2xl max-h-[90vh] overflow-auto">
        <div className="sticky top-0 flex items-center justify-between px-4 py-3 border-b bg-white z-10">
          <button onClick={onClose} className="p-2 text-gray-500">
            <X size={20} />
          </button>
          <span className="text-sm font-medium">메모 수정</span>
          <div className="flex items-center gap-1">
            <button onClick={handleCopy} className="p-2 text-gray-500 hover:text-primary">
              <Copy size={20} />
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges || saving}
              className={`p-2 ${hasChanges ? 'text-primary' : 'text-gray-300'}`}
            >
              <Check size={20} />
            </button>
          </div>
        </div>

        <div className="p-4 space-y-4">
          <MemoTypeChips selectedType={memoType} onSelect={setMemoType} />

          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full h-48 p-4 text-base text-gray-800 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary/30"
          />

          {/* 관심사 관리 */}
          <div className="border-t border-gray-100 pt-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                관심사
              </span>
              {userInterests.length > 0 && (
                <button
                  type="button"
                  onClick={handleRematch}
                  disabled={rematching}
                  className="flex items-center gap-1 text-xs text-primary hover:text-primary-600 disabled:opacity-50"
                >
                  <RefreshCw size={12} className={rematching ? 'animate-spin' : ''} />
                  다시 매핑
                </button>
              )}
            </div>

            {interests.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {interests.map((interest) => (
                  <span
                    key={interest}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary"
                  >
                    {interest}
                    <button
                      type="button"
                      onClick={() => handleRemoveInterest(interest)}
                      className="hover:text-red-500"
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}
                {availableInterests.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setShowInterestPicker((prev) => !prev)}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 hover:bg-gray-200"
                  >
                    <Plus size={12} />
                    추가
                  </button>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">매핑된 관심사 없음</span>
                {availableInterests.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setShowInterestPicker((prev) => !prev)}
                    className="text-xs text-primary hover:text-primary-600"
                  >
                    직접 추가
                  </button>
                )}
              </div>
            )}

            {/* 관심사 선택 드롭다운 */}
            {showInterestPicker && availableInterests.length > 0 && (
              <div className="flex flex-wrap gap-1.5 p-2 bg-gray-50 rounded-lg">
                {availableInterests.map((interest) => (
                  <button
                    key={interest}
                    type="button"
                    onClick={() => handleAddInterest(interest)}
                    className="px-2 py-1 text-xs bg-white border border-gray-200 rounded-full hover:border-primary hover:text-primary"
                  >
                    {interest}
                  </button>
                ))}
              </div>
            )}

            {userInterests.length === 0 && (
              <p className="text-xs text-gray-400">
                설정에서 관심사를 추가하면 메모와 자동 매핑됩니다.
              </p>
            )}
          </div>

          {/* Context */}
          {memo.context && (
            <div className="border-t border-gray-100 pt-3 space-y-1">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Context
              </span>
              <p className="text-sm text-gray-700">{memo.context}</p>
            </div>
          )}

          {/* Facts */}
          {memo.memo_type === 'EXTERNAL_SOURCE' && facts.length > 0 && (
            <div className="border-t border-gray-100 pt-3 space-y-2">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Facts
              </span>
              <div className="text-sm text-gray-700 space-y-1">
                {visibleFacts.map((fact, index) => (
                  <p key={`${memo.id}-fact-${index}`} className="break-words">
                    - {fact}
                  </p>
                ))}
              </div>
              {hasTruncatedFacts && (
                <button
                  type="button"
                  onClick={() => setFactsExpanded((prev) => !prev)}
                  className="text-xs text-primary hover:text-primary-600"
                >
                  {factsExpanded ? '접기' : '더보기'}
                </button>
              )}
            </div>
          )}

          {/* 외부 링크 */}
          {memo.source_url && (
            <a
              href={memo.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors"
            >
              <ExternalLink size={18} className="text-teal-600 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-teal-600 truncate">
                  {memo.og_title || memo.source_url}
                </p>
                <p className="text-xs text-gray-400 truncate mt-1">
                  {new URL(memo.source_url).hostname}
                </p>
              </div>
            </a>
          )}

          <div className="text-xs text-gray-400">
            <p>생성: {formatDateTime(memo.created_at)}</p>
            {memo.updated_at && <p>수정: {formatDateTime(memo.updated_at)}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
