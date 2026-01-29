/**
 * 메모 카드 - 분석 상태 표시 컴포넌트
 *
 * 분석 중, 타임아웃, 실패 상태를 표시합니다.
 */
import { useState, useEffect, useRef } from 'react';
import { Loader2, Clock, RefreshCw, AlertCircle, Terminal, ChevronDown, ChevronUp } from 'lucide-react';
import toast from 'react-hot-toast';
import type { TempMemoListItem } from '../../types/memo';
import type { AnalysisProgressEvent } from '../../hooks/useAnalysisSSE';
import { tempMemoApi } from '../../api/client';

// 분석 타임아웃 (초)
const ANALYSIS_TIMEOUT_SEC = 180;

interface MemoCardAnalysisStatusProps {
  memo: TempMemoListItem;
  analysisLogs?: AnalysisProgressEvent[];
  onReanalyze?: (id: string) => void;
}

export function MemoCardAnalysisStatus({
  memo,
  analysisLogs,
  onReanalyze,
}: MemoCardAnalysisStatusProps) {
  const [logsExpanded, setLogsExpanded] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [analysisTimedOut, setAnalysisTimedOut] = useState(false);
  const [timeoutMessage, setTimeoutMessage] = useState<string | null>(null);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isAnalyzing = memo.analysis_status === 'pending' || memo.analysis_status === 'analyzing';
  const isAnalysisFailed = memo.analysis_status === 'failed';

  // 초기 로그
  const displayLogs = (() => {
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
  })();

  // 타임아웃 시 서버 상태 확인 + 로그 분석
  const checkServerStatus = async () => {
    setCheckingStatus(true);
    try {
      const serverMemo = await tempMemoApi.get(memo.id);

      // 로그 분석
      const lastLog = displayLogs[displayLogs.length - 1];
      const logCount = displayLogs.length;
      const lastMessage = lastLog ? `${lastLog.message}${lastLog.detail ? ` (${lastLog.detail})` : ''}` : '로그 없음';

      // 서버 상태에 따라 메시지 구성
      if (serverMemo.analysis_status === 'completed') {
        setTimeoutMessage('✅ 분석 완료됨 - 새로고침 필요');
        onReanalyze?.(memo.id);
      } else if (serverMemo.analysis_status === 'failed') {
        setTimeoutMessage(`❌ ${serverMemo.analysis_error || '분석 실패'}\n마지막 진행: ${lastMessage}`);
      } else {
        // 아직 분석 중 - 마지막 진행 상황 표시
        setTimeoutMessage(`🔄 서버에서 아직 분석 중\n📊 ${logCount}단계 진행됨\n📍 마지막 단계: ${lastMessage}`);
      }
    } catch {
      const lastLog = displayLogs[displayLogs.length - 1];
      const lastMessage = lastLog ? `${lastLog.message}` : '로그 없음';
      setTimeoutMessage(`❌ 서버 연결 실패\n마지막 진행: ${lastMessage}`);
    } finally {
      setCheckingStatus(false);
    }
  };

  // 분석 타임아웃 처리
  useEffect(() => {
    if (isAnalyzing && !analysisTimedOut) {
      timeoutRef.current = setTimeout(async () => {
        setAnalysisTimedOut(true);
        await checkServerStatus();
      }, ANALYSIS_TIMEOUT_SEC * 1000);
    } else if (!isAnalyzing) {
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

  const handleReanalyze = async (force: boolean = false) => {
    if (reanalyzing) return;
    setReanalyzing(true);
    setAnalysisTimedOut(false);
    setTimeoutMessage(null);
    try {
      await tempMemoApi.reanalyze(memo.id, force);
      toast.success(force ? '강제 재분석을 시작했습니다.' : '재분석을 시작했습니다.');
      onReanalyze?.(memo.id);
    } catch (err) {
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

  // 분석 완료 상태 - 버튼은 MemoCard에서 처리하므로 아무것도 표시하지 않음
  if (memo.analysis_status === 'completed') {
    return null;
  }

  // 분석 중 (타임아웃 전)
  if (isAnalyzing && !analysisTimedOut) {
    return (
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
    );
  }

  // 분석 타임아웃
  if (isAnalyzing && analysisTimedOut) {
    return (
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
            onClick={() => handleReanalyze(true)}
            disabled={reanalyzing}
            className="flex items-center gap-1 text-primary hover:text-primary-600 ml-auto"
            title="강제 재분석 (analyzing 상태 무시)"
          >
            <RefreshCw size={12} className={reanalyzing ? 'animate-spin' : ''} />
            강제 재분석
          </button>
        </div>
        {timeoutMessage && (
          <p className="mt-1 text-[10px] text-gray-500 whitespace-pre-line">{timeoutMessage}</p>
        )}
      </div>
    );
  }

  // 분석 실패
  if (isAnalysisFailed) {
    return (
      <div className="border-t border-gray-100 pt-2">
        <div className="flex items-center gap-2 text-xs text-red-500">
          <AlertCircle size={14} />
          <span>분석 실패</span>
          <button
            type="button"
            onClick={() => handleReanalyze()}
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
    );
  }

  return null;
}
