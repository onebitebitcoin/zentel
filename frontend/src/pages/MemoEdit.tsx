import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Check, ExternalLink, Copy, RefreshCw, Plus, X, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import type { TempMemo, MemoType, TempMemoUpdate } from '../types/memo';
import { MemoTypeChips } from '../components/memo/MemoTypeChips';
import { formatDateTime } from '../utils/date';
import { useAuth } from '../contexts/AuthContext';
import { tempMemoApi } from '../api/client';

export function MemoEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [memo, setMemo] = useState<TempMemo | null>(null);
  const [loading, setLoading] = useState(true);
  const [memoType, setMemoType] = useState<MemoType>('NEW_IDEA');
  const [content, setContent] = useState('');
  const [interests, setInterests] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [rematching, setRematching] = useState(false);
  const [factsExpanded, setFactsExpanded] = useState(false);
  const [showInterestPicker, setShowInterestPicker] = useState(false);

  const userInterests: string[] = user?.interests || [];
  const availableInterests = userInterests.filter((i: string) => !interests.includes(i));

  const hasChanges = memo
    ? memoType !== memo.memo_type ||
      content !== memo.content ||
      JSON.stringify(interests) !== JSON.stringify(memo.interests || [])
    : false;

  useEffect(() => {
    if (!id) {
      navigate('/inbox');
      return;
    }

    const fetchMemo = async () => {
      try {
        const data = await tempMemoApi.get(id);
        setMemo(data);
        setMemoType(data.memo_type);
        setContent(data.content);
        setInterests(data.interests || []);
      } catch {
        toast.error('메모를 불러오는데 실패했습니다.');
        navigate('/inbox');
      } finally {
        setLoading(false);
      }
    };

    fetchMemo();
  }, [id, navigate]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('메모가 복사되었습니다.');
    } catch {
      toast.error('복사에 실패했습니다.');
    }
  };

  const handleSave = async () => {
    if (!memo || !hasChanges || saving) return;

    setSaving(true);
    try {
      const updates: TempMemoUpdate = {};
      if (memoType !== memo.memo_type) updates.memo_type = memoType;
      if (content !== memo.content) updates.content = content;
      if (JSON.stringify(interests) !== JSON.stringify(memo.interests || [])) {
        updates.interests = interests;
      }

      await tempMemoApi.update(memo.id, updates);
      toast.success('메모가 수정되었습니다.');
      navigate('/inbox');
    } catch {
      toast.error('수정에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleRematch = async () => {
    if (!memo || rematching || !userInterests.length) return;

    setRematching(true);
    try {
      const updated = await tempMemoApi.update(memo.id, { rematch_interests: true });
      setInterests(updated.interests || []);
      setMemo(updated);
      toast.success('관심사가 다시 매핑되었습니다.');
    } catch {
      toast.error('관심사 매핑에 실패했습니다.');
    } finally {
      setRematching(false);
    }
  };

  const handleDelete = async () => {
    if (!memo || !window.confirm('정말 삭제하시겠습니까?')) return;

    try {
      await tempMemoApi.delete(memo.id);
      toast.success('메모가 삭제되었습니다.');
      navigate('/inbox');
    } catch {
      toast.error('삭제에 실패했습니다.');
    }
  };

  const handleRemoveInterest = (interest: string) => {
    setInterests((prev) => prev.filter((i) => i !== interest));
  };

  const handleAddInterest = (interest: string) => {
    setInterests((prev) => [...prev, interest]);
    setShowInterestPicker(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!memo) {
    return null;
  }

  const facts = memo.facts?.slice(0, 3) ?? [];
  const maxFactLength = 200;
  const hasTruncatedFacts = facts.some((fact) => fact.length > maxFactLength);
  const visibleFacts = factsExpanded
    ? facts
    : facts.map((fact) =>
        fact.length > maxFactLength ? `${fact.slice(0, maxFactLength)}...` : fact,
      );

  return (
    <div className="flex flex-col h-full bg-white">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <button
          onClick={() => navigate('/inbox')}
          className="p-2 text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft size={20} />
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

      {/* 컨텐츠 */}
      <div className="flex-1 overflow-auto">
        <div className="p-4 space-y-4 pb-24">
          <MemoTypeChips selectedType={memoType} onSelect={setMemoType} />

          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full min-h-[200px] p-4 text-base text-gray-800 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary/30"
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

            {showInterestPicker && availableInterests.length > 0 && (
              <div className="flex flex-wrap gap-1.5 p-2 bg-gray-50 rounded-lg">
                {availableInterests.map((interest: string) => (
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

          {/* 삭제 버튼 */}
          <div className="border-t border-gray-100 pt-4">
            <button
              onClick={handleDelete}
              className="flex items-center gap-2 text-sm text-red-500 hover:text-red-600"
            >
              <Trash2 size={16} />
              메모 삭제
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
