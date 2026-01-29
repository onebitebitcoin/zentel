import { useState, useMemo } from 'react';
import { ExternalLink, FileText, ChevronDown, ChevronUp, Check } from 'lucide-react';
import type { TempMemoListItem } from '../../types/memo';
import { getMemoTypeInfo } from '../../types/memo';
import { getRelativeTime } from '../../utils/date';
import { CommentList } from './CommentList';
import { MemoCardAnalysisStatus } from './MemoCardAnalysisStatus';
import { MemoCardActions } from './MemoCardActions';
import { HighlightedText } from './HighlightedText';
import type { AnalysisProgressEvent } from '../../hooks/useAnalysisSSE';
import fertilizerImage from '../../assets/images/fertilizer.png';

interface MemoCardProps {
  memo: TempMemoListItem;
  onEdit: () => void;
  onDelete: (id: string) => void;
  onCommentChange?: () => void;
  onReanalyze?: (id: string) => void;
  analysisLogs?: AnalysisProgressEvent[];
  // 선택 모드 관련
  selectionMode?: boolean;
  isSelected?: boolean;
  onToggleSelect?: (id: string) => void;
}

export function MemoCard({
  memo,
  onEdit,
  onDelete,
  onCommentChange,
  onReanalyze,
  analysisLogs,
  selectionMode = false,
  isSelected = false,
  onToggleSelect,
}: MemoCardProps) {
  const typeInfo = getMemoTypeInfo(memo.memo_type);
  const [contentExpanded, setContentExpanded] = useState(false);
  const [commentsExpanded, setCommentsExpanded] = useState(false);
  const [translationExpanded, setTranslationExpanded] = useState(false);

  // 본문 보기에 표시할 콘텐츠 (목록에서 바로 사용 - 추가 API 호출 제거)
  const displayContent = useMemo(() => {
    if (memo.analysis_status !== 'completed') return null;

    // display_content가 있으면 사용 (외부 자료 등 번역/하이라이트된 콘텐츠)
    if (memo.display_content) {
      return {
        text: memo.display_content,
        highlights: memo.highlights,
        isTranslated: memo.original_language !== null && memo.original_language !== 'ko',
      };
    }

    // display_content가 없으면 사용자가 입력한 원본 content 사용 (궁금한 점 등)
    if (memo.content) {
      return {
        text: memo.content,
        highlights: null,
        isTranslated: false,
      };
    }

    return null;
  }, [memo.analysis_status, memo.original_language, memo.content, memo.display_content, memo.highlights]);

  // 본문 보기 버튼 표시 여부 (외부 자료만)
  const hasDisplayContent = memo.memo_type === 'EXTERNAL_SOURCE' && memo.has_display_content;

  // 메모 내용 분리 로직
  const lines = memo.content.split('\n').filter((line) => line.trim());
  const isShortMemo = lines.length === 1 && lines[0].length <= 100;

  // 짧은 한 줄 메모는 전체를 제목으로 표시
  const title = isShortMemo ? lines[0] : lines[0]?.slice(0, 80) || '';
  const body = isShortMemo ? '' : lines.slice(1).join('\n').trim();

  // 본문이 길면 더보기 표시
  const bodyLines = body.split('\n');
  const isLongContent = body.length > 150 || bodyLines.length > 3;

  // 본문 보기 클릭 핸들러 (목록에서 바로 사용 - 추가 API 호출 제거)
  const handleToggleContent = () => {
    setTranslationExpanded(!translationExpanded);
  };

  const isExternalSource = memo.memo_type === 'EXTERNAL_SOURCE';

  // 선택 모드에서 카드 클릭 시 선택 토글
  const handleCardClick = () => {
    if (selectionMode && onToggleSelect) {
      onToggleSelect(memo.id);
    }
  };

  return (
    <div
      onClick={handleCardClick}
      className={`bg-white rounded-xl border p-4 md:p-6 space-y-3 md:space-y-4 transition-colors overflow-hidden ${
        selectionMode ? 'cursor-pointer' : ''
      } ${
        isSelected
          ? 'border-primary bg-primary/5'
          : 'border-gray-100'
      }`}
    >
      {/* 타입 태그 + 선택 체크 + 외부 자료 이미지 */}
      <div className="flex items-center justify-between gap-2">
        <span
          className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium uppercase tracking-wide ${typeInfo.bgColor} ${typeInfo.color}`}
        >
          {typeInfo.label}
        </span>
        <div className="flex items-center gap-2">
          {isExternalSource && (
            <img
              src={fertilizerImage}
              alt="Fertilizer"
              className="w-10 h-10 md:w-12 md:h-12 object-contain flex-shrink-0"
            />
          )}
          {selectionMode && (
            <div
              className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                isSelected
                  ? 'bg-primary border-primary text-white'
                  : 'border-gray-300 bg-white'
              }`}
            >
              {isSelected && <Check size={14} />}
            </div>
          )}
        </div>
      </div>

      {/* 제목 (AI 분석 완료 시 context 사용, 아니면 기존 title) */}
      <h3 className="text-sm md:text-base font-semibold text-gray-800 line-clamp-2 break-all">
        {memo.analysis_status === 'completed' && memo.context ? memo.context : title}
      </h3>

      {/* 요약 (summary) */}
      {memo.analysis_status === 'completed' && memo.summary && (
        <p className="text-sm text-gray-600 whitespace-pre-wrap break-all leading-relaxed">
          {memo.summary}
        </p>
      )}

      {/* 분석 전 본문 표시 */}
      {memo.analysis_status !== 'completed' && body && (
        <div>
          <p
            className={`text-sm text-gray-600 whitespace-pre-wrap break-all ${
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
      <MemoCardAnalysisStatus
        memo={memo}
        analysisLogs={analysisLogs}
        onReanalyze={onReanalyze}
      />

      {/* 원문 링크 (외부 자료) */}
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

      {/* 본문 보기 (외부 자료) */}
      {memo.analysis_status === 'completed' && hasDisplayContent && (
        <div>
          <button
            type="button"
            onClick={handleToggleContent}
            className="flex items-center gap-1.5 text-xs text-gray-600 hover:text-primary transition-colors"
          >
            <FileText size={14} />
            <span>본문 보기</span>
            {translationExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          {translationExpanded && displayContent && (
            <div className="mt-2 p-3 bg-gray-50 rounded-lg">
              {displayContent.isTranslated && (
                <p className="text-[10px] text-blue-600 mb-2">
                  번역된 내용입니다
                </p>
              )}
              {!displayContent.isTranslated && memo.display_content && (
                <p className="text-[10px] text-gray-500 mb-2">
                  추출된 내용입니다
                </p>
              )}
              <p className="text-xs text-gray-700 whitespace-pre-wrap break-all leading-relaxed">
                <HighlightedText text={displayContent.text} highlights={displayContent.highlights} />
              </p>
            </div>
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

      {/* 댓글 섹션 */}
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
          <p className="text-xs text-gray-600 line-clamp-2 break-all">
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

      {/* 메타 정보 및 액션 버튼 */}
      <MemoCardActions
        memoId={memo.id}
        content={memo.content}
        commentCount={memo.comment_count}
        createdAt={memo.created_at}
        commentsExpanded={commentsExpanded}
        onToggleComments={() => setCommentsExpanded((prev) => !prev)}
        onEdit={onEdit}
        onDelete={onDelete}
      />
    </div>
  );
}
