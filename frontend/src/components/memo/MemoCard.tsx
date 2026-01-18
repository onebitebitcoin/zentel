import { useState } from 'react';
import { Pencil, Trash2, ExternalLink, Copy, MessageCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import type { TempMemo } from '../../types/memo';
import { getMemoTypeInfo } from '../../types/memo';
import { getRelativeTime } from '../../utils/date';

interface MemoCardProps {
  memo: TempMemo;
  onEdit: (memo: TempMemo) => void;
  onDelete: (id: string) => void;
}

export function MemoCard({ memo, onEdit, onDelete }: MemoCardProps) {
  const typeInfo = getMemoTypeInfo(memo.memo_type);
  const [factsExpanded, setFactsExpanded] = useState(false);

  // 첫 줄을 제목으로 추출
  const lines = memo.content.split('\n');
  const title = lines[0].slice(0, 80);
  const body = lines.length > 1 ? lines.slice(1).join('\n').trim() : '';
  const maxFactLength = 120;
  const facts = memo.facts?.slice(0, 3) ?? [];
  const hasTruncatedFacts = facts.some((fact) => fact.length > maxFactLength);
  const visibleFacts = factsExpanded
    ? facts
    : facts.map((fact) =>
        fact.length > maxFactLength ? `${fact.slice(0, maxFactLength)}...` : fact,
      );

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(memo.content);
      toast.success('메모가 복사되었습니다.');
    } catch {
      toast.error('복사에 실패했습니다.');
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 md:p-6 space-y-3 md:space-y-4">
      {/* 타입 태그 */}
      <div className="flex items-center gap-2">
        <span
          className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium uppercase tracking-wide ${typeInfo.bgColor} ${typeInfo.color}`}
        >
          {typeInfo.label}
        </span>
      </div>

      {/* 제목 (PC에서 더 크게) */}
      <h3 className="text-sm md:text-base font-semibold text-gray-800 line-clamp-2">
        {title}
      </h3>

      {/* 본문 */}
      {body && (
        <p className="text-sm text-gray-600 line-clamp-3 md:line-clamp-4 whitespace-pre-wrap">
          {body}
        </p>
      )}

      {/* Context */}
      {memo.context && (
        <div className="border-t border-gray-100 pt-2">
          <span className="text-[10px] text-gray-400 uppercase tracking-wide">Context</span>
          <p className="text-xs text-gray-700 line-clamp-2">{memo.context}</p>
        </div>
      )}

      {/* Facts */}
      {memo.memo_type === 'EXTERNAL_SOURCE' && facts.length > 0 && (
        <div className="border-t border-gray-100 pt-2">
          <span className="text-[10px] text-gray-400 uppercase tracking-wide">Facts</span>
          <div className="mt-1 text-xs text-gray-700 space-y-1">
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
              className="mt-1 text-xs text-primary hover:text-primary-600"
            >
              {factsExpanded ? '접기' : '더보기'}
            </button>
          )}
        </div>
      )}

      {/* 관심사 태그 */}
      {memo.interests && memo.interests.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {memo.interests.map((interest) => (
            <span
              key={`${memo.id}-interest-${interest}`}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary"
            >
              {interest}
            </span>
          ))}
        </div>
      )}

      {/* 외부 링크 */}
      {memo.source_url && (
        <a
          href={memo.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 p-2 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
        >
          <ExternalLink size={14} className="text-teal-600 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-teal-600 truncate">
              {memo.og_title || memo.source_url}
            </p>
            <p className="text-[10px] text-gray-400 truncate">
              {new URL(memo.source_url).hostname}
            </p>
          </div>
        </a>
      )}

      {/* 최신 댓글 */}
      {memo.latest_comment && (
        <div
          onClick={() => onEdit(memo)}
          className="p-2 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
        >
          <p className="text-xs text-gray-600 line-clamp-2">
            {memo.latest_comment.content}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] text-gray-400">
              {getRelativeTime(memo.latest_comment.created_at)}
            </span>
            {memo.comment_count > 1 && (
              <span className="text-[10px] text-primary">
                + {memo.comment_count - 1}개 더보기
              </span>
            )}
          </div>
        </div>
      )}

      {/* 메타 정보 */}
      <div className="flex items-center justify-between pt-1 md:pt-2">
        <div className="flex items-center gap-4">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary"
          >
            <Copy size={14} />
            <span>복사</span>
          </button>
          <button
            onClick={() => onEdit(memo)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary"
          >
            <MessageCircle size={14} />
            <span>{memo.comment_count || 0}</span>
          </button>
          <button
            onClick={() => onEdit(memo)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary"
          >
            <Pencil size={14} />
            <span>수정</span>
          </button>
          <button
            onClick={() => onDelete(memo.id)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-500"
          >
            <Trash2 size={14} />
            <span>삭제</span>
          </button>
        </div>
        <span className="hidden md:block text-xs text-primary tracking-wide">
          수정됨 {getRelativeTime(memo.created_at)}
        </span>
        <span className="md:hidden text-xs text-gray-400">
          {getRelativeTime(memo.created_at)}
        </span>
      </div>
    </div>
  );
}
