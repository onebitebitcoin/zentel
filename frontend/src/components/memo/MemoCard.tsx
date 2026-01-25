import { useState, useMemo, Fragment, useEffect, useRef } from 'react';
import { Pencil, Trash2, ExternalLink, Copy, MessageCircle, ChevronDown, ChevronUp, RefreshCw, Loader2, AlertCircle, FileText, Clock, Terminal } from 'lucide-react';
import toast from 'react-hot-toast';
import type { TempMemo, TempMemoListItem, HighlightItem } from '../../types/memo';
import { getMemoTypeInfo } from '../../types/memo';
import { getRelativeTime } from '../../utils/date';
import { CommentList } from './CommentList';
import { tempMemoApi } from '../../api/client';
import type { AnalysisProgressEvent } from '../../hooks/useAnalysisSSE';

// 분석 타임아웃 (초) - 스크래핑 + LLM 호출 고려
const ANALYSIS_TIMEOUT_SEC = 120;

interface MemoCardProps {
  memo: TempMemoListItem;
  onEdit: () => void;
  onDelete: (id: string) => void;
  onCommentChange?: () => void;
  onReanalyze?: (id: string) => void;
  analysisLogs?: AnalysisProgressEvent[];
  // Lazy loading 관련
  cachedDetail?: TempMemo;
  onFetchDetail?: (id: string) => Promise<TempMemo | undefined>;
}

export function MemoCard({ memo, onEdit, onDelete, onCommentChange, onReanalyze, analysisLogs, cachedDetail, onFetchDetail }: MemoCardProps) {
  const typeInfo = getMemoTypeInfo(memo.memo_type);
  const [contentExpanded, setContentExpanded] = useState(false);
  const [commentsExpanded, setCommentsExpanded] = useState(false);
  const [translationExpanded, setTranslationExpanded] = useState(false);
  const [logsExpanded, setLogsExpanded] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [analysisTimedOut, setAnalysisTimedOut] = useState(false);
  const [timeoutMessage, setTimeoutMessage] = useState<string | null>(null);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Lazy loading 상태
  const [detailLoading, setDetailLoading] = useState(false);
  const [loadedDetail, setLoadedDetail] = useState<TempMemo | undefined>(cachedDetail);

  const isAnalyzing = memo.analysis_status === 'pending' || memo.analysis_status === 'analyzing';
  const isAnalysisFailed = memo.analysis_status === 'failed';

  // 초기 로그 (서버 응답 전에도 표시)
  const displayLogs = useMemo(() => {
    const initialLog: AnalysisProgressEvent = {
      memo_id: memo.id,
      step: 'init',
      message: '분석 요청 시작',
      timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };
    if (!analysisLogs || analysisLogs.length === 0) {
      return isAnalyzing ? [initialLog] : [];
    }
    return analysisLogs;
  }, [analysisLogs, isAnalyzing, memo.id]);

  // 타임아웃 시 서버 상태 확인
  const checkServerStatus = async () => {
    setCheckingStatus(true);
    try {
      const serverMemo = await tempMemoApi.get(memo.id);
      if (serverMemo.analysis_status === 'completed') {
        setTimeoutMessage('분석 완료됨 - 새로고침 필요');
        onReanalyze?.(memo.id); // 상태 갱신 트리거
      } else if (serverMemo.analysis_status === 'failed') {
        setTimeoutMessage(serverMemo.analysis_error || '분석 실패');
      } else {
        setTimeoutMessage('서버에서 아직 분석 중');
      }
    } catch {
      setTimeoutMessage('서버 연결 실패');
    } finally {
      setCheckingStatus(false);
    }
  };

  // 분석 타임아웃 처리
  useEffect(() => {
    if (isAnalyzing && !analysisTimedOut) {
      // 타임아웃 설정
      timeoutRef.current = setTimeout(async () => {
        setAnalysisTimedOut(true);
        console.log(`[MemoCard] 분석 타임아웃: ${memo.id}`);
        // 서버 상태 자동 확인
        await checkServerStatus();
      }, ANALYSIS_TIMEOUT_SEC * 1000);
    } else if (!isAnalyzing) {
      // 분석 완료되면 타임아웃 해제
      setAnalysisTimedOut(false);
      setTimeoutMessage(null);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAnalyzing, memo.id]);

  // cachedDetail이 변경되면 loadedDetail도 업데이트
  useEffect(() => {
    if (cachedDetail) {
      setLoadedDetail(cachedDetail);
    }
  }, [cachedDetail]);

  // 본문 보기에 표시할 콘텐츠 (loadedDetail에서 가져옴)
  const displayContent = useMemo(() => {
    if (memo.analysis_status !== 'completed') return null;

    // display_content가 있으면 사용 (외부 자료 등 번역/하이라이트된 콘텐츠)
    if (loadedDetail?.display_content) {
      return {
        text: loadedDetail.display_content,
        highlights: loadedDetail.highlights,
        isTranslated: memo.original_language !== null && memo.original_language !== 'ko',
      };
    }

    // display_content가 없으면 사용자가 입력한 원본 content 사용 (궁금한 점 등)
    if (loadedDetail?.content || memo.content) {
      return {
        text: loadedDetail?.content || memo.content,
        highlights: null,
        isTranslated: false,
      };
    }

    return null;
  }, [memo.analysis_status, memo.original_language, memo.content, loadedDetail]);

  // 본문 보기 버튼 표시 여부 (외부 자료만)
  // 외부 자료는 스크래핑된 긴 본문이 있으므로 별도 버튼으로 표시
  // 다른 타입은 사용자 입력이므로 카드 본문에 바로 표시
  const hasDisplayContent = memo.memo_type === 'EXTERNAL_SOURCE' && memo.has_display_content;

  // 하이라이트 렌더링 함수
  const renderHighlightedText = useMemo(() => {
    return (text: string, highlights: HighlightItem[] | null) => {
      // 하이라이트가 없으면 텍스트만 반환
      if (!highlights || highlights.length === 0) {
        return <span>{text}</span>;
      }

      // 유효한 위치가 있는 하이라이트만 필터링
      const validHighlights = highlights.filter((h) => h.start >= 0 && h.end >= 0);

      // 유효한 하이라이트가 없으면 텍스트만 반환
      if (validHighlights.length === 0) {
        return <span>{text}</span>;
      }

      // 하이라이트 위치 정렬
      const sortedHighlights = [...validHighlights].sort((a, b) => a.start - b.start);
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
              <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 text-[10px] bg-gray-800 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity max-w-[200px] break-words text-center pointer-events-none z-10">
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
    setAnalysisTimedOut(false);
    setTimeoutMessage(null);
    try {
      await tempMemoApi.reanalyze(memo.id);
      toast.success('재분석을 시작했습니다.');
      onReanalyze?.(memo.id);
    } catch (err) {
      // axios 에러에서 상세 메시지 추출
      let errorMsg = '재분석 요청에 실패했습니다.';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string }, status?: number } };
        if (axiosErr.response?.data?.detail) {
          errorMsg = axiosErr.response.data.detail;
        } else if (axiosErr.response?.status === 404) {
          errorMsg = '메모를 찾을 수 없습니다.';
        } else if (axiosErr.response?.status === 400) {
          errorMsg = '이미 분석 중입니다.';
        }
      }
      toast.error(errorMsg);
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

  // 본문 보기 클릭 핸들러 (lazy loading)
  const handleToggleContent = async () => {
    if (translationExpanded) {
      // 닫기
      setTranslationExpanded(false);
      return;
    }

    // 열기 - 상세 정보가 없으면 가져오기
    if (!loadedDetail && onFetchDetail) {
      setDetailLoading(true);
      try {
        const detail = await onFetchDetail(memo.id);
        if (detail) {
          setLoadedDetail(detail);
        }
      } finally {
        setDetailLoading(false);
      }
    }
    setTranslationExpanded(true);
  };

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
      {isAnalyzing && !analysisTimedOut && (
        <div className="border-t border-gray-100 pt-2">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Loader2 size={14} className="animate-spin text-primary" />
            <span>AI 분석중...</span>
            <button
              type="button"
              onClick={() => setLogsExpanded((prev) => !prev)}
              className="flex items-center gap-1 ml-auto text-gray-400 hover:text-gray-600"
            >
              <Terminal size={12} />
              <span>로그</span>
              {logsExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
          </div>
          {/* 분석 로그 표시 */}
          {logsExpanded && displayLogs.length > 0 && (
            <div className="mt-2 p-2 bg-gray-900 rounded-lg text-[10px] font-mono text-gray-300 max-h-32 overflow-auto">
              {displayLogs.map((log, idx) => (
                <div key={idx} className="flex gap-2 py-0.5">
                  <span className="text-gray-500 flex-shrink-0">{log.timestamp}</span>
                  <span className="text-green-400 break-all">{log.message}</span>
                  {log.detail && <span className="text-gray-500 break-all">({log.detail})</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 분석 타임아웃 */}
      {isAnalyzing && analysisTimedOut && (
        <div className="border-t border-gray-100 pt-2">
          <div className="flex items-center gap-2 text-xs text-amber-600">
            <Clock size={14} />
            <span>분석 지연</span>
            <button
              type="button"
              onClick={checkServerStatus}
              disabled={checkingStatus}
              className="flex items-center gap-1 text-gray-500 hover:text-gray-700"
            >
              <RefreshCw size={12} className={checkingStatus ? 'animate-spin' : ''} />
              상태 확인
            </button>
            <button
              type="button"
              onClick={handleReanalyze}
              disabled={reanalyzing}
              className="flex items-center gap-1 text-primary hover:text-primary-600 ml-auto"
            >
              <RefreshCw size={12} className={reanalyzing ? 'animate-spin' : ''} />
              다시 시도
            </button>
          </div>
          {timeoutMessage && (
            <p className="mt-1 text-[10px] text-gray-500">{timeoutMessage}</p>
          )}
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
      {memo.analysis_status === 'completed' && (
        <div className="border-t border-gray-100 pt-2">
          <div className="flex items-center justify-between">
            {memo.context ? (
              <span className="text-[10px] text-gray-400 uppercase tracking-wide">Context</span>
            ) : (
              <span className="text-[10px] text-gray-400">분석 완료 (context 없음)</span>
            )}
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
          {memo.context && (
            <p className="text-xs text-gray-700 line-clamp-2">{memo.context}</p>
          )}
        </div>
      )}

      {/* 본문 보기 (추출된 콘텐츠 확인 + 하이라이트) - lazy loading */}
      {memo.analysis_status === 'completed' && hasDisplayContent && (
        <div className="border-t border-gray-100 pt-2">
          <button
            type="button"
            onClick={handleToggleContent}
            disabled={detailLoading}
            className="flex items-center gap-1.5 text-xs text-primary hover:text-primary-600 disabled:opacity-50"
          >
            {detailLoading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <FileText size={14} />
            )}
            <span>{detailLoading ? '불러오는 중...' : '본문 보기'}</span>
            {!detailLoading && (translationExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
          </button>
          {translationExpanded && displayContent && (
            <div className="mt-2 p-3 bg-gray-50 rounded-lg">
              {displayContent.isTranslated && (
                <p className="text-[10px] text-blue-600 mb-2">
                  번역된 내용입니다
                </p>
              )}
              {!displayContent.isTranslated && loadedDetail?.display_content && (
                <p className="text-[10px] text-gray-500 mb-2">
                  추출된 내용입니다
                </p>
              )}
              <p className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
                {renderHighlightedText(displayContent.text, displayContent.highlights)}
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
