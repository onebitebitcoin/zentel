import { useState, useMemo, Fragment } from 'react';
import { Pencil, Trash2, ExternalLink, Copy, MessageCircle, ChevronDown, ChevronUp, RefreshCw, Loader2, AlertCircle, Languages } from 'lucide-react';
import toast from 'react-hot-toast';
import type { TempMemo, HighlightItem } from '../../types/memo';
import { getMemoTypeInfo } from '../../types/memo';
import { getRelativeTime } from '../../utils/date';
import { CommentList } from './CommentList';
import { tempMemoApi } from '../../api/client';

interface MemoCardProps {
  memo: TempMemo;
  onEdit: () => void;
  onDelete: (id: string) => void;
  onCommentChange?: () => void;
  onReanalyze?: (id: string) => void;
}

export function MemoCard({ memo, onEdit, onDelete, onCommentChange, onReanalyze }: MemoCardProps) {
  const typeInfo = getMemoTypeInfo(memo.memo_type);
  const [factsExpanded, setFactsExpanded] = useState(false);
  const [contentExpanded, setContentExpanded] = useState(false);
  const [commentsExpanded, setCommentsExpanded] = useState(false);
  const [translationExpanded, setTranslationExpanded] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);

  const isAnalyzing = memo.analysis_status === 'pending' || memo.analysis_status === 'analyzing';
  const isAnalysisFailed = memo.analysis_status === 'failed';

  // 번역 가능 여부 (한국어가 아니고 번역본이 있는 경우)
  const hasTranslation = memo.original_language && memo.original_language !== 'ko' && memo.translated_content;

  // 하이라이트 렌더링 함수
  const renderHighlightedText = useMemo(() => {
    return (text: string, highlights: HighlightItem[] | null) => {
      if (!highlights || highlights.length === 0) {
        return <span>{text}</span>;
      }

      // 하이라이트 위치 정렬
      const sortedHighlights = [...highlights].sort((a, b) => a.start - b.start);
      const elements: React.ReactNode[] = [];
      let lastEnd = 0;

      sortedHighlights.forEach((highlight, idx) => {
        // 하이라이트 이전 텍스트
        if (highlight.start > lastEnd) {
          elements.push(
            <span key={`text-${idx}`}>{text.slice(lastEnd, highlight.start)}</span>
          );
        }

        // 하이라이트된 텍스트
        elements.push(
          <span
            key={`highlight-${idx}`}
            className="bg-yellow-200 cursor-help relative group"
            title={highlight.reason || ''}
          >
            {text.slice(highlight.start, highlight.end)}
            {highlight.reason && (
              <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 text-[10px] bg-gray-800 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                {highlight.reason}
              </span>
            )}
          </span>
        );

        lastEnd = highlight.end;
      });

      // 마지막 하이라이트 이후 텍스트
      if (lastEnd < text.length) {
        elements.push(
          <span key="text-last">{text.slice(lastEnd)}</span>
        );
      }

      return <Fragment>{elements}</Fragment>;
    };
  }, []);

  const handleReanalyze = async () => {
    if (reanalyzing) return;
    setReanalyzing(true);
    try {
      await tempMemoApi.reanalyze(memo.id);
      toast.success('재분석을 시작했습니다.');
      onReanalyze?.(memo.id);
    } catch {
      toast.error('재분석 요청에 실패했습니다.');
    } finally {
      setReanalyzing(false);
    }
  };

  // 메모 내용 분리 로직
  const lines = memo.content.split('\n').filter((line) => line.trim());
  const isShortMemo = lines.length === 1 && lines[0].length <= 100;

  // 짧은 한 줄 메모는 전체를 제목으로 표시
  // 긴 메모는 첫 줄을 제목, 나머지를 본문으로 분리
  const title = isShortMemo ? lines[0] : lines[0]?.slice(0, 80) || '';
  const body = isShortMemo ? '' : lines.slice(1).join('\n').trim();

  // 본문이 길면 더보기 표시 (150자 또는 3줄 이상)
  const bodyLines = body.split('\n');
  const isLongContent = body.length > 150 || bodyLines.length > 3;
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
        <div>
          <p
            className={`text-sm text-gray-600 whitespace-pre-wrap ${
              !contentExpanded ? 'line-clamp-3 md:line-clamp-4' : ''
            }`}
          >
            {body}
          </p>
          {isLongContent && (
            <button
              type="button"
              onClick={() => setContentExpanded((prev) => !prev)}
              className="mt-1 text-xs text-primary hover:text-primary-600"
            >
              {contentExpanded ? '접기' : '더보기'}
            </button>
          )}
        </div>
      )}

      {/* AI 분석 상태 */}
      {isAnalyzing && (
        <div className="border-t border-gray-100 pt-2">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Loader2 size={14} className="animate-spin text-primary" />
            <span>AI 분석중...</span>
          </div>
        </div>
      )}

      {/* 분석 실패 */}
      {isAnalysisFailed && (
        <div className="border-t border-gray-100 pt-2">
          <div className="flex items-center gap-2 text-xs text-red-500">
            <AlertCircle size={14} />
            <span>분석 실패</span>
            <button
              type="button"
              onClick={handleReanalyze}
              disabled={reanalyzing}
              className="flex items-center gap-1 text-primary hover:text-primary-600 ml-auto"
            >
              <RefreshCw size={12} className={reanalyzing ? 'animate-spin' : ''} />
              다시 분석
            </button>
          </div>
          {memo.analysis_error && (
            <p className="mt-1 text-[10px] text-red-400 line-clamp-2">{memo.analysis_error}</p>
          )}
        </div>
      )}

      {/* Context (분석 완료 시에만 표시) */}
      {memo.analysis_status === 'completed' && memo.context && (
        <div className="border-t border-gray-100 pt-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-400 uppercase tracking-wide">Context</span>
            <button
              type="button"
              onClick={handleReanalyze}
              disabled={reanalyzing}
              className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-primary"
            >
              <RefreshCw size={10} className={reanalyzing ? 'animate-spin' : ''} />
              다시 분석
            </button>
          </div>
          <p className="text-xs text-gray-700 line-clamp-2">{memo.context}</p>
        </div>
      )}

      {/* Facts (분석 완료 시에만 표시) */}
      {memo.analysis_status === 'completed' && memo.memo_type === 'EXTERNAL_SOURCE' && facts.length > 0 && (
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

      {/* 번역 섹션 (한국어가 아닌 컨텐츠에만 표시) */}
      {memo.analysis_status === 'completed' && hasTranslation && (
        <div className="border-t border-gray-100 pt-2">
          <button
            type="button"
            onClick={() => setTranslationExpanded((prev) => !prev)}
            className="flex items-center gap-1.5 text-xs text-primary hover:text-primary-600"
          >
            <Languages size={14} />
            <span>번역 보기</span>
            {translationExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          {translationExpanded && memo.translated_content && (
            <div className="mt-2 p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
                {renderHighlightedText(memo.translated_content, memo.highlights)}
              </p>
            </div>
          )}
        </div>
      )}

      {/* 하이라이트 (한국어 컨텐츠 - 번역 없이 원문에 하이라이트) */}
      {memo.analysis_status === 'completed' &&
       memo.original_language === 'ko' &&
       memo.highlights &&
       memo.highlights.length > 0 && (
        <div className="border-t border-gray-100 pt-2">
          <span className="text-[10px] text-gray-400 uppercase tracking-wide">Highlights</span>
          <div className="mt-1 text-xs text-gray-700 space-y-1">
            {memo.highlights.slice(0, 3).map((highlight, index) => (
              <p key={`${memo.id}-highlight-${index}`} className="break-words">
                <span className="bg-yellow-200 cursor-help" title={highlight.reason}>
                  {highlight.text.length > 100 ? `${highlight.text.slice(0, 100)}...` : highlight.text}
                </span>
              </p>
            ))}
          </div>
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

      {/* 댓글 섹션 (트위터 스타일) */}
      {commentsExpanded && (
        <div className="border-t border-gray-100 pt-3">
          <CommentList memoId={memo.id} onCommentChange={onCommentChange} />
        </div>
      )}

      {/* 최신 댓글 미리보기 (접혀있을 때만 표시) */}
      {!commentsExpanded && memo.latest_comment && (
        <div
          onClick={() => setCommentsExpanded(true)}
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
            onClick={() => setCommentsExpanded((prev) => !prev)}
            className={`flex items-center gap-1 text-xs ${commentsExpanded ? 'text-primary' : 'text-gray-500'} hover:text-primary`}
          >
            <MessageCircle size={14} />
            <span>{memo.comment_count || 0}</span>
            {commentsExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          <button
            onClick={onEdit}
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
